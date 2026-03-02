"""Gate G9.2: ScenarioGrid v1 — deterministic scenario expansion (no pricing).

Expands a ScenarioSet spec into a full Cartesian scenario grid over:
  spot_shocks × df_domestic_shocks × df_foreign_shocks

This module is structural-only: no repricing/valuation semantics.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal

from core.risk.risk_request import RiskValidationError
from core.risk.scenario_set import ScenarioSet
from core.validation.error_taxonomy import make_error


SUPPORTED_SCHEMA_VERSION: int = 1
CANONICALIZATION_RULE: str = "json.sort_keys=True,separators=(',',':'),ensure_ascii=False"


def _reject(code: str, details: dict[str, str]) -> None:
    raise RiskValidationError(make_error(code, details))


@dataclass(frozen=True, order=True)
class ScenarioKey:
    spot_shock: Decimal
    df_domestic_shock: Decimal
    df_foreign_shock: Decimal


def _scenario_id_from_key(scenario_set_id: str, key: ScenarioKey) -> str:
    payload = {
        "scenario_set_id": scenario_set_id,
        "spot_shock": str(key.spot_shock),
        "df_domestic_shock": str(key.df_domestic_shock),
        "df_foreign_shock": str(key.df_foreign_shock),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ScenarioGrid:
    schema_version: int
    scenario_set_id: str
    canonicalization: str
    scenarios: tuple[ScenarioKey, ...]
    scenario_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version is None:
            _reject("MISSING_SCHEMA_VERSION", {"field": "schema_version"})
        if self.schema_version != SUPPORTED_SCHEMA_VERSION:
            _reject(
                "UNSUPPORTED_SCHEMA_VERSION",
                {
                    "given": str(self.schema_version),
                    "supported": str(SUPPORTED_SCHEMA_VERSION),
                },
            )
        if not self.scenario_set_id:
            _reject("VALIDATION_ERROR", {"field": "scenario_set_id", "reason": "must be non-empty"})
        if self.canonicalization != CANONICALIZATION_RULE:
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "canonicalization",
                    "reason": "must match frozen canonicalization rule",
                },
            )
        if len(self.scenarios) != len(self.scenario_ids):
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "scenario_ids",
                    "reason": "length must equal scenarios length",
                },
            )
        if len(set(self.scenario_ids)) != len(self.scenario_ids):
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "scenario_ids",
                    "reason": "scenario_ids must be unique",
                },
            )

    @classmethod
    def from_scenario_set(
        cls,
        scenario_set: ScenarioSet,
        *,
        schema_version: int = SUPPORTED_SCHEMA_VERSION,
    ) -> ScenarioGrid:
        spec = scenario_set.spec

        scenarios = [
            ScenarioKey(
                spot_shock=spot,
                df_domestic_shock=df_domestic,
                df_foreign_shock=df_foreign,
            )
            for spot in spec.spot_shocks
            for df_domestic in spec.df_domestic_shocks
            for df_foreign in spec.df_foreign_shocks
        ]

        ordered_scenarios = tuple(sorted(scenarios))
        ordered_ids = tuple(
            _scenario_id_from_key(scenario_set.scenario_set_id, key)
            for key in ordered_scenarios
        )

        expected_count = (
            len(spec.spot_shocks)
            * len(spec.df_domestic_shocks)
            * len(spec.df_foreign_shocks)
        )
        if len(ordered_scenarios) != expected_count:
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "scenarios",
                    "reason": "scenario count must equal Cartesian product size",
                },
            )

        return cls(
            schema_version=schema_version,
            scenario_set_id=scenario_set.scenario_set_id,
            canonicalization=CANONICALIZATION_RULE,
            scenarios=ordered_scenarios,
            scenario_ids=ordered_ids,
        )


__all__ = [
    "CANONICALIZATION_RULE",
    "ScenarioGrid",
    "ScenarioKey",
    "SUPPORTED_SCHEMA_VERSION",
]
