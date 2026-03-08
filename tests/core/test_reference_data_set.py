from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.contracts.reference_data_set import ReferenceDataSet


def _reference_data_set(**overrides) -> ReferenceDataSet:
    payload = {
        "calendar_version": "cal-v2026-01",
        "holiday_calendar_refs": ["cal.us.nyfed", "cal.il.tase"],
        "day_count_convention_refs": ["dcc.ACT_365F"],
        "business_day_adjustment_refs": ["bda.MOD_FOLLOWING"],
        "settlement_convention_refs": ["set.fx.spot_t2"],
        "fixing_source_refs": ["fix.wm_reuters_16"],
        "exercise_convention_refs": ["ex.european.at_expiry"],
        "taxonomy_mapping_refs": ["tax.fxopt.g10"],
        "reference_data_version_id": "refdata-2026-01-31",
    }
    payload.update(overrides)
    return ReferenceDataSet(**payload)


def test_reference_data_set_construction() -> None:
    ref_data = _reference_data_set()

    assert ref_data.calendar_version == "cal-v2026-01"
    assert ref_data.reference_data_version_id == "refdata-2026-01-31"
    assert isinstance(ref_data.holiday_calendar_refs, tuple)


def test_reference_data_set_is_immutable() -> None:
    ref_data = _reference_data_set()

    with pytest.raises(FrozenInstanceError):
        ref_data.calendar_version = "cal-v2027-01"


def test_reference_data_set_requires_all_fields() -> None:
    with pytest.raises(TypeError):
        ReferenceDataSet(
            calendar_version="cal-v2026-01",
            holiday_calendar_refs=("cal.us.nyfed",),
            day_count_convention_refs=("dcc.ACT_365F",),
            business_day_adjustment_refs=("bda.MOD_FOLLOWING",),
            settlement_convention_refs=("set.fx.spot_t2",),
            fixing_source_refs=("fix.wm_reuters_16",),
            exercise_convention_refs=("ex.european.at_expiry",),
            reference_data_version_id="refdata-2026-01-31",
        )
