# Read, run, and explain the project

This guide follows one example through the code. Run it yourself, change a setting, and explain the result in your own words before using the project in an interview.

## Follow a request through the files

From the repository root, using the environment described in the [README](../README.md):

```bash
python -m risk_reward --tickers NVDA PFE --weights 0.5 0.5 --years 1 3 5 --investment 15000 --plots
```

1. **`risk_reward/__main__.py`: collect settings.** `argparse` handles the ticker list, weights, horizons, and output options. Parse errors and invalid inputs produce readable errors with a nonzero exit status.
2. **`risk_reward/data.py`: make a reliable price matrix.** `load_prices` reads exactly the requested files. It removes currency formatting, sorts dates, rejects unusable values, and keeps only shared dates. Column order preserves the relationship between tickers and weights.
3. **`MCForecastTools.py`: fit and sample.** `MCSimulation` validates settings and copies input data. It calculates historical log returns, fits their mean and covariance, and generates seeded paths. Each path starts at 1 and compounds weighted asset growth factors.
4. **`risk_reward/analysis.py`: compare horizons.** `analyze_portfolio` computes each horizon's terminal statistics separately and converts growth factors to values. It keeps the first simulation for preview charts.
5. **Return to `__main__.py`: make the run inspectable.** The CLI writes the summary, metadata with source hashes, and optional PNGs. Notebooks call the same analysis functions rather than maintaining another copy of the algorithm.

## Understand the important decisions

| Decision | Why it matters |
| --- | --- |
| Sort prices oldest-first | Returns must follow time forward; the saved CSV order is reversed |
| Join on common dates without filling | Avoid inventing observations, while exposing that histories may shrink |
| Validate weights on both sides of 1 | Reject both underallocated and overallocated portfolios, plus negative or invalid weights |
| Fit a covariance matrix | Independent asset draws would discard the relationship observed in the input |
| Use a local random generator | Repeated runs can be compared without resetting unrelated random code |
| Rebalance at every step | The weighted-growth calculation has a specific portfolio interpretation |
| Keep summary methods free of cache mutation | Calling a summary twice should not rename or change its stored quantiles |
| Separate means, medians, and quantiles | These answer different questions and are not interchangeable |

The [model notes](MODEL.md) explain the equations. The [data notes](DATA.md) explain what remains unverified.

## Check behavior with small examples

Open [Simulation_Concepts.ipynb](../Simulation_Concepts.ipynb). Flat prices should produce a growth factor of 1 everywhere because both fitted drift and variance are zero. Repeating a seeded run should return the same paths in the same environment. A small hand-written series demonstrates why a mean differs from the midpoint of quantiles.

The automated tests also check known constant growth, perfectly correlated assets, an opposite-return rebalancing example, independent horizon summaries, invalid data, CLI output provenance, and notebook ticker mappings. These tests protect observable behavior; they do not prove the financial model is accurate.

Run a focused example:

```bash
python -m pytest tests/test_simulation.py -q
python -m risk_reward --tickers NTES
```

The second command should fail with an explanation that NTES data is missing. That is the intended behavior. Silently reading a differently named file would produce an apparently successful but mislabeled result.

## Practice explaining your work

Try answering these without reading the implementation:

- What input enters the program, and which checks happen before simulation?
- Why use log returns, and what changed from the original simple-return model?
- How does covariance affect a multi-asset scenario?
- What does the random seed control, and what does it not establish?
- Why is a 95% scenario range different from a verified 95% future probability?
- How do you know each horizon summarizes its own outcomes?
- Which assumptions would you investigate before applying the model to real decisions?

Describe the project's educational origin and the parts you have personally studied, changed, and tested. Use the code and tests as evidence of understanding; avoid claiming a production trading system or investment performance that this project does not demonstrate.

## Small extensions to implement yourself

1. Add a median-path line to the plot. Decide whether you mean the median at each day or the path whose final value is nearest the terminal median; explain why those differ.
2. Add a configurable historical date filter. Validate empty windows and include the selected dates in metadata.
3. Compare daily rebalancing with buy-and-hold using synthetic prices where you can calculate the result by hand.

Keep each extension separate, update the README with its actual behavior, and add a test for the mathematical or data-handling decision it introduces.
