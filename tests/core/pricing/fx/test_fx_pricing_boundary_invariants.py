import inspect
import datetime

import pytest

from core.pricing.fx import types as fx_types


def test_fxforward_contract_rejects_non_finite_notional():
    with pytest.raises(ValueError):
        fx_types.FXForwardContract(base_currency="USD", quote_currency="EUR", notional=float("nan"), forward_date=datetime.date(2026,1,1))


def test_market_snapshot_requires_as_of_ts_and_finite_spot():
    now = datetime.datetime(2026, 2, 9, 0, 0)
    # missing as_of_ts should raise TypeError when omitted (constructor requires it)
    with pytest.raises(TypeError):
        fx_types.FxMarketSnapshot(spot_rate=1.1)

    # non-finite spot_rate rejected
    with pytest.raises(ValueError):
        fx_types.FxMarketSnapshot(as_of_ts=now, spot_rate=float("inf"))


def test_pricing_result_requires_as_of_ts_and_finite_pv():
    now = datetime.datetime(2026, 2, 9, 0, 0)
    with pytest.raises(TypeError):
        fx_types.PricingResult(pv=100.0)

    with pytest.raises(ValueError):
        fx_types.PricingResult(as_of_ts=now, pv=float("nan"))


def test_dataclass_equality_and_determinism():
    now = datetime.datetime(2026, 2, 9, 0, 0)
    c1 = fx_types.FXForwardContract("USD", "EUR", 1e6, datetime.date(2026, 3, 1))
    c2 = fx_types.FXForwardContract("USD", "EUR", 1e6, datetime.date(2026, 3, 1))
    assert c1 == c2

    s1 = fx_types.FxMarketSnapshot(as_of_ts=now, spot_rate=1.05)
    s2 = fx_types.FxMarketSnapshot(as_of_ts=now, spot_rate=1.05)
    assert s1 == s2


def test_no_core_imports_api_in_module_source():
    src = inspect.getsource(fx_types)
    assert "import api" not in src
    assert "from api" not in src
