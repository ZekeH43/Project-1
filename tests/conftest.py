"""Small synthetic histories let tests verify behavior without market forecasts."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def prices():
    rng = np.random.default_rng(7)
    changes = rng.normal(0.001, 0.02, size=(29, 2))
    values = np.vstack([np.ones(2), np.exp(np.cumsum(changes, axis=0))]) * 100
    return pd.DataFrame(
        values, index=pd.date_range("2020-01-01", periods=30, freq="B"), columns=["AAA", "BBB"]
    )
