from pathlib import Path
import sys
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core import bs_price_greeks


def test_bs_price_greeks_matches_expected_call(base_option_params):
    result = bs_price_greeks(**base_option_params)

    assert result.price == pytest.approx(5.876024, rel=1e-3)
    assert result.delta == pytest.approx(0.542235, rel=1e-3)
    assert result.gamma > 0


def test_put_greeks_use_shared_fixture(base_option_params):
    params = dict(base_option_params)
    params["cp"] = "P"

    result = bs_price_greeks(**params)

    assert result.price == pytest.approx(5.377272, rel=1e-3)
    assert result.delta < 0
    assert result.rho < 0


def test_call_price_monotonic_with_spot(short_time_series, base_option_params):
    params = dict(base_option_params)
    prices = []
    for spot in short_time_series:
        params["S"] = float(spot)
        prices.append(bs_price_greeks(**params).price)

    assert prices == sorted(prices)


def test_long_series_trend(long_time_series, typical_market_data):
    params = dict(typical_market_data)
    sampled_spots = long_time_series.iloc[::20]
    prices = []
    for spot in sampled_spots:
        params["S"] = float(spot)
        prices.append(bs_price_greeks(**params).price)

    assert all(b > a for a, b in zip(prices, prices[1:]))
