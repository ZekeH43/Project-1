"""Check CSV cleaning, date alignment, and actual committed input files."""

import numpy as np
import pandas as pd
import pytest

from risk_reward.data import available_tickers, load_prices, validate_prices


def test_loader_parses_dollars_and_sorts_dates_without_using_volume(tmp_path):
    (tmp_path / "AAA_data.csv").write_text(
        'Date,Close/Last,Volume\n1/3/2020,"$1,020.00",N/A\n1/1/2020,$1000,10\n1/2/2020,$1010,20\n'
    )
    prices = load_prices("aaa", tmp_path)
    np.testing.assert_array_equal(prices.AAA, [1000, 1010, 1020])
    assert prices.index.is_monotonic_increasing


def test_alignment_uses_common_dates_without_forward_filling(tmp_path):
    (tmp_path / "AAA_data.csv").write_text(
        "Date,Close/Last\n1/1/2020,100\n1/2/2020,101\n1/3/2020,102\n1/4/2020,103\n"
    )
    (tmp_path / "BBB_data.csv").write_text(
        "Date,Close/Last\n1/2/2020,200\n1/3/2020,202\n1/4/2020,204\n1/5/2020,206\n"
    )
    prices = load_prices(["BBB", "AAA"], tmp_path)
    assert list(prices.columns) == ["BBB", "AAA"]
    assert list(prices.index.day) == [2, 3, 4]
    np.testing.assert_array_equal(prices.AAA, [101, 102, 103])


@pytest.mark.parametrize("value", [0, -1, np.nan, np.inf])
def test_invalid_prices_are_rejected(prices, value):
    prices.iloc[0, 0] = value
    with pytest.raises(ValueError, match="finite and strictly positive"):
        validate_prices(prices)


def test_duplicate_or_reverse_dates_are_rejected(prices):
    for frame in (prices.iloc[::-1], pd.concat([prices, prices.iloc[[-1]]])):
        with pytest.raises(ValueError, match="unique and sorted"):
            validate_prices(frame)


def test_missing_date_or_asset_schema_is_rejected(prices):
    with pytest.raises(ValueError, match="DatetimeIndex"):
        validate_prices(prices.reset_index(drop=True))
    with pytest.raises(ValueError, match="three common"):
        validate_prices(prices.iloc[:2])
    with pytest.raises(ValueError, match="unique asset"):
        validate_prices(pd.concat([prices, prices], axis=1))


@pytest.mark.parametrize("tickers", [[], ["AAA", "aaa"], ["../.env"]])
def test_invalid_ticker_selection(tickers):
    with pytest.raises(ValueError):
        load_prices(tickers)


def test_missing_ntes_is_not_substituted_with_nettf():
    assert "NETTF" in available_tickers()
    assert "NTES" not in available_tickers()
    with pytest.raises(ValueError, match="No CSV for NTES"):
        load_prices(["NTES"])


@pytest.mark.parametrize("ticker", available_tickers())
def test_all_committed_price_files_load(ticker):
    prices = load_prices([ticker])
    assert len(prices) >= 3 and (prices > 0).all().all()
    assert prices.index[-1] == pd.Timestamp("2023-11-01")
