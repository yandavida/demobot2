"""Gate G9.4: RiskArtifact v1 (canonical artifact + contract freeze).

Packages a RiskResult into a canonical, content-addressed artifact.
No repricing semantics are changed here.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from core.risk.reprice_harness import RiskResult
from core.risk.risk_request import RiskRequest
from core.risk.risk_request import RiskValidationError
from core.risk.scenario_grid import ScenarioGrid
from core.validation.error_taxonomy import make_error


SCHEMA_NAME = "pe.g9.risk_artifact"
SCHEMA_VERSION = "1.0"
ENGINE_NAME = "pe.g9.repricing_harness"
ENGINE_VERSION = "1.0"
HASH_CANONICALIZATION = "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False)"
HASH_DECIMAL_ENCODING = "str"
HASH_SHA_SCOPE = "artifact_without_sha256"


def _reject(code: str, details: dict[str, str]) -> None:
    raise RiskValidationError(make_error(code, details))


def _canonical_sha256(obj: dict[str, Any]) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _decimal_str(value: Decimal) -> str:
    return str(value)


def build_risk_artifact_v1(
    risk_request: RiskRequest,
    scenario_grid: ScenarioGrid,
    risk_result: RiskResult,
) -> dict[str, Any]:
    if risk_result.market_snapshot_id != risk_request.market_snapshot_id:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "market_snapshot_id",
                "reason": "risk_result.market_snapshot_id must equal risk_request.market_snapshot_id",
            },
        )

    if risk_result.scenario_set_id != scenario_grid.scenario_set_id:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "scenario_set_id",
                "reason": "risk_result.scenario_set_id must equal scenario_grid.scenario_set_id",
            },
        )

    if tuple(cube.instrument_id for cube in risk_result.results) != risk_request.instrument_ids:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "results.instrument_id",
                "reason": "risk_result instrument order must equal canonical request.instrument_ids",
            },
        )

    scenario_ids = scenario_grid.scenario_ids
    scenario_totals = [Decimal("0") for _ in scenario_ids]
    base_total = Decimal("0")

    output_results: list[dict[str, Any]] = []
    for cube in risk_result.results:
        if len(cube.scenario_pvs) != len(scenario_ids):
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "scenario_pvs",
                    "reason": "len(scenario_pvs) must equal len(scenario_grid.scenario_ids)",
                },
            )

        base_total += cube.base_pv

        if not cube.scenario_pvs:
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "scenario_pvs",
                    "reason": "scenario_pvs cannot be empty",
                },
            )

        base_currency = cube.scenario_pvs[0].currency
        base_metric_class = cube.scenario_pvs[0].metric_class

        if base_currency != risk_request.valuation_context.domestic_currency:
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "currency",
                    "reason": "output currency must equal valuation_context.domestic_currency",
                },
            )

        scenario_entries: list[dict[str, str]] = []
        for idx, (expected_id, scenario_item) in enumerate(zip(scenario_ids, cube.scenario_pvs)):
            if scenario_item.scenario_id != expected_id:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "scenario_id",
                        "reason": "scenario_id alignment must match ScenarioGrid ordering",
                    },
                )
            if scenario_item.currency != base_currency:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "currency",
                        "reason": "all scenario currency values per instrument must be equal",
                    },
                )
            if scenario_item.metric_class != base_metric_class:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "metric_class",
                        "reason": "all scenario metric_class values per instrument must be equal",
                    },
                )

            scenario_totals[idx] += scenario_item.pv_domestic
            scenario_entries.append(
                {
                    "scenario_id": scenario_item.scenario_id,
                    "pv_domestic": _decimal_str(scenario_item.pv_domestic),
                }
            )

        output_results.append(
            {
                "instrument_id": cube.instrument_id,
                "base": {
                    "pv_domestic": _decimal_str(cube.base_pv),
                    "currency": base_currency,
                    "metric_class": base_metric_class,
                },
                "scenarios": scenario_entries,
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
            "schema_version": risk_request.schema_version,
            "market_snapshot_id": risk_request.market_snapshot_id,
            "scenario_set_id": scenario_grid.scenario_set_id,
            "instrument_ids": list(risk_request.instrument_ids),
            "valuation_context": {
                "as_of_ts": risk_request.valuation_context.as_of_ts.isoformat(),
                "domestic_currency": risk_request.valuation_context.domestic_currency,
            },
            "scenario_spec": {
                "schema_version": risk_request.scenario_spec.schema_version,
                "spot_shocks": [str(v) for v in risk_request.scenario_spec.spot_shocks],
                "df_domestic_shocks": [str(v) for v in risk_request.scenario_spec.df_domestic_shocks],
                "df_foreign_shocks": [str(v) for v in risk_request.scenario_spec.df_foreign_shocks],
            },
        },
        "outputs": {
            "results": output_results,
            "aggregates": {
                "base_total_pv_domestic": _decimal_str(base_total),
                "scenario_total_pv_domestic": [
                    {
                        "scenario_id": scenario_id,
                        "pv_domestic": _decimal_str(total),
                    }
                    for scenario_id, total in zip(scenario_ids, scenario_totals)
                ],
            },
        },
        "hashing": {
            "canonicalization": HASH_CANONICALIZATION,
            "decimal_encoding": HASH_DECIMAL_ENCODING,
            "sha_scope": HASH_SHA_SCOPE,
        },
    }

    artifact["sha256"] = _canonical_sha256(artifact)
    return artifact


__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "HASH_CANONICALIZATION",
    "HASH_DECIMAL_ENCODING",
    "HASH_SHA_SCOPE",
    "SCHEMA_NAME",
    "SCHEMA_VERSION",
    "build_risk_artifact_v1",
]
