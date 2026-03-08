from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def _normalize_ref_list(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} entries must be non-empty strings")
        normalized.append(value.strip())
    return tuple(normalized)


@dataclass(frozen=True)
class ReferenceDataSet:
    calendar_version: str
    holiday_calendar_refs: tuple[str, ...]
    day_count_convention_refs: tuple[str, ...]
    business_day_adjustment_refs: tuple[str, ...]
    settlement_convention_refs: tuple[str, ...]
    fixing_source_refs: tuple[str, ...]
    exercise_convention_refs: tuple[str, ...]
    taxonomy_mapping_refs: tuple[str, ...]
    reference_data_version_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.calendar_version, str) or not self.calendar_version.strip():
            raise ValueError("calendar_version must be a non-empty string")
        if (
            not isinstance(self.reference_data_version_id, str)
            or not self.reference_data_version_id.strip()
        ):
            raise ValueError("reference_data_version_id must be a non-empty string")

        object.__setattr__(
            self,
            "holiday_calendar_refs",
            _normalize_ref_list(self.holiday_calendar_refs, "holiday_calendar_refs"),
        )
        object.__setattr__(
            self,
            "day_count_convention_refs",
            _normalize_ref_list(self.day_count_convention_refs, "day_count_convention_refs"),
        )
        object.__setattr__(
            self,
            "business_day_adjustment_refs",
            _normalize_ref_list(
                self.business_day_adjustment_refs,
                "business_day_adjustment_refs",
            ),
        )
        object.__setattr__(
            self,
            "settlement_convention_refs",
            _normalize_ref_list(self.settlement_convention_refs, "settlement_convention_refs"),
        )
        object.__setattr__(
            self,
            "fixing_source_refs",
            _normalize_ref_list(self.fixing_source_refs, "fixing_source_refs"),
        )
        object.__setattr__(
            self,
            "exercise_convention_refs",
            _normalize_ref_list(self.exercise_convention_refs, "exercise_convention_refs"),
        )
        object.__setattr__(
            self,
            "taxonomy_mapping_refs",
            _normalize_ref_list(self.taxonomy_mapping_refs, "taxonomy_mapping_refs"),
        )


__all__ = ["ReferenceDataSet"]
