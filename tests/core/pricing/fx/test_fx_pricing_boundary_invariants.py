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


# F8.1A boundary extension tests (backward compatibility)

def test_fxforward_contract_backward_compatible_construction():
    """F8.1 4-arg construction MUST still work (backward compatibility)."""
    # Original F8.1 signature
    c = fx_types.FXForwardContract("USD", "EUR", 1e6, datetime.date(2026, 3, 1))
    assert c.base_currency == "USD"
    assert c.quote_currency == "EUR"
    assert c.notional == 1e6
    assert c.forward_date == datetime.date(2026, 3, 1)
    # New optional fields should be None
    assert c.forward_rate is None
    assert c.direction is None


def test_fxforward_contract_extended_fields_optional():
    """New forward_rate and direction fields are optional."""
    # With forward_rate only
    c1 = fx_types.FXForwardContract(
        "USD", "EUR", 1e6, datetime.date(2026, 3, 1), forward_rate=1.10
    )
    assert c1.forward_rate == 1.10
    assert c1.direction is None
    
    # With direction only
    c2 = fx_types.FXForwardContract(
        "USD", "EUR", 1e6, datetime.date(2026, 3, 1), direction="receive_foreign_pay_domestic"
    )
    assert c2.forward_rate is None
    assert c2.direction == "receive_foreign_pay_domestic"
    
    # With both
    c3 = fx_types.FXForwardContract(
        "USD", "EUR", 1e6, datetime.date(2026, 3, 1), 
        forward_rate=1.10, direction="receive_foreign_pay_domestic"
    )
    assert c3.forward_rate == 1.10
    assert c3.direction == "receive_foreign_pay_domestic"


def test_fxforward_contract_forward_rate_must_be_finite():
    """If forward_rate is provided, it must be finite."""
    with pytest.raises(ValueError):
        fx_types.FXForwardContract(
            "USD", "EUR", 1e6, datetime.date(2026, 3, 1), forward_rate=float("nan")
        )
    
    with pytest.raises(ValueError):
        fx_types.FXForwardContract(
            "USD", "EUR", 1e6, datetime.date(2026, 3, 1), forward_rate=float("inf")
        )


def test_fxforward_contract_direction_must_be_valid():
    """If direction is provided, it must be one of the allowed values."""
    # Valid directions
    c1 = fx_types.FXForwardContract(
        "USD", "EUR", 1e6, datetime.date(2026, 3, 1), 
        direction="receive_foreign_pay_domestic"
    )
    assert c1.direction == "receive_foreign_pay_domestic"
    
    c2 = fx_types.FXForwardContract(
        "USD", "EUR", 1e6, datetime.date(2026, 3, 1), 
        direction="pay_foreign_receive_domestic"
    )
    assert c2.direction == "pay_foreign_receive_domestic"
    
    # Invalid direction
    with pytest.raises(ValueError):
        fx_types.FXForwardContract(
            "USD", "EUR", 1e6, datetime.date(2026, 3, 1), direction="invalid_direction"
        )


def test_market_snapshot_extended_fields_optional():
    """New df_domestic and df_foreign fields are optional."""
    now = datetime.datetime(2026, 2, 9, 0, 0)
    
    # Original F8.1 construction
    s1 = fx_types.FxMarketSnapshot(as_of_ts=now, spot_rate=1.05)
    assert s1.df_domestic is None
    assert s1.df_foreign is None
    
    # With df_domestic only
    s2 = fx_types.FxMarketSnapshot(as_of_ts=now, spot_rate=1.05, df_domestic=0.99)
    assert s2.df_domestic == 0.99
    assert s2.df_foreign is None
    
    # With df_foreign only
    s3 = fx_types.FxMarketSnapshot(as_of_ts=now, spot_rate=1.05, df_foreign=0.98)
    assert s3.df_domestic is None
    assert s3.df_foreign == 0.98
    
    # With both
    s4 = fx_types.FxMarketSnapshot(
        as_of_ts=now, spot_rate=1.05, df_domestic=0.99, df_foreign=0.98
    )
    assert s4.df_domestic == 0.99
    assert s4.df_foreign == 0.98


def test_market_snapshot_discount_factors_must_be_finite():
    """If df_domestic or df_foreign are provided, they must be finite."""
    now = datetime.datetime(2026, 2, 9, 0, 0)
    
    # Non-finite df_domestic
    with pytest.raises(ValueError):
        fx_types.FxMarketSnapshot(
            as_of_ts=now, spot_rate=1.05, df_domestic=float("nan")
        )
    
    # Non-finite df_foreign
    with pytest.raises(ValueError):
        fx_types.FxMarketSnapshot(
            as_of_ts=now, spot_rate=1.05, df_foreign=float("inf")
        )
