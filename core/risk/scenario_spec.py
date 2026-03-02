"""Gate G9.1: ScenarioSpec v1 — deterministic shock definition contract.

Defines the canonical schema for scenario axis specifications used by the
Gate 9 risk layer. No scenario expansion logic. No pricing logic.

Rules:
- All shock lists are normalized to sorted unique order (ascending Decimal).
- Non-finite values are rejected at construction time.
- schema_version is mandatory and must equal SUPPORTED_SCHEMA_VERSION.
- Deterministic by construction: no wall-clock, no randomness.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Sequence


SUPPORTED_SCHEMA_VERSION: int = 1


def _ensure_finite_decimal(value: Decimal, field: str) -> None:
    if not value.is_finite():
        raise ValueError(f"{field} contains non-finite value: {value!r}")


def _normalize_shocks(values: Sequence[Decimal], field: str) -> tuple[Decimal, ...]:
    seen = set()
    result = []
    for v in values:
        if not isinstance(v, Decimal):
            try:
                v = Decimal(v)
            except (InvalidOperation, TypeError) as exc:
                raise ValueError(f"{field}: cannot convert {v!r} to Decimal") from exc
        _ensure_finite_decimal(v, field)
        if v not in seen:
            seen.add(v)
            result.append(v)
    return tuple(sorted(result))


@dataclass(frozen=True)
class ScenarioSpec:
    schema_version: int
    spot_shocks: tuple[Decimal, ...]
    df_domestic_shocks: tuple[Decimal, ...]
    df_foreign_shocks: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        # schema_version enforcement
        if self.schema_version is None:
            raise ValueError("schema_version is required")
        if self.schema_version != SUPPORTED_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version {self.schema_version!r};"
                f" supported: {SUPPORTED_SCHEMA_VERSION}"
            )

        # Normalize each shock list: deduplicate, sort, validate finiteness
        object.__setattr__(
            self, "spot_shocks", _normalize_shocks(self.spot_shocks, "spot_shocks")
        )
        object.__setattr__(
            self,
            "df_domestic_shocks",
            _normalize_shocks(self.df_domestic_shocks, "df_domestic_shocks"),
        )
        object.__setattr__(
            self,
            "df_foreign_shocks",
            _normalize_shocks(self.df_foreign_shocks, "df_foreign_shocks"),
        )


__all__ = ["ScenarioSpec", "SUPPORTED_SCHEMA_VERSION"]
