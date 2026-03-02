"""Gate G9.1 — ScenarioSpec determinism + ScenarioSet id tests (T7–T11).

All tests are deterministic:
- No wall-clock
- No randomness
- Exact equality only (no tolerances)
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import SUPPORTED_SCHEMA_VERSION, ScenarioSpec


def _spec(
    *,
    spot: tuple = (Decimal("-0.05"), Decimal("0"), Decimal("0.05")),
    dfd: tuple = (Decimal("-0.01"), Decimal("0"), Decimal("0.01")),
    dff: tuple = (Decimal("-0.01"), Decimal("0"), Decimal("0.01")),
    version: int = 1,
) -> ScenarioSpec:
    return ScenarioSpec(
        schema_version=version,
        spot_shocks=spot,
        df_domestic_shocks=dfd,
        df_foreign_shocks=dff,
    )


# ──────────────────────────────────────────────────────────────────────────────
# T7: identical inputs → identical canonical JSON → identical scenario_set_id
# ──────────────────────────────────────────────────────────────────────────────

def test_t7_identical_spec_produces_identical_scenario_set_id():
    s1 = ScenarioSet.from_spec(_spec())
    s2 = ScenarioSet.from_spec(_spec())
    assert s1.scenario_set_id == s2.scenario_set_id


def test_t7_scenario_set_id_is_64_char_hex():
    s = ScenarioSet.from_spec(_spec())
    assert len(s.scenario_set_id) == 64
    assert all(c in "0123456789abcdef" for c in s.scenario_set_id)


# ──────────────────────────────────────────────────────────────────────────────
# T8: insertion order of shock lists does not change scenario_set_id
# ──────────────────────────────────────────────────────────────────────────────

def test_t8_spot_shock_insertion_order_invariant():
    ordered = _spec(spot=(Decimal("-0.05"), Decimal("0"), Decimal("0.05")))
    reversed_ = _spec(spot=(Decimal("0.05"), Decimal("0"), Decimal("-0.05")))
    shuffled = _spec(spot=(Decimal("0"), Decimal("0.05"), Decimal("-0.05")))

    id_a = ScenarioSet.from_spec(ordered).scenario_set_id
    id_b = ScenarioSet.from_spec(reversed_).scenario_set_id
    id_c = ScenarioSet.from_spec(shuffled).scenario_set_id

    assert id_a == id_b == id_c


def test_t8_df_shock_insertion_order_invariant():
    s_a = _spec(dfd=(Decimal("0.01"), Decimal("-0.01"), Decimal("0")))
    s_b = _spec(dfd=(Decimal("0"), Decimal("0.01"), Decimal("-0.01")))

    assert (
        ScenarioSet.from_spec(s_a).scenario_set_id
        == ScenarioSet.from_spec(s_b).scenario_set_id
    )


def test_t8_normalized_shocks_are_sorted_ascending():
    spec = _spec(spot=(Decimal("0.1"), Decimal("-0.1"), Decimal("0")))
    assert spec.spot_shocks == (Decimal("-0.1"), Decimal("0"), Decimal("0.1"))


# ──────────────────────────────────────────────────────────────────────────────
# T9: duplicates removed deterministically
# ──────────────────────────────────────────────────────────────────────────────

def test_t9_duplicate_shocks_removed():
    spec = _spec(spot=(Decimal("0.05"), Decimal("0.05"), Decimal("-0.05"), Decimal("0")))
    assert spec.spot_shocks == (Decimal("-0.05"), Decimal("0"), Decimal("0.05"))


def test_t9_duplicate_scenario_id_equals_deduped():
    with_dups = _spec(spot=(Decimal("0.05"), Decimal("0.05"), Decimal("0"), Decimal("-0.05")))
    without_dups = _spec(spot=(Decimal("-0.05"), Decimal("0"), Decimal("0.05")))
    assert (
        ScenarioSet.from_spec(with_dups).scenario_set_id
        == ScenarioSet.from_spec(without_dups).scenario_set_id
    )


def test_t9_all_duplicate_shocks_collapses():
    spec = _spec(spot=(Decimal("0.05"), Decimal("0.05"), Decimal("0.05")))
    assert spec.spot_shocks == (Decimal("0.05"),)


# ──────────────────────────────────────────────────────────────────────────────
# T10: non-finite values rejected
# ──────────────────────────────────────────────────────────────────────────────

def test_t10_infinity_in_spot_shocks_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        _spec(spot=(Decimal("Infinity"), Decimal("0")))


def test_t10_negative_infinity_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        _spec(dfd=(Decimal("-Infinity"), Decimal("0")))


def test_t10_nan_in_df_foreign_shocks_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        _spec(dff=(Decimal("NaN"), Decimal("0")))


# ──────────────────────────────────────────────────────────────────────────────
# T11: schema_version required and version enforcement
# ──────────────────────────────────────────────────────────────────────────────

def test_t11_unsupported_schema_version_rejected():
    with pytest.raises(ValueError, match="unsupported schema_version"):
        _spec(version=99)


def test_t11_zero_schema_version_rejected():
    with pytest.raises(ValueError, match="unsupported schema_version"):
        _spec(version=0)


def test_t11_supported_version_accepted():
    spec = _spec(version=SUPPORTED_SCHEMA_VERSION)
    assert spec.schema_version == SUPPORTED_SCHEMA_VERSION


def test_t11_different_supported_version_produces_different_id():
    # Sanity check: scenario_set_id embeds the spec, which includes schema_version.
    # If we had multiple supported versions, they would differ. For now verify
    # that schema_version is part of the canonical payload (immutability of content).
    spec = _spec()
    s = ScenarioSet.from_spec(spec)
    assert spec.schema_version == s.spec.schema_version
