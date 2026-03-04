from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any

from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import ScenarioSpec


@dataclass(frozen=True)
class ScenarioRowV1:
    scenario_id: str
    label: str
    total_pv_domestic: float
    pnl_vs_base_domestic: float


@dataclass(frozen=True)
class ScenarioRiskSummaryV1:
    contract_version: str
    snapshot_id: str
    base_total_pv_domestic: float
    worst_scenario_id: str
    worst_total_pv_domestic: float
    worst_loss_domestic: float
    scenario_rows: list[ScenarioRowV1]


def _to_decimal(value: Any, *, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a valid decimal") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field} must be finite")
    return parsed


def _extract_snapshot_id(risk_artifact: dict[str, Any], portfolio_surface_artifact: dict[str, Any]) -> str:
    risk_snapshot_id = risk_artifact.get("inputs", {}).get("market_snapshot_id")
    if isinstance(risk_snapshot_id, str) and risk_snapshot_id:
        return risk_snapshot_id
    surface_snapshot_id = portfolio_surface_artifact.get("inputs", {}).get("market_snapshot_id")
    if isinstance(surface_snapshot_id, str) and surface_snapshot_id:
        return surface_snapshot_id
    return ""


def _build_label_map(risk_artifact: dict[str, Any]) -> dict[str, str]:
    spec_raw = risk_artifact.get("inputs", {}).get("scenario_spec")
    if not isinstance(spec_raw, dict):
        return {}
    try:
        scenario_spec = ScenarioSpec(
            schema_version=int(spec_raw["schema_version"]),
            spot_shocks=tuple(Decimal(v) for v in spec_raw["spot_shocks"]),
            df_domestic_shocks=tuple(Decimal(v) for v in spec_raw["df_domestic_shocks"]),
            df_foreign_shocks=tuple(Decimal(v) for v in spec_raw["df_foreign_shocks"]),
        )
    except Exception:
        return {}

    grid = ScenarioGrid.from_scenario_set(ScenarioSet.from_spec(scenario_spec))
    return {
        scenario_id: (
            f"spot_shock={scenario_key.spot_shock:+.2%},"
            f"df_domestic_shock={scenario_key.df_domestic_shock:+.2%},"
            f"df_foreign_shock={scenario_key.df_foreign_shock:+.2%}"
        )
        for scenario_key, scenario_id in zip(grid.scenarios, grid.scenario_ids)
    }


def summarize_scenario_risk_v1(
    risk_artifact,
    portfolio_surface_artifact,
) -> ScenarioRiskSummaryV1:
    if not isinstance(risk_artifact, dict):
        raise ValueError("risk_artifact must be dict")
    if not isinstance(portfolio_surface_artifact, dict):
        raise ValueError("portfolio_surface_artifact must be dict")

    base_total = _to_decimal(
        risk_artifact.get("outputs", {}).get("aggregates", {}).get("base_total_pv_domestic"),
        field="risk_artifact.outputs.aggregates.base_total_pv_domestic",
    )
    scenario_totals = risk_artifact.get("outputs", {}).get("aggregates", {}).get("scenario_total_pv_domestic")
    if not isinstance(scenario_totals, list) or not scenario_totals:
        raise ValueError("risk_artifact.outputs.aggregates.scenario_total_pv_domestic must be a non-empty list")

    ranking = portfolio_surface_artifact.get("outputs", {}).get("ranking_worst_to_best")
    if not isinstance(ranking, list) or not ranking:
        raise ValueError("portfolio_surface_artifact.outputs.ranking_worst_to_best must be a non-empty list")

    label_map = _build_label_map(risk_artifact)

    rows: list[tuple[Decimal, str, ScenarioRowV1]] = []
    totals_by_scenario: dict[str, Decimal] = {}
    for row in scenario_totals:
        scenario_id = row.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id:
            raise ValueError("scenario_total_pv_domestic.scenario_id must be non-empty string")
        total = _to_decimal(row.get("pv_domestic"), field=f"scenario_total_pv_domestic[{scenario_id}].pv_domestic")
        pnl = total - base_total
        totals_by_scenario[scenario_id] = total
        rows.append(
            (
                pnl,
                scenario_id,
                ScenarioRowV1(
                    scenario_id=scenario_id,
                    label=label_map.get(scenario_id, ""),
                    total_pv_domestic=float(total),
                    pnl_vs_base_domestic=float(pnl),
                ),
            )
        )

    rows_sorted = [item[2] for item in sorted(rows, key=lambda t: (t[0], t[1]))]

    top_rank = min(
        ranking,
        key=lambda item: (
            int(item.get("rank", 10**12)),
            str(item.get("scenario_id", "")),
        ),
    )
    worst_scenario_id = str(top_rank.get("scenario_id", ""))
    if worst_scenario_id not in totals_by_scenario:
        raise ValueError("worst scenario from portfolio_surface_artifact not found in risk_artifact scenario totals")

    worst_total = totals_by_scenario[worst_scenario_id]
    worst_loss = worst_total - base_total

    return ScenarioRiskSummaryV1(
        contract_version="v1",
        snapshot_id=_extract_snapshot_id(risk_artifact, portfolio_surface_artifact),
        base_total_pv_domestic=float(base_total),
        worst_scenario_id=worst_scenario_id,
        worst_total_pv_domestic=float(worst_total),
        worst_loss_domestic=float(worst_loss),
        scenario_rows=rows_sorted,
    )


__all__ = [
    "ScenarioRiskSummaryV1",
    "ScenarioRowV1",
    "summarize_scenario_risk_v1",
]
