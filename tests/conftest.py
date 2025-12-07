import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def base_option_params() -> dict:
    """Baseline option parameters for quick greeks checks."""
    return {
        "S": 100.0,
        "K": 100.0,
        "r": 0.01,
        "q": 0.0,
        "sigma": 0.2,
        "T": 0.5,
        "cp": "C",
    }


@pytest.fixture
def typical_market_data() -> dict:
    """Representative market data point close to the UI defaults."""
    return {
        "S": 3317.09,
        "K": 3300.0,
        "r": 0.02,
        "q": 0.0,
        "sigma": 0.18,
        "T": 30 / 365,
        "cp": "C",
    }


@pytest.fixture
def short_time_series() -> pd.Series:
    """A small series of spot prices to validate monotonic relationships."""
    return pd.Series([95.0, 97.5, 100.0, 102.5, 105.0], name="spot")


@pytest.fixture
def long_time_series() -> pd.Series:
    """Longer synthetic history for stability-sensitive checks."""
    return pd.Series(np.linspace(3000.0, 3400.0, 120), name="spot")
