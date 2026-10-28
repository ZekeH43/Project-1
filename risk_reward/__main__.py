"""Run historical-data scenarios with `python -m risk_reward --help`."""

import argparse
import json
import platform
from importlib.metadata import version
from pathlib import Path

from risk_reward.analysis import analyze_portfolio
from risk_reward.data import DEFAULT_DATA_DIR, load_prices, source_metadata


def main(argv=None):
    """Write summary.csv and metadata.json, with optional preview plots."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", nargs="+", default=["NVDA"])
    parser.add_argument("--weights", nargs="+", type=float, help="Default: equal weights")
    parser.add_argument("--years", nargs="+", type=int, default=[1])
    parser.add_argument("--simulations", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--investment", type=float, default=2500)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--plots", action="store_true", help="Save PNGs for the first horizon")
    args = parser.parse_args(argv)
    try:
        prices = load_prices(args.tickers, args.data_dir)
        result = analyze_portfolio(
            prices,
            years=args.years,
            weights=args.weights,
            simulations=args.simulations,
            seed=args.seed,
            initial_investment=args.investment,
        )
        metadata = {
            "model": "correlated_log_return_v1",
            "tickers": list(prices.columns),
            "weights": result.preview.weights.tolist(),
            "years": args.years,
            "trading_steps_per_year": 252,
            "simulations": args.simulations,
            "seed": args.seed,
            "initial_investment": args.investment,
            "observations": len(prices),
            "fitting_window": {
                "start": prices.index[0].date().isoformat(),
                "end": prices.index[-1].date().isoformat(),
            },
            "sources": source_metadata(prices.columns, args.data_dir),
            "assumptions": [
                "Joint normal log returns with fixed fitted mean and covariance",
                "Independent daily draws and constant weights rebalanced each step",
                "Historical close values; split/dividend adjustments are unverified",
                "No trading costs, taxes, cash flows, or parameter uncertainty",
                "Quantiles summarize simulated scenarios, not guaranteed future probabilities",
            ],
            "versions": {
                "python": platform.python_version(),
                **{name: version(name) for name in ("numpy", "pandas", "matplotlib")},
            },
        }
        args.output.mkdir(parents=True, exist_ok=True)
        result.summary.to_csv(args.output / "summary.csv", float_format="%.10g")
        (args.output / "metadata.json").write_text(
            json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        if args.plots:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            for name, plot in (
                ("paths", result.preview.plot_simulation),
                ("distribution", result.preview.plot_distribution),
            ):
                axis = plot()
                axis.figure.tight_layout()
                axis.figure.savefig(args.output / f"{name}.png", dpi=120)
                plt.close(axis.figure)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(
        f"Historical observations: {metadata['fitting_window']['start']} to "
        f"{metadata['fitting_window']['end']} ({len(prices):,} aligned rows)"
    )
    print(result.summary.round(4).to_string())
    print("\nScenario quantiles describe this model; they are not guaranteed investment outcomes.")
    print(f"Saved results to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
