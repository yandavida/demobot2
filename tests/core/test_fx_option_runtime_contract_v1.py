from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1


def _contract(**overrides: object) -> FxOptionRuntimeContractV1:
    payload: dict[str, object] = {
        "contract_id": "fx-opt-001",
        "currency_pair_orientation": "base_per_quote",
        "base_currency": "usd",
        "quote_currency": "ils",
        "option_type": "call",
        "exercise_style": "european",
        "strike": "3.65",
        "expiry_date": datetime.date(2026, 12, 31),
        "expiry_cutoff_time": datetime.time(10, 0, 0),
        "expiry_cutoff_timezone": "Asia/Jerusalem",
        "notional": "1000000",
        "notional_currency_semantics": "base_currency",
        "premium_currency": "usd",
        "premium_payment_date": datetime.date(2026, 6, 1),
        "settlement_style": "deliverable",
        "settlement_date": datetime.date(2027, 1, 4),
        "settlement_calendar_refs": ("IL-TASE", "US-NYFED"),
        "fixing_source": "WM/Reuters 4pm",
        "fixing_date": datetime.date(2026, 12, 31),
        "domestic_curve_id": "curve.ils.ois.v1",
        "foreign_curve_id": "curve.usd.ois.v1",
        "volatility_surface_quote_convention": "delta-neutral-vol",
    }
    payload.update(overrides)
    return FxOptionRuntimeContractV1(**payload)


def test_constructs_with_complete_fx_option_terms() -> None:
    contract = _contract()

    assert contract.contract_id == "fx-opt-001"
    assert contract.currency_pair_orientation == "base_per_quote"
    assert contract.base_currency == "USD"
    assert contract.quote_currency == "ILS"
    assert contract.option_type == "call"
    assert contract.exercise_style == "european"
    assert contract.strike == Decimal("3.65")
    assert contract.expiry_date == datetime.date(2026, 12, 31)
    assert contract.expiry_cutoff_time == datetime.time(10, 0, 0)
    assert contract.expiry_cutoff_timezone == "Asia/Jerusalem"
    assert contract.notional == Decimal("1000000")
    assert contract.notional_currency_semantics == "base_currency"
    assert contract.premium_currency == "USD"
    assert contract.premium_payment_date == datetime.date(2026, 6, 1)
    assert contract.settlement_style == "deliverable"
    assert contract.settlement_date == datetime.date(2027, 1, 4)
    assert contract.settlement_calendar_refs == ("IL-TASE", "US-NYFED")
    assert contract.fixing_source == "WM/Reuters 4pm"
    assert contract.fixing_date == datetime.date(2026, 12, 31)
    assert contract.domestic_curve_id == "curve.ils.ois.v1"
    assert contract.foreign_curve_id == "curve.usd.ois.v1"
    assert contract.volatility_surface_quote_convention == "delta-neutral-vol"


def test_contract_is_immutable() -> None:
    contract = _contract()

    with pytest.raises(FrozenInstanceError):
        contract.settlement_style = "non_deliverable"


def test_required_fx_terms_reject_empty_values() -> None:
    with pytest.raises(ValueError, match="contract_id"):
        _contract(contract_id="")

    with pytest.raises(ValueError, match="fixing_source"):
        _contract(fixing_source="")

    with pytest.raises(ValueError, match="domestic_curve_id"):
        _contract(domestic_curve_id="")


def test_premium_semantics_are_explicit_and_typed() -> None:
    with pytest.raises(ValueError, match="premium_currency"):
        _contract(premium_currency="")

    with pytest.raises(ValueError, match="premium_payment_date"):
        _contract(premium_payment_date="2026-06-01")


def test_settlement_semantics_are_explicit_and_validated() -> None:
    with pytest.raises(ValueError, match="settlement_style"):
        _contract(settlement_style="cash")

    with pytest.raises(ValueError, match="settlement_calendar_refs"):
        _contract(settlement_calendar_refs=())


def test_fixing_semantics_are_explicit_and_typed() -> None:
    with pytest.raises(ValueError, match="fixing_date"):
        _contract(fixing_date="2026-12-31")

    with pytest.raises(ValueError, match="expiry_cutoff_time"):
        _contract(expiry_cutoff_time="10:00:00")


def test_rejects_invalid_key_fx_economic_terms() -> None:
    with pytest.raises(ValueError, match="notional"):
        _contract(notional="0")

    with pytest.raises(ValueError, match="strike"):
        _contract(strike="-1")


def test_rejects_invalid_structural_use_with_unrelated_fields() -> None:
    with pytest.raises(TypeError):
        _contract(pricing_engine_id="bs.v1")

    with pytest.raises(TypeError):
        _contract(lifecycle_state="pending")
