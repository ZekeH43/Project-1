# How the scenario model works

The implementation is in [MCForecastTools.py](../MCForecastTools.py). It estimates a distribution from historical observations, then samples possible paths under that distribution. It does not demonstrate out-of-sample forecasting performance.

## 1. Prepare prices and log returns

Let `P[t, i]` be a positive closing price for asset `i` on aligned observation `t`. The daily log return is:

```text
r[t, i] = log(P[t, i]) - log(P[t - 1, i])
```

`mu` is the column-wise mean of these log returns. `Sigma` is their sample covariance matrix, using pandas' default sample normalization. Both remain fixed throughout a run. Prices are sorted oldest-first and aligned without filling missing observations; see [DATA.md](DATA.md).

## 2. Sample joint returns

The covariance is factored once with an eigendecomposition:

```text
Sigma = Q diag(lambda) Q.T
L = Q diag(sqrt(max(lambda, 0)))
z = independent standard normal draws for each simulation and asset
sampled_log_return = mu + z @ L.T
```

Clipping small negative eigenvalues caused by floating-point roundoff allows positive-semidefinite, singular covariance matrices, including identical assets. Joint draws retain the fitted cross-asset relationship. Draws on different simulated days are independent.

A local `numpy.random.default_rng(seed)` isolates sampling from NumPy's global random state. Recalculating with the same seed, input, settings, and numerical environment repeats the run. Changing the seed changes Monte Carlo sampling; changing the number of paths also changes how random draws are allocated. Linear algebra backends, NumPy versions, and eigenvector choices can affect exact samples across environments, so cross-platform byte-for-byte results are not promised.

## 3. Compound portfolio growth

Each asset's positive growth factor is the exponential of its sampled log return. Portfolio weights are finite, nonnegative, and sum to one:

```text
asset_growth[i] = exp(sampled_log_return[i])
portfolio_growth = sum(weight[i] * asset_growth[i])
path[0] = 1
path[day] = path[day - 1] * portfolio_growth
```

This assumes **daily rebalancing to constant weights**. It is not a buy-and-hold portfolio whose weights drift. There is no extra `-0.5 * variance` drift correction: `mu` is already the estimated mean of log returns, rather than an arithmetic-return drift parameter.

The model uses 252 simulated trading steps per year. It vectorizes across paths and assets while looping over days, avoiding a full days-by-paths-by-assets allocation. It limits the stored path matrix to five million values and rejects invalid settings before simulation. Numerical overflow or underflow raises an error rather than returning misleading infinite or zero paths.

## 4. Summarize each horizon

[analysis.py](../risk_reward/analysis.py) creates a simulation for each requested horizon. It computes all statistics from that horizon's terminal outcomes, avoiding reuse of a previous horizon's results.

| Output | Meaning |
| --- | --- |
| `mean_growth_factor` | Arithmetic mean of all terminal growth factors |
| `median_growth_factor` | 50th percentile of terminal factors |
| `p025_growth_factor`, `p975_growth_factor` | 2.5th and 97.5th percentiles of terminal factors |
| `simulated_loss_fraction` | Fraction of terminal factors below 1 |
| Corresponding `*_terminal_value` columns | Growth statistic multiplied by the initial value |

The quantiles span the model's central 95% scenario range. They are **not** a confidence interval for an unknown population mean or proof of a 95% real-world chance of falling inside that range. The loss fraction is likewise a sample statistic under the fitted model, not a calibrated investment probability. The mean can be pulled upward by a small number of large outcomes; neither the mean nor the midpoint of quantiles is automatically the most likely result.

The same seed is used for each horizon. With the same path count and input, a longer path shares its prefix with a shorter path. The horizon runs therefore are not independent experiments. Plots show the first requested horizon; only the path chart is limited to 100 paths, while the summary and histogram use all paths.

## Changes and compatibility

The original implementation independently sampled normal **simple returns** per asset. This version samples correlated normal **log returns**, then exponentiates. The change prevents negative asset growth factors and retains cross-asset covariance, but it also changes the modeled distribution. Old results cannot be compared as if only formatting changed.

The `MCSimulation` class name and its main calculation, summary, and plotting methods remain. Inputs may use ticker columns or legacy two-level `(ticker, field)` columns containing `close`. Any old `daily_return` columns are ignored and returns are recomputed. Omitting weights, or passing the legacy empty string, means equal weights. The legacy `confidence_interval` property returns a copy of scenario quantiles; its historical name is not a statistical interpretation.

Input validation is intentionally stricter. Other undocumented behavior of the original helper is not guaranteed compatible. See the regression tests for the supported interface.

## Limitations and useful extensions

- Normal log returns do not capture all tail events, changing volatility, or market regimes.
- Fixed historical parameters omit estimation uncertainty; longer horizons compound this assumption.
- Data adjustments, missing sessions, and security identity are not independently verified.
- Rebalancing has no trading costs or taxes. Deposits, withdrawals, and separate dividend cash flows are absent.
- This is a simulation exercise without a held-out forecast evaluation or portfolio optimizer.

Useful next experiments include a documented adjusted-price dataset, an out-of-sample evaluation, joint-row bootstrap sampling, and a buy-and-hold comparison. Each should state what changes and add a meaningful test before making accuracy claims.

## Library references

- [NumPy random Generator](https://numpy.org/doc/stable/reference/random/generator.html): local generators and reproducibility considerations.
- [NumPy multivariate normal](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.multivariate_normal.html): joint normal sampling and covariance requirements. This project performs the factorization explicitly so it can reuse it across simulated days.
