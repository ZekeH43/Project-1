"""Protect weight validation, correlation, reproducibility, and summary semantics."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from MCForecastTools import MCSimulation
from risk_reward.analysis import analyze_portfolio


@pytest.mark.parametrize(
    "weights",
    [
        [0.4, 0.4],
        [0.6, 0.6],
        [-0.5, 1.5],
        [np.nan, 1],
        [np.inf, 0],
        [1],
        [[0.5, 0.5]],
        ["bad", "data"],
    ],
)
def test_invalid_weights_are_rejected(prices, weights):
    with pytest.raises(ValueError):
        MCSimulation(prices, weights=weights)


def test_numpy_weights_and_default_weights_are_supported(prices):
    for weights in (None, "", np.array([0.5, 0.5])):
        simulation = MCSimulation(prices, weights=weights)
        np.testing.assert_array_equal(simulation.weights, [0.5, 0.5])


@pytest.mark.parametrize(
    "arguments",
    [
        {"num_simulation": 0},
        {"num_simulation": 1},
        {"num_simulation": 2.5},
        {"num_simulation": True},
        {"num_trading_days": 0},
        {"num_trading_days": -5},
        {"seed": -1},
        {"seed": 2**32},
        {"seed": True},
        {"num_simulation": 10000, "num_trading_days": 10000},
    ],
)
def test_invalid_settings_are_rejected(prices, arguments):
    with pytest.raises(ValueError):
        MCSimulation(prices, **arguments)


def test_flat_history_stays_at_one(prices):
    flat = prices * 0 + 100
    model = MCSimulation(flat, num_simulation=20, num_trading_days=10)
    paths = model.calc_cumulative_return()
    assert paths.shape == (11, 20)
    assert (paths == 1).all().all()
    assert model.summarize_cumulative_return()["mean"] == 1


def test_constant_growth_has_known_terminal_value():
    frame = pd.DataFrame(
        {"AAA": 100 * 1.01 ** np.arange(10)}, index=pd.date_range("2020-01-01", periods=10)
    )
    paths = MCSimulation(frame, num_simulation=10, num_trading_days=5).calc_cumulative_return()
    np.testing.assert_allclose(paths.iloc[-1], 1.01**5, atol=1e-12)


def test_seeded_paths_repeat_without_changing_global_randomness(prices):
    model = MCSimulation(prices, num_simulation=20, num_trading_days=10, seed=5)
    np.random.seed(11)
    expected = np.random.random(3)
    np.random.seed(11)
    first = model.calc_cumulative_return().copy()
    pd.testing.assert_frame_equal(first, model.calc_cumulative_return())
    np.testing.assert_array_equal(np.random.random(3), expected)
    other = MCSimulation(prices, num_simulation=20, num_trading_days=10, seed=6)
    assert not first.equals(other.calc_cumulative_return())
    assert (first.iloc[0] == 1).all() and (first > 0).all().all()


def test_longer_horizon_preserves_the_same_seeded_prefix(prices):
    short = MCSimulation(prices, num_simulation=20, num_trading_days=5).calc_cumulative_return()
    long = MCSimulation(prices, num_simulation=20, num_trading_days=10).calc_cumulative_return()
    pd.testing.assert_frame_equal(short, long.iloc[:6])


def test_identical_assets_remain_correlated(prices):
    prices["BBB"] = prices["AAA"]
    left = MCSimulation(prices, weights=[1, 0], num_simulation=30, num_trading_days=10)
    right = MCSimulation(prices, weights=[0, 1], num_simulation=30, num_trading_days=10)
    np.testing.assert_allclose(
        left.calc_cumulative_return(), right.calc_cumulative_return(), atol=1e-8
    )


def test_opposite_log_returns_keep_daily_rebalancing_behavior():
    changes = np.array([0.1, -0.1, 0.2, -0.2])
    values = np.r_[0, np.cumsum(changes)]
    frame = pd.DataFrame(
        {"AAA": 100 * np.exp(values), "BBB": 100 * np.exp(-values)},
        index=pd.date_range("2020-01-01", periods=5),
    )
    model = MCSimulation(frame, weights=[0.5, 0.5], num_simulation=100, num_trading_days=10)
    # Perfectly opposite log shocks give (exp(r) + exp(-r))/2 >= 1 each day.
    paths = model.calc_cumulative_return()
    assert (paths.diff().iloc[1:] >= -1e-10).all().all()


def test_input_prices_and_quantiles_are_not_mutated(prices):
    original = prices.copy()
    model = MCSimulation(prices, num_simulation=20, num_trading_days=10)
    first = model.summarize_cumulative_return()
    quantiles = model.confidence_interval
    quantiles.index = ["changed", "labels"]
    pd.testing.assert_series_equal(first, model.summarize_cumulative_return())
    assert list(model.scenario_quantiles.index) == [0.025, 0.975]
    pd.testing.assert_frame_equal(prices, original)


def test_legacy_multilevel_close_input_ignores_stale_return_columns(prices):
    legacy = pd.concat(
        {
            name: pd.DataFrame({"close": prices[name], "daily_return": 999})
            for name in prices.columns
        },
        axis=1,
    )
    direct = MCSimulation(prices, num_simulation=20, num_trading_days=10)
    adapted = MCSimulation(legacy, num_simulation=20, num_trading_days=10)
    pd.testing.assert_frame_equal(direct.calc_cumulative_return(), adapted.calc_cumulative_return())


def test_each_horizon_uses_its_own_results_and_actual_mean(prices):
    result = analyze_portfolio(prices, years=(1, 3), simulations=20, initial_investment=100)
    model = MCSimulation(prices, num_simulation=20, num_trading_days=756)
    terminal = model.calc_cumulative_return().iloc[-1]
    assert result.summary.loc[3, "mean_terminal_value"] == pytest.approx(terminal.mean() * 100)
    assert result.summary.loc[3, "p025_terminal_value"] == pytest.approx(
        terminal.quantile(0.025) * 100
    )
    assert result.summary.loc[3, "simulated_loss_fraction"] == pytest.approx((terminal < 1).mean())
    assert not np.isclose(
        terminal.mean(), (terminal.quantile(0.025) + terminal.quantile(0.975)) / 2
    )
    assert result.preview.nTrading == 252


@pytest.mark.parametrize(
    "arguments",
    [
        {"years": []},
        {"years": [0]},
        {"years": [True]},
        {"years": [1.5]},
        {"years": [1, 1]},
        {"initial_investment": 0},
        {"initial_investment": -1},
        {"initial_investment": np.nan},
        {"initial_investment": np.inf},
    ],
)
def test_invalid_analysis_parameters(prices, arguments):
    with pytest.raises(ValueError):
        analyze_portfolio(prices, **arguments)


def test_plot_helpers_work_before_explicit_calculation(prices):
    model = MCSimulation(prices, num_simulation=20, num_trading_days=10)
    for plot in (model.plot_simulation, model.plot_distribution):
        axis = plot()
        assert axis.get_xlabel() and axis.get_ylabel()
        plt.close(axis.figure)
