from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from core.contracts.option_runtime_contract_v1 import OptionRuntimeContractV1


def _contract(**overrides: object) -> OptionRuntimeContractV1:
    payload: dict[str, object] = {
        "contract_id": "opt-rt-001",
        "underlying_instrument_ref": "USD/ILS",
        "option_type": "call",
        "exercise_style": "european",
        "strike": "3.65",
        "expiry_date": datetime.date(2026, 12, 31),
        "notional": "1000000",
        "notional_currency": "usd",
    }
    payload.update(overrides)
    return OptionRuntimeContractV1(**payload)


def test_constructs_with_explicit_option_domain_fields() -> None:
    contract = _contract()

    assert contract.contract_id == "opt-rt-001"
    assert contract.underlying_instrument_ref == "USD/ILS"
    assert contract.option_type == "call"
    assert contract.exercise_style == "european"
    assert contract.strike == Decimal("3.65")
    assert contract.expiry_date == datetime.date(2026, 12, 31)
    assert contract.notional == Decimal("1000000")
    assert contract.notional_currency == "USD"


def test_contract_is_immutable() -> None:
    contract = _contract()

    with pytest.raises(FrozenInstanceError):
        contract.option_type = "put"


def test_required_fields_reject_empty_values() -> None:
    with pytest.raises(ValueError, match="contract_id"):
        _contract(contract_id="")

    with pytest.raises(ValueError, match="underlying_instrument_ref"):
        _contract(underlying_instrument_ref="")

    with pytest.raises(ValueError, match="notional_currency"):
        _contract(notional_currency="")


def test_option_type_must_be_explicit_supported_value() -> None:
    with pytest.raises(ValueError, match="option_type"):
        _contract(option_type="digital")


def test_exercise_style_must_be_explicit_supported_value() -> None:
    with pytest.raises(ValueError, match="exercise_style"):
        _contract(exercise_style="bermudan")


def test_rejects_invalid_structural_field_types() -> None:
    with pytest.raises(ValueError, match="expiry_date"):
        _contract(expiry_date="2026-12-31")

    with pytest.raises(ValueError, match="strike"):
        _contract(strike="0")

    with pytest.raises(ValueError, match="notional"):
        _contract(notional="-1")


def test_rejects_accidental_pricing_or_lifecycle_payload_fields() -> None:
    with pytest.raises(TypeError):
        _contract(pricing_engine_id="bs.v1")

    with pytest.raises(TypeError):
        _contract(lifecycle_state="open")
