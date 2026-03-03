"""Gate G9.6: Portfolio Risk Surface v1 (aggregation + ranking, hash-locked).

Derived strictly from frozen G9.4 RiskArtifact.
No repricing, no VaR/ES, no strategy logic.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any

from core.risk.risk_request import RiskValidationError
from core.validation.error_taxonomy import make_error


SCHEMA_NAME = "pe.g9.portfolio_surface_artifact"
SCHEMA_VERSION = "1.0"
ENGINE_NAME = "pe.g9.portfolio_surface"
ENGINE_VERSION = "1.0"

RISK_SCHEMA_NAME = "pe.g9.risk_artifact"
RISK_SCHEMA_VERSION = "1.0"

HASH_CANONICALIZATION = "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False)"
HASH_DECIMAL_ENCODING = "str"
HASH_SHA_SCOPE = "artifact_without_sha256"


def _reject(code: str, details: dict[str, str]) -> None:
    raise RiskValidationError(make_error(code, details))


def _to_decimal(value: Any, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        _reject("VALIDATION_ERROR", {"field": field, "reason": f"invalid decimal: {value!r}"})
        raise AssertionError("unreachable") from exc
    if not parsed.is_finite():
        _reject("VALIDATION_ERROR", {"field": field, "reason": "must be finite"})
    return parsed


def _canonical_sha256_excluding_sha(artifact: dict[str, Any]) -> str:
    payload = {k: v for k, v in artifact.items() if k != "sha256"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_portfolio_surface_v1(risk_artifact: dict) -> dict[str, Any]:
    if not isinstance(risk_artifact, dict):
        _reject("VALIDATION_ERROR", {"field": "risk_artifact", "reason": "must be dict"})

    schema = risk_artifact.get("schema", {})
    if schema.get("name") != RISK_SCHEMA_NAME:
        _reject("VALIDATION_ERROR", {"field": "schema.name", "reason": "unsupported risk artifact schema"})
    if schema.get("version") != RISK_SCHEMA_VERSION:
        _reject("VALIDATION_ERROR", {"field": "schema.version", "reason": "unsupported risk artifact version"})

    inputs = risk_artifact.get("inputs", {})
    outputs = risk_artifact.get("outputs", {})
    aggregates = outputs.get("aggregates", {})

    market_snapshot_id = inputs.get("market_snapshot_id")
    scenario_set_id = inputs.get("scenario_set_id")
    instrument_ids = inputs.get("instrument_ids")

    if not isinstance(market_snapshot_id, str) or not market_snapshot_id:
        _reject("VALIDATION_ERROR", {"field": "inputs.market_snapshot_id", "reason": "missing or invalid"})
    if not isinstance(scenario_set_id, str) or not scenario_set_id:
        _reject("VALIDATION_ERROR", {"field": "inputs.scenario_set_id", "reason": "missing or invalid"})
    if not isinstance(instrument_ids, list):
        _reject("VALIDATION_ERROR", {"field": "inputs.instrument_ids", "reason": "missing or invalid"})

    base_total = _to_decimal(aggregates.get("base_total_pv_domestic"), "outputs.aggregates.base_total_pv_domestic")
    scenario_totals_raw = aggregates.get("scenario_total_pv_domestic")
    if not isinstance(scenario_totals_raw, list) or not scenario_totals_raw:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "outputs.aggregates.scenario_total_pv_domestic",
                "reason": "missing or empty",
            },
        )

    seen_ids: set[str] = set()
    ordered_scenarios: list[dict[str, str]] = []
    ranking_rows: list[tuple[Decimal, str, Decimal]] = []

    for row in scenario_totals_raw:
        scenario_id = row.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id:
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "outputs.aggregates.scenario_total_pv_domestic.scenario_id",
                    "reason": "missing or invalid",
                },
            )
        if scenario_id in seen_ids:
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "outputs.aggregates.scenario_total_pv_domestic",
                    "reason": "scenario_id must be unique",
                },
            )
        seen_ids.add(scenario_id)

        total_pv = _to_decimal(row.get("pv_domestic"), "outputs.aggregates.scenario_total_pv_domestic.pv_domestic")
        loss = total_pv - base_total

        ordered_scenarios.append(
            {
                "scenario_id": scenario_id,
                "total_pv_domestic": str(total_pv),
                "loss_vs_base_domestic": str(loss),
            }
        )
        ranking_rows.append((loss, scenario_id, total_pv))

    ranking_rows_sorted = sorted(ranking_rows, key=lambda t: (t[0], t[1]))
    ranking = [
        {
            "scenario_id": scenario_id,
            "total_pv_domestic": str(total_pv),
            "loss_vs_base_domestic": str(loss),
            "rank": idx,
        }
        for idx, (loss, scenario_id, total_pv) in enumerate(ranking_rows_sorted, start=1)
    ]

    artifact: dict[str, Any] = {
        "schema": {"name": SCHEMA_NAME, "version": SCHEMA_VERSION},
        "engine": {"name": ENGINE_NAME, "version": ENGINE_VERSION},
        "inputs": {
            "risk_artifact_sha256": str(risk_artifact.get("sha256", "")),
            "market_snapshot_id": market_snapshot_id,
            "scenario_set_id": scenario_set_id,
            "instrument_ids": sorted(str(x) for x in instrument_ids),
        },
        "outputs": {
            "base_total_pv_domestic": str(base_total),
            "scenarios": ordered_scenarios,
            "ranking_worst_to_best": ranking,
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
    "compute_portfolio_surface_v1",
]
