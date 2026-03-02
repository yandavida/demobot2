"""Gate G9.1 — RiskRequest contract tests (T1–T6).

All tests are deterministic:
- No wall-clock
- No randomness
- Exact equality only (no tolerances)
"""
from __future__ import annotations

import datetime
from decimal import Decimal

import pytest

from core.pricing.fx.valuation_context import ValuationContext
from core.risk.risk_request import (
    SUPPORTED_SCHEMA_VERSION,
    RiskRequest,
    RiskValidationError,
)
from core.risk.scenario_spec import ScenarioSpec


def _context() -> ValuationContext:
    return ValuationContext(
        as_of_ts=datetime.datetime(
            2026, 3, 2, 12, 0, 0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
        ),
        domestic_currency="ILS",
        strict_mode=True,
    )


def _spec() -> ScenarioSpec:
    return ScenarioSpec(
        schema_version=1,
        spot_shocks=(Decimal("-0.05"), Decimal("0"), Decimal("0.05")),
        df_domestic_shocks=(Decimal("-0.01"), Decimal("0"), Decimal("0.01")),
        df_foreign_shocks=(Decimal("-0.01"), Decimal("0"), Decimal("0.01")),
    )


def _valid_request(**overrides) -> RiskRequest:
    defaults = {
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "valuation_context": _context(),
        "market_snapshot_id": "snap-abc123",
        "instrument_ids": ("usd_ils_fwd_001", "usd_ils_fwd_002"),
        "scenario_spec": _spec(),
        "strict": True,
    }
    defaults.update(overrides)
    return RiskRequest(**defaults)


# ──────────────────────────────────────────────────────────────────────────────
# T1: schema_version required
# ──────────────────────────────────────────────────────────────────────────────

def test_t1_schema_version_none_is_rejected():
    with pytest.raises(RiskValidationError) as exc_info:
        _valid_request(schema_version=None)
    assert exc_info.value.envelope.code in (
        "MISSING_SCHEMA_VERSION",
        "UNSUPPORTED_SCHEMA_VERSION",
    )


# ──────────────────────────────────────────────────────────────────────────────
# T2: unsupported schema_version rejected
# ──────────────────────────────────────────────────────────────────────────────

def test_t2_unsupported_schema_version_rejected():
    with pytest.raises(RiskValidationError) as exc_info:
        _valid_request(schema_version=99)
    assert exc_info.value.envelope.code == "UNSUPPORTED_SCHEMA_VERSION"
    assert exc_info.value.envelope.category == "VALIDATION"


def test_t2_zero_schema_version_rejected():
    with pytest.raises(RiskValidationError) as exc_info:
        _valid_request(schema_version=0)
    assert exc_info.value.envelope.code == "UNSUPPORTED_SCHEMA_VERSION"


# ──────────────────────────────────────────────────────────────────────────────
# T3: instrument_ids sorted deterministically
# ──────────────────────────────────────────────────────────────────────────────

def test_t3_instrument_ids_sorted_on_construction():
    req = _valid_request(
        instrument_ids=("zzz_instr", "aaa_instr", "mmm_instr"),
    )
    assert req.instrument_ids == ("aaa_instr", "mmm_instr", "zzz_instr")


def test_t3_different_input_order_same_result():
    req_a = _valid_request(instrument_ids=("c", "a", "b"))
    req_b = _valid_request(instrument_ids=("b", "c", "a"))
    assert req_a.instrument_ids == req_b.instrument_ids == ("a", "b", "c")


# ──────────────────────────────────────────────────────────────────────────────
# T4: duplicate instrument_ids removed deterministically
# ──────────────────────────────────────────────────────────────────────────────

def test_t4_duplicates_removed():
    req = _valid_request(
        instrument_ids=("fwd_001", "fwd_002", "fwd_001", "fwd_002", "fwd_003"),
    )
    assert req.instrument_ids == ("fwd_001", "fwd_002", "fwd_003")


def test_t4_all_duplicates_collapses_to_unique():
    req = _valid_request(instrument_ids=("fwd_x", "fwd_x", "fwd_x"))
    assert req.instrument_ids == ("fwd_x",)


# ──────────────────────────────────────────────────────────────────────────────
# T5: strict vs lenient both reject invalid request — no partial accept
# ──────────────────────────────────────────────────────────────────────────────

def test_t5_strict_mode_rejects_empty_instrument_ids():
    with pytest.raises(RiskValidationError) as exc_info:
        _valid_request(instrument_ids=(), strict=True)
    env = exc_info.value.envelope
    assert env.code == "VALIDATION_ERROR"
    assert env.category == "VALIDATION"


def test_t5_lenient_mode_also_rejects_empty_instrument_ids():
    with pytest.raises(RiskValidationError) as exc_info:
        _valid_request(instrument_ids=(), strict=False)
    env = exc_info.value.envelope
    assert env.code == "VALIDATION_ERROR"


def test_t5_lenient_mode_includes_validation_mode_in_details():
    with pytest.raises(RiskValidationError) as exc_info:
        _valid_request(instrument_ids=(), strict=False)
    details = exc_info.value.envelope.details
    assert details.get("validation_mode") == "lenient"


def test_t5_strict_mode_does_not_include_validation_mode_key():
    with pytest.raises(RiskValidationError) as exc_info:
        _valid_request(instrument_ids=(), strict=True)
    details = exc_info.value.envelope.details
    assert "validation_mode" not in details


def test_t5_empty_market_snapshot_id_rejected_strict():
    with pytest.raises(RiskValidationError):
        _valid_request(market_snapshot_id="", strict=True)


def test_t5_empty_market_snapshot_id_rejected_lenient():
    with pytest.raises(RiskValidationError):
        _valid_request(market_snapshot_id="", strict=False)


# ──────────────────────────────────────────────────────────────────────────────
# T6: immutability — frozen dataclass cannot be mutated
# ──────────────────────────────────────────────────────────────────────────────

def test_t6_instrument_ids_immutable():
    req = _valid_request()
    with pytest.raises((AttributeError, TypeError)):
        req.instrument_ids = ("new_fwd",)  # type: ignore[misc]


def test_t6_schema_version_immutable():
    req = _valid_request()
    with pytest.raises((AttributeError, TypeError)):
        req.schema_version = 2  # type: ignore[misc]


def test_t6_valid_request_is_constructable():
    req = _valid_request()
    assert req.schema_version == SUPPORTED_SCHEMA_VERSION
    assert req.strict is True
    assert len(req.instrument_ids) >= 1
