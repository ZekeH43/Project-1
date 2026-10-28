"""Seeded log-return simulations using the original MCSimulation interface.

This educational model fits historical daily log returns. It preserves fitted
cross-asset covariance and assumes constant weights rebalanced every simulated
day. Its scenario quantiles are not guaranteed future-return probabilities.
"""

import numpy as np
import pandas as pd

from risk_reward.data import validate_prices

MAX_PATH_VALUES = 5_000_000


def _integer(value, name, minimum=1):
    """Reject fractional, boolean, and nonpositive simulation settings."""
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise ValueError(f"{name} must be an integer of at least {minimum}.")
    return int(value)


class MCSimulation:
    """Simulate growth factors from a price DataFrame, with no network access.

    `portfolio_data` may have ticker columns or the original two-level
    (ticker, field) columns containing a `close` field. `weights` follow the
    price column order; None or the legacy empty string means equal weights.
    All weights must be nonnegative, finite, and sum to one. This is a
    log-return model, so results differ from the original independent normal
    simple-return implementation. See docs/MODEL.md for the equations.
    """

    def __init__(
        self,
        portfolio_data,
        weights=None,
        num_simulation=500,
        num_trading_days=252,
        seed=42,
    ):
        if not isinstance(portfolio_data, pd.DataFrame):
            raise TypeError("portfolio_data must be a pandas DataFrame.")
        if isinstance(portfolio_data.columns, pd.MultiIndex):
            if (
                portfolio_data.columns.nlevels != 2
                or "close" not in portfolio_data.columns.levels[1]
            ):
                raise ValueError("Legacy portfolio data needs (ticker, field) columns with close.")
            prices = portfolio_data.xs("close", level=1, axis=1)
        else:
            prices = portfolio_data
        self.portfolio_data = validate_prices(prices)
        self.nSim = _integer(num_simulation, "Number of simulations", minimum=2)
        self.nTrading = _integer(num_trading_days, "Number of trading days")
        self.seed = _integer(seed, "Seed", minimum=0)
        if self.seed >= 2**32:
            raise ValueError("Seed must be less than 4294967296.")
        if (self.nTrading + 1) * self.nSim > MAX_PATH_VALUES:
            raise ValueError("Requested paths are too large; reduce simulations or trading days.")
        if weights is None or (isinstance(weights, str) and weights == ""):
            weights = np.full(self.portfolio_data.shape[1], 1 / self.portfolio_data.shape[1])
        try:
            weights = np.asarray(weights, dtype=float)
        except (ValueError, TypeError) as exc:
            raise ValueError("Weights must be numeric.") from exc
        if weights.shape != (self.portfolio_data.shape[1],):
            raise ValueError("Provide one weight per asset, in ticker column order.")
        if not np.isfinite(weights).all() or (weights < 0).any():
            raise ValueError("Weights must be finite and nonnegative.")
        if not np.isclose(weights.sum(), 1, atol=1e-9, rtol=0):
            raise ValueError("Weights must sum to one.")
        self.weights = weights.copy()
        # Subtract logarithms instead of dividing extreme price values first.
        self.log_returns = np.log(self.portfolio_data).diff().iloc[1:]
        self.simulated_return = None
        self.scenario_quantiles = None

    @property
    def confidence_interval(self):
        """Legacy attribute name: a copy of scenario quantiles, not a statistical CI."""
        self._ensure_simulated()
        return self.scenario_quantiles.copy()

    def calc_cumulative_return(self):
        """Return (days + 1) by simulations growth factors, starting exactly at 1.

        Factor the covariance once, then draw all assets and simulations for
        one day at a time. This supports singular covariance (e.g. identical
        assets) and avoids allocating a days x simulations x assets tensor.
        Reinitializing a local generator makes repeated calls reproducible
        without changing NumPy's global random state.
        """
        means = self.log_returns.mean().to_numpy()
        covariance = self.log_returns.cov().to_numpy()
        eigenvalues, eigenvectors = np.linalg.eigh(covariance)
        # Sample covariance is positive semidefinite; clip roundoff below zero.
        factor = eigenvectors @ np.diag(np.sqrt(np.maximum(eigenvalues, 0)))
        rng = np.random.default_rng(self.seed)
        paths = np.ones((self.nTrading + 1, self.nSim))
        try:
            with np.errstate(over="raise", under="raise", invalid="raise", divide="raise"):
                for day in range(1, self.nTrading + 1):
                    shocks = rng.standard_normal((self.nSim, len(self.weights)))
                    log_changes = shocks @ factor.T + means
                    # Constant-weight portfolio: rebalance at each simulated step.
                    growth = np.exp(log_changes) @ self.weights
                    paths[day] = paths[day - 1] * growth
        except FloatingPointError as exc:
            raise ValueError(
                "The scenario exceeds numeric limits; check prices or shorten the horizon."
            ) from exc
        self.simulated_return = pd.DataFrame(
            paths,
            index=pd.RangeIndex(self.nTrading + 1, name="trading_day"),
            columns=pd.RangeIndex(self.nSim, name="simulation"),
        )
        self.scenario_quantiles = self.simulated_return.iloc[-1].quantile([0.025, 0.975])
        return self.simulated_return

    def _ensure_simulated(self):
        """Calculate paths once when a plot or summary is requested first."""
        if self.simulated_return is None:
            self.calc_cumulative_return()

    def summarize_cumulative_return(self):
        """Describe terminal growth factors without mutating cached quantile labels."""
        self._ensure_simulated()
        quantiles = self.scenario_quantiles.rename(
            index={0.025: "2.5% scenario quantile", 0.975: "97.5% scenario quantile"}
        )
        return pd.concat([self.simulated_return.iloc[-1].describe(), quantiles])

    def plot_simulation(self, max_paths=100):
        """Plot a readable subset of paths; all paths still contribute to summaries."""
        self._ensure_simulated()
        count = min(_integer(max_paths, "Maximum plotted paths"), self.nSim)
        axis = self.simulated_return.iloc[:, :count].plot(
            legend=False,
            color="#2563A0",
            alpha=0.12,
            figsize=(9, 5),
            title=f"Model scenarios: {count} of {self.nSim} paths",
        )
        axis.set_xlabel("Simulated trading days")
        axis.set_ylabel("Growth of 1 unit of starting value")
        return axis

    def plot_distribution(self):
        """Plot terminal factors and the model's central 95% scenario range."""
        self._ensure_simulated()
        axis = (
            self.simulated_return.iloc[-1]
            .rename("Simulated endings")
            .plot.hist(
                bins=30,
                color="#2563A0",
                alpha=0.75,
                figsize=(9, 5),
                title="Terminal values across simulated scenarios",
            )
        )
        for quantile, value in self.scenario_quantiles.items():
            axis.axvline(value, color="#B33A3A", linestyle="--", label=f"{quantile:.1%} quantile")
        axis.set_xlabel("Terminal growth factor")
        axis.set_ylabel("Simulation count")
        axis.legend()
        return axis
