"""Gate G9.5: Exposures v1 via deterministic finite differences.

Computes spot exposure metrics from a frozen G9.4 RiskArtifact.
No repricing logic is introduced here.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any

from core.risk.risk_request import RiskValidationError
from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import ScenarioSpec
from core.validation.error_taxonomy import make_error


SCHEMA_NAME = "pe.g9.exposures_artifact"
SCHEMA_VERSION = "1.0"
ENGINE_NAME = "pe.g9.exposures_fd"
ENGINE_VERSION = "1.0"
HASH_CANONICALIZATION = "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False)"
HASH_DECIMAL_ENCODING = "str"
HASH_SHA_SCOPE = "artifact_without_sha256"

RISK_ARTIFACT_SCHEMA_NAME = "pe.g9.risk_artifact"
RISK_ARTIFACT_SCHEMA_VERSION = "1.0"


def _reject(code: str, details: dict[str, str]) -> None:
    raise RiskValidationError(make_error(code, details))


def _to_decimal(value: Any, field: str) -> Decimal:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        _reject("VALIDATION_ERROR", {"field": field, "reason": f"invalid decimal: {value!r}"})
        raise AssertionError("unreachable") from exc
    if not d.is_finite():
        _reject("VALIDATION_ERROR", {"field": field, "reason": "decimal must be finite"})
    return d


def _canonical_sha256_excluding_sha(obj: dict[str, Any]) -> str:
    payload = {k: v for k, v in obj.items() if k != "sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_scenario_spec_from_artifact(risk_artifact: dict[str, Any]) -> ScenarioSpec:
    try:
        spec_raw = risk_artifact["inputs"]["scenario_spec"]
    except Exception:
        _reject("VALIDATION_ERROR", {"field": "inputs.scenario_spec", "reason": "missing"})

    try:
        schema_version = int(spec_raw["schema_version"])
        spot_shocks = tuple(_to_decimal(v, "inputs.scenario_spec.spot_shocks") for v in spec_raw["spot_shocks"])
        df_domestic_shocks = tuple(
            _to_decimal(v, "inputs.scenario_spec.df_domestic_shocks") for v in spec_raw["df_domestic_shocks"]
        )
        df_foreign_shocks = tuple(
            _to_decimal(v, "inputs.scenario_spec.df_foreign_shocks") for v in spec_raw["df_foreign_shocks"]
        )
    except KeyError as exc:
        _reject("VALIDATION_ERROR", {"field": f"inputs.scenario_spec.{exc.args[0]}", "reason": "missing"})

    return ScenarioSpec(
        schema_version=schema_version,
        spot_shocks=spot_shocks,
        df_domestic_shocks=df_domestic_shocks,
        df_foreign_shocks=df_foreign_shocks,
    )


def _find_symmetric_h(spec: ScenarioSpec) -> Decimal:
    positives = [h for h in spec.spot_shocks if h > 0 and (-h) in spec.spot_shocks]
    positives = sorted(set(positives))
    if len(positives) != 1:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "inputs.scenario_spec.spot_shocks",
                "reason": "must contain exactly one symmetric +/-h pair",
            },
        )

    h = positives[0]
    if h <= 0:
        _reject("VALIDATION_ERROR", {"field": "h", "reason": "h must be > 0"})

    if Decimal("0") not in spec.df_domestic_shocks:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "inputs.scenario_spec.df_domestic_shocks",
                "reason": "must include 0 for exposures v1",
            },
        )
    if Decimal("0") not in spec.df_foreign_shocks:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "inputs.scenario_spec.df_foreign_shocks",
                "reason": "must include 0 for exposures v1",
            },
        )

    return h


def compute_exposures_v1(
    risk_artifact: dict,
    base_spot: Decimal,
) -> dict[str, Any]:
    if not isinstance(risk_artifact, dict):
        _reject("VALIDATION_ERROR", {"field": "risk_artifact", "reason": "must be a dict"})

    schema = risk_artifact.get("schema", {})
    if schema.get("name") != RISK_ARTIFACT_SCHEMA_NAME:
        _reject("VALIDATION_ERROR", {"field": "schema.name", "reason": "unsupported risk artifact schema"})
    if schema.get("version") != RISK_ARTIFACT_SCHEMA_VERSION:
        _reject("VALIDATION_ERROR", {"field": "schema.version", "reason": "unsupported risk artifact version"})

    base_spot_dec = _to_decimal(base_spot, "base_spot")
    if base_spot_dec <= 0:
        _reject("VALIDATION_ERROR", {"field": "base_spot", "reason": "must be > 0"})

    spec = _parse_scenario_spec_from_artifact(risk_artifact)
    h = _find_symmetric_h(spec)

    scenario_set_id = risk_artifact.get("inputs", {}).get("scenario_set_id")
    if not isinstance(scenario_set_id, str) or not scenario_set_id:
        _reject("VALIDATION_ERROR", {"field": "inputs.scenario_set_id", "reason": "missing or invalid"})

    scenario_set = ScenarioSet.from_spec(spec)
    if scenario_set.scenario_set_id != scenario_set_id:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "inputs.scenario_set_id",
                "reason": "does not match deterministic ScenarioSet(spec)",
            },
        )

    scenario_grid = ScenarioGrid.from_scenario_set(scenario_set)

    plus_id = None
    minus_id = None
    for key, sid in zip(scenario_grid.scenarios, scenario_grid.scenario_ids):
        if key.df_domestic_shock == Decimal("0") and key.df_foreign_shock == Decimal("0"):
            if key.spot_shock == h:
                plus_id = sid
            elif key.spot_shock == -h:
                minus_id = sid

    if plus_id is None or minus_id is None:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "scenario_ids",
                "reason": "missing required +/-h scenarios with df shocks == 0",
            },
        )

    results_raw = risk_artifact.get("outputs", {}).get("results")
    if not isinstance(results_raw, list) or not results_raw:
        _reject("VALIDATION_ERROR", {"field": "outputs.results", "reason": "missing or empty"})

    per_instrument_entries: list[dict[str, str]] = []
    delta_total_unit = Decimal("0")
    delta_total_pct = Decimal("0")

    for item in sorted(results_raw, key=lambda x: x.get("instrument_id", "")):
        instrument_id = item.get("instrument_id")
        if not isinstance(instrument_id, str) or not instrument_id:
            _reject("VALIDATION_ERROR", {"field": "outputs.results.instrument_id", "reason": "invalid"})

        base_block = item.get("base", {})
        currency = base_block.get("currency")
        if not isinstance(currency, str) or not currency:
            _reject("VALIDATION_ERROR", {"field": "outputs.results.base.currency", "reason": "invalid"})

        scenario_rows = item.get("scenarios")
        if not isinstance(scenario_rows, list) or not scenario_rows:
            _reject("VALIDATION_ERROR", {"field": "outputs.results.scenarios", "reason": "missing or empty"})

        by_id: dict[str, Decimal] = {}
        for row in scenario_rows:
            sid = row.get("scenario_id")
            if not isinstance(sid, str) or not sid:
                _reject("VALIDATION_ERROR", {"field": "outputs.results.scenarios.scenario_id", "reason": "invalid"})
            by_id[sid] = _to_decimal(row.get("pv_domestic"), "outputs.results.scenarios.pv_domestic")

        if plus_id not in by_id or minus_id not in by_id:
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "outputs.results.scenarios",
                    "reason": "missing scenario row for required +/-h scenario ids",
                },
            )

        pv_plus = by_id[plus_id]
        pv_minus = by_id[minus_id]
        delta_pct = (pv_plus - pv_minus) / (Decimal("2") * h)
        delta_unit = delta_pct / base_spot_dec

        delta_total_pct += delta_pct
        delta_total_unit += delta_unit

        per_instrument_entries.append(
            {
                "instrument_id": instrument_id,
                "delta_per_unit_spot": str(delta_unit),
                "delta_per_pct": str(delta_pct),
                "currency": currency,
                "metric_class": "DELTA",
            }
        )

    artifact: dict[str, Any] = {
        "schema": {
            "name": SCHEMA_NAME,
            "version": SCHEMA_VERSION,
        },
        "engine": {
            "name": ENGINE_NAME,
            "version": ENGINE_VERSION,
        },
        "inputs": {
            "risk_artifact_sha256": str(risk_artifact.get("sha256", "")),
            "base_spot": str(base_spot_dec),
            "h": str(h),
            "definition": {
                "delta_per_unit_spot": "(PV(+h)-PV(-h))/(2*h*S)",
                "delta_per_pct": "(PV(+h)-PV(-h))/(2*h)",
            },
        },
        "outputs": {
            "per_instrument": per_instrument_entries,
            "aggregates": {
                "delta_total_per_unit_spot": str(delta_total_unit),
                "delta_total_per_pct": str(delta_total_pct),
            },
        },
        "hashing": {
            "canonicalization": HASH_CANONICALIZATION,
            "decimal_encoding": HASH_DECIMAL_ENCODING,
            "sha_scope": HASH_SHA_SCOPE,
        },
    }

    artifact["sha256"] = _canonical_sha256_excluding_sha(artifact)
    return artifact


__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "HASH_CANONICALIZATION",
    "HASH_DECIMAL_ENCODING",
    "HASH_SHA_SCOPE",
    "SCHEMA_NAME",
    "SCHEMA_VERSION",
    "compute_exposures_v1",
]
