from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.market_data.fx_snapshot_resolver_v1 import SnapshotResolutionError
from core.market_data.fx_snapshot_resolver_v1 import resolve_fx_market_snapshot_v1
from core.portfolio.portfolio_ref_resolver_v1 import PortfolioResolutionError
from core.portfolio.portfolio_ref_resolver_v1 import resolve_portfolio_ref_to_advisory_payload_v1
from core.risk.scenario_spec import ScenarioSpec
from core.services.policy_templates_v1 import get_policy_template_v1
from core.services.scenario_templates_v1 import get_scenario_template_v1


class ScenarioResolutionError(ValueError):
    pass


class PolicyResolutionError(ValueError):
    pass


class CopilotResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class CopilotResolvedInputsV1:
    advisory_payload: object
    base_snapshot: object
    scenario_spec: object
    target_worst_loss_domestic: object | float | int
    policy_template_id: str
    scenario_template_id: str
    market_snapshot_id: str
    portfolio_ref: str


def resolve_scenario_spec_v1(scenario_template_id: str) -> ScenarioSpec:
    try:
        template = get_scenario_template_v1(scenario_template_id)
    except Exception as exc:
        raise ScenarioResolutionError(f"unknown_scenario_template_id:{scenario_template_id}") from exc

    return ScenarioSpec(
        schema_version=1,
        spot_shocks=tuple(Decimal(str(value)) for value in template.shocks_pct),
        df_domestic_shocks=(Decimal("0.0"),),
        df_foreign_shocks=(Decimal("0.0"),),
    )


def resolve_policy_inputs_v1(policy_template_id: str) -> tuple[object, float]:
    try:
        template = get_policy_template_v1(policy_template_id)
    except Exception as exc:
        raise PolicyResolutionError(f"unknown_policy_template_id:{policy_template_id}") from exc

    target = float(template.ladder_config.target_worst_loss_total_domestic)
    return template, target


def resolve_copilot_inputs_fx_v1(context) -> CopilotResolvedInputsV1:
    try:
        payload = resolve_portfolio_ref_to_advisory_payload_v1(str(context.portfolio_ref or ""))
    except PortfolioResolutionError as exc:
        raise CopilotResolutionError(f"portfolio_resolution_failed:{exc}") from exc

    try:
        base_snapshot = resolve_fx_market_snapshot_v1(str(context.market_snapshot_id or ""))
    except SnapshotResolutionError as exc:
        raise CopilotResolutionError(f"snapshot_resolution_failed:{exc}") from exc

    try:
        scenario_spec = resolve_scenario_spec_v1(str(context.scenario_template_id or ""))
    except ScenarioResolutionError as exc:
        raise CopilotResolutionError(f"scenario_resolution_failed:{exc}") from exc

    try:
        policy_template, target = resolve_policy_inputs_v1(str(context.policy_template_id or ""))
    except PolicyResolutionError as exc:
        raise CopilotResolutionError(f"policy_resolution_failed:{exc}") from exc

    return CopilotResolvedInputsV1(
        advisory_payload=payload,
        base_snapshot=base_snapshot,
        scenario_spec=scenario_spec,
        target_worst_loss_domestic=target,
        policy_template_id=str(context.policy_template_id),
        scenario_template_id=str(context.scenario_template_id),
        market_snapshot_id=str(context.market_snapshot_id),
        portfolio_ref=str(context.portfolio_ref),
    )


__all__ = [
    "CopilotResolvedInputsV1",
    "CopilotResolutionError",
    "ScenarioResolutionError",
    "PolicyResolutionError",
    "resolve_scenario_spec_v1",
    "resolve_policy_inputs_v1",
    "resolve_copilot_inputs_fx_v1",
]
