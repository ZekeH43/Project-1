"""Compare time horizons and convert simulated growth factors into values."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from MCForecastTools import MCSimulation


@dataclass
class AnalysisResult:
    """Summary for every horizon plus the first simulation for demonstration plots."""

    summary: pd.DataFrame
    preview: MCSimulation


def analyze_portfolio(
    prices: pd.DataFrame,
    *,
    years=(1,),
    weights=None,
    simulations=500,
    seed=42,
    initial_investment=2500,
) -> AnalysisResult:
    """Run separate horizons with 252 simulated trading steps per year.

    Each horizon uses the same fitted model and seed. Longer horizons share
    the beginning of shorter paths; they are not independent experiments.
    Mean and median are calculated from all terminal outcomes, not from
    the midpoint of two quantiles.
    """
    years = list(years)
    if not years or any(isinstance(y, bool) or not isinstance(y, int) or y < 1 for y in years):
        raise ValueError("Years must contain one or more positive integers.")
    if len(years) != len(set(years)):
        raise ValueError("Year horizons must be unique.")
    if (
        isinstance(initial_investment, bool)
        or not np.isfinite(initial_investment)
        or initial_investment <= 0
    ):
        raise ValueError("Initial investment must be finite and greater than zero.")
    records = []
    preview = None
    for horizon in years:
        simulation = MCSimulation(
            prices,
            weights=weights,
            num_simulation=simulations,
            num_trading_days=252 * horizon,
            seed=seed,
        )
        terminal = simulation.calc_cumulative_return().iloc[-1]
        if preview is None:
            preview = simulation
        lower, upper = terminal.quantile([0.025, 0.975])
        mean, median = terminal.mean(), terminal.median()
        records.append(
            {
                "years": horizon,
                "mean_growth_factor": float(mean),
                "median_growth_factor": float(median),
                "p025_growth_factor": float(lower),
                "p975_growth_factor": float(upper),
                "simulated_loss_fraction": float((terminal < 1).mean()),
                "mean_terminal_value": float(mean * initial_investment),
                "median_terminal_value": float(median * initial_investment),
                "p025_terminal_value": float(lower * initial_investment),
                "p975_terminal_value": float(upper * initial_investment),
            }
        )
    summary = pd.DataFrame(records).set_index("years")
    if not np.isfinite(summary.to_numpy()).all():
        raise ValueError("Result values exceed numeric limits; reduce the investment or horizon.")
    return AnalysisResult(summary, preview)
