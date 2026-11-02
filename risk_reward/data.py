"""Read the historical CSVs without API keys or working-directory assumptions."""

import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "Resources csv"


def available_tickers(data_dir: Path = DEFAULT_DATA_DIR) -> list[str]:
    """List actual CSV names; never substitute a different ticker's data."""
    return sorted(path.name.removesuffix("_data.csv") for path in Path(data_dir).glob("*_data.csv"))


def normalize_tickers(tickers) -> list[str]:
    """Normalize symbols and reject duplicate names or file-path input."""
    if isinstance(tickers, str):
        tickers = [tickers]
    symbols = [str(symbol).strip().upper() for symbol in tickers]
    if not symbols or any(not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,14}", s) for s in symbols):
        raise ValueError("Provide one or more ticker symbols, not file paths.")
    if len(set(symbols)) != len(symbols):
        raise ValueError("Ticker symbols must be unique.")
    return symbols


def validate_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Copy a chronological price matrix, rejecting unusable observations."""
    if not isinstance(prices, pd.DataFrame):
        raise TypeError("Prices must be a pandas DataFrame.")
    if prices.shape[1] == 0 or prices.shape[0] < 3:
        raise ValueError("At least three common price dates and one asset are required.")
    if prices.columns.has_duplicates:
        raise ValueError("Price columns must have unique asset names.")
    if not isinstance(prices.index, pd.DatetimeIndex) or prices.index.hasnans:
        raise ValueError("Prices need a valid DatetimeIndex.")
    if not prices.index.is_unique or not prices.index.is_monotonic_increasing:
        raise ValueError("Price dates must be unique and sorted from oldest to newest.")
    try:
        numeric = prices.apply(pd.to_numeric, errors="raise").astype(float)
    except (ValueError, TypeError) as exc:
        raise ValueError("Closing prices must be numeric.") from exc
    if not np.isfinite(numeric.to_numpy()).all() or (numeric <= 0).any().any():
        raise ValueError(
            "Closing prices must be finite and strictly positive, with no missing values."
        )
    return numeric.copy()


def read_price_csv(path: Path, ticker: str) -> pd.Series:
    """Read Date and Close/Last; unused OHLC/volume columns may contain N/A."""
    frame = pd.read_csv(path, encoding="utf-8-sig")
    if not {"Date", "Close/Last"}.issubset(frame.columns):
        raise ValueError(f"{path.name} needs Date and Close/Last columns.")
    try:
        dates = pd.to_datetime(frame["Date"], format="%m/%d/%Y", errors="raise")
        values = pd.to_numeric(
            frame["Close/Last"].astype(str).str.replace(r"[$,\s]", "", regex=True),
            errors="raise",
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{path.name} contains invalid dates or closing prices.") from exc
    prices = pd.DataFrame({ticker: values.to_numpy()}, index=pd.DatetimeIndex(dates))
    return validate_prices(prices.sort_index())[ticker]


def load_prices(tickers, data_dir: Path = DEFAULT_DATA_DIR) -> pd.DataFrame:
    """Align assets on their common observed dates; never forward-fill prices.

    CSVs are stored in reverse chronological order. Each file is sorted before
    alignment. Differing histories shorten the shared window; missing market
    sessions and unverified price adjustments remain data limitations.
    """
    series = []
    for ticker in normalize_tickers(tickers):
        path = Path(data_dir) / f"{ticker}_data.csv"
        if not path.is_file():
            choices = ", ".join(available_tickers(data_dir)) or "none"
            raise ValueError(f"No CSV for {ticker}. Available tickers: {choices}.")
        series.append(read_price_csv(path, ticker))
    return validate_prices(pd.concat(series, axis=1, join="inner").sort_index())


def source_metadata(tickers, data_dir: Path = DEFAULT_DATA_DIR) -> list[dict]:
    """Record source hashes and date ranges so a result can be traced to its input."""
    sources = []
    for ticker in normalize_tickers(tickers):
        path = Path(data_dir) / f"{ticker}_data.csv"
        prices = read_price_csv(path, ticker)
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        sources.append(
            {
                "ticker": ticker,
                "file": path.name,
                "sha256": digest,
                "rows": len(prices),
                "start": prices.index[0].date().isoformat(),
                "end": prices.index[-1].date().isoformat(),
            }
        )
    return sources
