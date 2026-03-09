from __future__ import annotations

from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1


def test_enum_freeze_matches_approved_canonical_names() -> None:
    assert [member.value for member in ValuationMeasureNameV1] == [
        "present_value",
        "intrinsic_value",
        "time_value",
        "delta_spot_non_premium_adjusted",
        "gamma_spot",
        "vega_1vol_abs",
        "theta_1d_calendar",
        "rho_domestic_1pct",
        "rho_foreign_1pct",
    ]


def test_enum_is_alias_free_and_has_no_accidental_additions() -> None:
    values = [member.value for member in ValuationMeasureNameV1]
    assert len(values) == len(set(values))
    assert len(values) == 9
