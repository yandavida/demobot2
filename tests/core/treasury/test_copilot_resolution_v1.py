from __future__ import annotations

import pytest

from core.risk.scenario_spec import ScenarioSpec
from core.treasury.copilot_resolution_v1 import CopilotResolutionError
from core.treasury.copilot_resolution_v1 import resolve_copilot_inputs_fx_v1
from core.treasury.copilot_resolution_v1 import resolve_policy_inputs_v1
from core.treasury.copilot_resolution_v1 import resolve_scenario_spec_v1
from treasury_copilot_v1 import CopilotContextV1
from treasury_copilot_v1 import TreasuryCopilotRequestV1
from treasury_copilot_v1 import run_treasury_copilot_v1


def test_resolve_scenario_spec_from_catalog() -> None:
    spec = resolve_scenario_spec_v1("STANDARD_7")

    assert isinstance(spec, ScenarioSpec)
    assert tuple(float(x) for x in spec.spot_shocks) == (-0.07, 0.0, 0.07)


def test_resolve_policy_inputs_from_catalog() -> None:
    policy_template, target = resolve_policy_inputs_v1("TREASURY_STANDARD_70")

    assert getattr(policy_template, "template_id") == "TREASURY_STANDARD_70"
    assert isinstance(target, float)


def test_unknown_ids_raise_hard_failures() -> None:
    with pytest.raises(Exception, match="unknown_scenario_template_id"):
        resolve_scenario_spec_v1("NOPE")

    with pytest.raises(Exception, match="unknown_policy_template_id"):
        resolve_policy_inputs_v1("NOPE")


def test_unified_resolver_wraps_portfolio_resolution_error() -> None:
    context = CopilotContextV1(
        market_snapshot_id="snap-1",
        scenario_template_id="STANDARD_7",
        policy_template_id="TREASURY_STANDARD_70",
        portfolio_ref="portfolio-1",
    )

    with pytest.raises(CopilotResolutionError, match="portfolio_resolution_failed:no_portfolio_source_registered"):
        resolve_copilot_inputs_fx_v1(context)


def test_router_fx_sufficient_context_resolution_failure_warning() -> None:
    req = TreasuryCopilotRequestV1(
        question="תעשה גידור",
        context=CopilotContextV1(
            market_snapshot_id="snap-1",
            scenario_template_id="STANDARD_7",
            policy_template_id="TREASURY_STANDARD_70",
            portfolio_ref="portfolio-1",
        ),
    )

    out = run_treasury_copilot_v1(req)

    assert out.missing_context == []
    assert out.warnings[0] == "resolution_failed_v1"
    assert out.warnings[1].startswith("resolution_error:portfolio_resolution_failed:")
