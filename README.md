# Risk and Reward

[![Python checks](https://github.com/ZekeH43/Project-1/actions/workflows/python-checks.yml/badge.svg)](https://github.com/ZekeH43/Project-1/actions/workflows/python-checks.yml)

An educational Python project that turns historical price CSVs into reproducible Monte Carlo portfolio scenarios. It demonstrates data cleaning, NumPy simulation, pandas analysis, visualization, input validation, and automated testing.

**Start here:** run the CLI below, explore [Risk_Simulator.ipynb](Risk_Simulator.ipynb), then follow the [code walkthrough](docs/WALKTHROUGH.md).

The included snapshot ends on **November 1, 2023**. These are scenarios under a simplified model, not current market forecasts or investment recommendations. Source price adjustments are unverified; see the [data notes](docs/DATA.md).

## What the project does

- Parses currency-formatted closing prices, sorts dates, and aligns assets on shared observations.
- Fits historical log-return means and covariance, then generates seeded, correlated scenarios.
- Compares time horizons using actual simulated means, medians, quantiles, and loss fractions.
- Exports a summary, run settings, source hashes, and optional charts.
- Shares one implementation between the command line and documented notebooks.

No account, API key, or network connection is needed after installing dependencies. The original project explored short- and long-term portfolios as an educational assignment. This version focuses on reproducibility and explaining the assumptions; it does not optimize or recommend a portfolio.

## Quick start

Use **Python 3.11 or 3.12** and Git. Clone the repository and enter it:

```bash
git clone https://github.com/ZekeH43/Project-1.git
cd Project-1
```

**Windows PowerShell:**

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m risk_reward --plots
```

For subsequent commands, use `.venv\Scripts\python` wherever the instructions say `python`. This avoids needing to change PowerShell's activation policy.

**WSL, Linux, or macOS:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m risk_reward --plots
```

If using Python 3.11, substitute `py -3.11` or `python3.11` when creating the environment. Run the remaining commands from the repository root.

The default run uses NVDA, 500 paths, 252 trading steps, seed 42, and a starting value of 2,500. It prints the historical date range and writes these files to the ignored `artifacts/` directory:

| File | Contents |
| --- | --- |
| `summary.csv` | One row per requested horizon, with growth factors and terminal values |
| `metadata.json` | Model, settings, dependency versions, fitting window, and input SHA-256 hashes |
| `paths.png` | First 100 paths for the first requested horizon; requires `--plots` |
| `distribution.png` | All terminal outcomes for that horizon; requires `--plots` |

## Try a portfolio

```bash
python -m risk_reward --tickers NVDA PFE --weights 0.5 0.5 --years 1 3 5 --investment 15000 --plots
python -m risk_reward --help
```

Weights follow ticker order, must be nonnegative, and must sum to one. Omitting weights gives equal weights. Each simulated day assumes rebalancing to these weights. This example demonstrates a two-asset calculation, not a suggested allocation.

Use `--simulations`, `--seed`, `--output`, or `--data-dir` to change the defaults. A custom data directory must contain files named `<TICKER>_data.csv` with the schema in [DATA.md](docs/DATA.md). A run overwrites matching output filenames in the chosen directory, so use separate output directories to keep comparisons.

An example summary and its provenance are committed in [reports/example](reports/example/README.md). The main notebook uses the same settings. A growth factor of `1.12` means a simulated 12% gain; a factor of `0.80` means a simulated 20% loss. Quantiles describe the generated distribution, **not a guaranteed real-world probability**.

## Explore the notebooks

```bash
python -m pip install -r requirements-notebook.txt
python -m jupyter lab Risk_Simulator.ipynb
```

Select **Restart Kernel and Run All Cells**. Source notebooks intentionally contain no saved outputs; running them creates the figures and tables.

| Notebook | Purpose |
| --- | --- |
| [Risk_Simulator.ipynb](Risk_Simulator.ipynb) | Main walkthrough: data inspection, two-asset scenarios, plots, and interpretation |
| [Simulation_Concepts.ipynb](Simulation_Concepts.ipynb) | Small synthetic examples of seeds, growth factors, and summary statistics |
| Single-ticker notebooks, such as [AOSL_1.ipynb](AOSL_1.ipynb) | Compare 1-, 3-, 5-, 8-, 10-, and 15-year scenarios using the shared implementation |
| [NTES_1.ipynb](NTES_1.ipynb) | Explains the missing NTES CSV and skips calculation until that exact dataset is supplied |

`NETTF_data.csv` is a different symbol and is never substituted for NTES. NETTF is available through the CLI. Long horizons are retained as a modeling exercise; compounding uncertain historical assumptions can produce extreme values.

## Code map

| Path | Responsibility |
| --- | --- |
| [risk_reward/data.py](risk_reward/data.py) | Read, validate, align, and fingerprint source data |
| [MCForecastTools.py](MCForecastTools.py) | `MCSimulation`: sample paths, summarize outcomes, and plot |
| [risk_reward/analysis.py](risk_reward/analysis.py) | Run each horizon and convert growth factors into values |
| [risk_reward/__main__.py](risk_reward/__main__.py) | Parse CLI arguments and save results |
| [tests](tests) | Regression tests for data, math, reproducibility, CLI outputs, and ticker mappings |
| [scripts/check_notebooks.py](scripts/check_notebooks.py) | Execute every notebook with a fresh Jupyter kernel |

Read [WALKTHROUGH.md](docs/WALKTHROUGH.md) to follow one request through the code and practice explaining it. [MODEL.md](docs/MODEL.md) gives the equations and tradeoffs.

## Development checks

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python scripts/check_notebooks.py
```

GitHub Actions runs these checks on Python 3.11 and 3.12. Notebook execution saves copies under `artifacts/notebooks/` and leaves the source files unchanged. The NTES notebook checks its intentional missing-data path; it does not produce NTES results without an NTES CSV.

## Changes from the original experiment

The original notebooks duplicated API setup and simulation code. This refactor corrects copied ticker references, per-horizon result reuse, weight validation, and mutable summary labels. It removes live-data dependencies, generated checkpoints, bytecode, and duplicate historical summary files.

The model also changes from independent normal **simple returns** to correlated normal **log returns**. This preserves fitted cross-asset covariance and positive asset growth factors. Old and new results are different experiments, not a performance comparison.

The original `Data_1.csv`, `Book1.xlsx`, and `Risk & Reward.pptx` remain historical artifacts; their claims and numbers are not outputs of this implementation. The raw source CSVs are preserved unchanged. The tracked credentials file has been removed and `.env` files are ignored. Any credentials previously committed must be revoked and replaced if still active; deleting a file does not remove earlier Git history.

## Limits

This model assumes fixed fitted parameters, normal log returns, independent daily draws, 252 trading steps per year, and daily rebalancing. It omits trading costs, taxes, separate dividend cash flows, and parameter uncertainty. Missing sessions and unverified split/dividend adjustments can distort the fit. A seed makes sampling reproducible; it does not establish forecast accuracy. See [MODEL.md](docs/MODEL.md) and [DATA.md](docs/DATA.md) before interpreting results.
