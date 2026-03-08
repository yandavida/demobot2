from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError
from dataclasses import fields

import pytest

from core.contracts.valuation_context import ValuationContext


def _valuation_context(**overrides) -> ValuationContext:
    payload = {
        "valuation_context_id": "vc-2026-03-08-001",
        "valuation_timestamp": datetime.datetime(2026, 3, 8, 12, 0, 0, tzinfo=datetime.timezone.utc),
        "market_snapshot_id": "ms-2026-03-08-001",
        "reference_data_set_id": "rds-2026-03-08-001",
        "valuation_policy_set_id": "vps-2026-03-08-001",
        "pricing_currency": "usd",
        "reporting_currency": "eur",
        "run_purpose": "risk_snapshot",
    }
    payload.update(overrides)
    return ValuationContext(**payload)


def test_valuation_context_construction() -> None:
    context = _valuation_context()

    assert context.valuation_context_id == "vc-2026-03-08-001"
    assert context.pricing_currency == "USD"
    assert context.reporting_currency == "EUR"


def test_valuation_context_is_immutable() -> None:
    context = _valuation_context()

    with pytest.raises(FrozenInstanceError):
        context.run_purpose = "pricing"


def test_valuation_context_requires_all_fields() -> None:
    with pytest.raises(TypeError):
        ValuationContext(
            valuation_context_id="vc-2026-03-08-001",
            valuation_timestamp=datetime.datetime(
                2026,
                3,
                8,
                12,
                0,
                0,
                tzinfo=datetime.timezone.utc,
            ),
            market_snapshot_id="ms-2026-03-08-001",
            reference_data_set_id="rds-2026-03-08-001",
            valuation_policy_set_id="vps-2026-03-08-001",
            pricing_currency="USD",
            reporting_currency="EUR",
        )


def test_valuation_context_remains_thin_reference_object() -> None:
    allowed_fields = {
        "valuation_context_id",
        "valuation_timestamp",
        "market_snapshot_id",
        "reference_data_set_id",
        "valuation_policy_set_id",
        "pricing_currency",
        "reporting_currency",
        "run_purpose",
    }

    names = {f.name for f in fields(ValuationContext)}
    assert names == allowed_fields
    assert not any(name.endswith("_payload") for name in names)
