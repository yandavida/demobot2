from __future__ import annotations

from typing import List
from pydantic import BaseModel

from api.v2.american_schemas import AmericanOptionValuationOut, AmericanOptionGreeksOut

FORBIDDEN_DYNAMIC_FIELDS = {
    "created_at",
    "updated_at",
    "timestamp",
    "ts",
    "time",
    "uuid",
    "id",
    "idempotency_key",
}


def _field_is_datetime(field) -> bool:
    ann = field.get("annotation") if isinstance(field, dict) else None
    if ann is None:
        return False
    try:
        import datetime as _dt

        return issubclass(ann, _dt.datetime) or issubclass(ann, _dt.date)
    except Exception:
        return "datetime" in str(ann) or "date" in str(ann)


def test_american_models_no_dynamic_fields():
    """Introspect American-facing Pydantic models for forbidden dynamic fields/types."""
    models: List[type[BaseModel]] = [AmericanOptionValuationOut, AmericanOptionGreeksOut]

    for m in models:
        for name, field in m.model_fields.items():
            assert name not in FORBIDDEN_DYNAMIC_FIELDS, f"Forbidden dynamic field in {m.__name__}: {name}"
            assert not _field_is_datetime(field), f"Datetime-like field in {m.__name__}.{name} is not allowed"


def test_american_serialization_determinism():
    """Two logically-equivalent instances created with different insertion orders must serialize identically.

    This enforces deterministic serialization at the API boundary (no dynamic fields or non-deterministic ordering).
    """
    base_a = {
        "symbol": "ABC",
        "option_type": "call",
        "expiry": "2030-01-01",
        "spot": 100.0,
        "strike": 95.0,
        "price": {"value": 6.5, "currency": "USD"},
        "greeks": {"delta": 0.6, "gamma": 0.02, "vega": 0.10, "theta": -0.01},
    }

    # different insertion order
    base_b = {
        "price": {"currency": "USD", "value": 6.5},
        "greeks": {"gamma": 0.02, "delta": 0.6, "vega": 0.10, "theta": -0.01},
        "strike": 95.0,
        "symbol": "ABC",
        "option_type": "call",
        "expiry": "2030-01-01",
        "spot": 100.0,
    }

    a = AmericanOptionValuationOut(**base_a)
    b = AmericanOptionValuationOut(**base_b)

    # Use pydantic v2 JSON dump for deterministic serialization; require byte-identical strings
    assert a.model_dump_json(indent=2) == b.model_dump_json(indent=2)
