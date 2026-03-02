"""Gate G9.1: ScenarioSet — content-addressed immutable descriptor.

Constructed from a ScenarioSpec. Assigns a stable SHA256 id based on the
canonical JSON representation of the spec. No scenario expansion logic.

Hashing rule (frozen):
  canonical = json.dumps(spec_dict, sort_keys=True, separators=(",",":"), ensure_ascii=False)
  scenario_set_id = sha256(canonical.encode("utf-8")).hexdigest()

Decimal shock values are serialized as their canonical string representation
to guarantee round-trip stability.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from core.risk.scenario_spec import ScenarioSpec


def _spec_to_canonical_dict(spec: ScenarioSpec) -> dict:
    return {
        "schema_version": spec.schema_version,
        "spot_shocks": [str(v) for v in spec.spot_shocks],
        "df_domestic_shocks": [str(v) for v in spec.df_domestic_shocks],
        "df_foreign_shocks": [str(v) for v in spec.df_foreign_shocks],
    }


def _compute_scenario_set_id(spec: ScenarioSpec) -> str:
    payload = _spec_to_canonical_dict(spec)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ScenarioSet:
    scenario_set_id: str
    spec: ScenarioSpec

    @classmethod
    def from_spec(cls, spec: ScenarioSpec) -> ScenarioSet:
        """Construct a content-addressed ScenarioSet from a validated ScenarioSpec."""
        scenario_set_id = _compute_scenario_set_id(spec)
        return cls(scenario_set_id=scenario_set_id, spec=spec)


__all__ = ["ScenarioSet"]
