from __future__ import annotations

from datetime import datetime
from typing import List
from api.v2.portfolio_schemas import PortfolioSummaryOut, ExposureOut, MoneyOut, ConstraintsOut
from pydantic import BaseModel

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
    t = getattr(field, "outer_type_", None) or getattr(field, "type_", None)
    if t is None:
        return False
    try:
        return issubclass(t, datetime)
    except Exception:
        # for typing constructs
        return str(t).find("datetime") >= 0


def test_finance_models_no_dynamic_fields():
    """Introspect finance-facing Pydantic models for forbidden dynamic fields/types."""
    models: List[type[BaseModel]] = [PortfolioSummaryOut, ExposureOut, MoneyOut, ConstraintsOut]

    for m in models:
        for name, field in m.__fields__.items():
            assert name not in FORBIDDEN_DYNAMIC_FIELDS, f"Forbidden dynamic field in {m.__name__}: {name}"
            assert not _field_is_datetime(field), f"Datetime-like field in {m.__name__}.{name} is not allowed"


def test_portfolio_exposures_ordering_invariant():
    """Two PortfolioSummaryOut with exposures in different insertion order should serialize identically.

    This enforces that the API boundary provides a canonical ordering for list-like finance outputs.
    """
    exposures_a = [
        ExposureOut(underlying="AAA", abs_notional=100.0, delta=1.0),
        ExposureOut(underlying="BBB", abs_notional=50.0, delta=0.5),
        ExposureOut(underlying="CCC", abs_notional=75.0, delta=0.75),
    ]
    exposures_b = [exposures_a[2], exposures_a[0], exposures_a[1]]  # permuted

    base = dict(session_id="S1", version=1, pv=MoneyOut(value=1000.0, currency="USD"), delta=1.0, constraints=ConstraintsOut(passed=True, breaches=[]))

    p_a = PortfolioSummaryOut(**{**base, "exposures": exposures_a})
    p_b = PortfolioSummaryOut(**{**base, "exposures": exposures_b})

    # Serialized dicts must be identical if the contract enforces stable ordering
    assert p_a.dict() == p_b.dict(), "PortfolioSummaryOut exposures ordering is not canonical/permutation-invariant"
