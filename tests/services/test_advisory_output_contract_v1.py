from __future__ import annotations

import pytest

from core.services.advisory_output_contract_v1 import AdvisoryDecisionV1
from core.services.hedge_recommendation_v1 import HedgeRecommendationV1
from core.services.scenario_risk_summary_v1 import ScenarioRiskSummaryV1
from core.services.scenario_risk_summary_v1 import ScenarioRowV1


def _risk_summary() -> ScenarioRiskSummaryV1:
    return ScenarioRiskSummaryV1(
        contract_version="v1",
        snapshot_id="snap-001",
        base_total_pv_domestic=1000.0,
        worst_scenario_id="scn-worst",
        worst_total_pv_domestic=700.0,
        worst_loss_domestic=-300.0,
        scenario_rows=[
            ScenarioRowV1(
                scenario_id="scn-worst",
                label="",
                total_pv_domestic=700.0,
                pnl_vs_base_domestic=-300.0,
            )
        ],
    )


def _hedge_recommendation() -> HedgeRecommendationV1:
    return HedgeRecommendationV1(
        contract_version="v1",
        current_hedge_ratio=0.6,
        target_worst_loss_domestic=200000.0,
        implied_worst_loss_unhedged_domestic=829170.0,
        recommended_hedge_ratio=0.7587954212,
        expected_worst_loss_domestic=200000.0,
    )


def _decision(**overrides) -> AdvisoryDecisionV1:
    defaults = {
        "company_id": "acme",
        "snapshot_id": "snap-001",
        "scenario_template_id": "tmpl-001",
        "risk_summary": _risk_summary(),
        "hedge_recommendation": _hedge_recommendation(),
    }
    defaults.update(overrides)
    return AdvisoryDecisionV1(**defaults)


def test_to_dict_deterministic_across_repeated_calls() -> None:
    decision = _decision(notes=("n1", "n2"))

    out_a = decision.to_dict()
    out_b = decision.to_dict()

    assert out_a == out_b
    assert list(out_a.keys()) == [
        "contract_version",
        "company_id",
        "snapshot_id",
        "scenario_template_id",
        "risk_summary",
        "hedge_recommendation",
        "delta_exposure_aggregate_domestic",
        "notes",
    ]


def test_delta_exposure_can_be_none() -> None:
    decision = _decision(delta_exposure_aggregate_domestic=None)
    out = decision.to_dict()

    assert "delta_exposure_aggregate_domestic" in out
    assert out["delta_exposure_aggregate_domestic"] is None


def test_notes_default_empty_and_immutable_style() -> None:
    decision = _decision()

    assert decision.notes == ()
    assert decision.to_dict()["notes"] == []
    with pytest.raises(AttributeError):
        decision.notes.append("x")  # type: ignore[attr-defined]


def test_validation_empty_company_raises() -> None:
    with pytest.raises(ValueError, match="company_id"):
        _decision(company_id="")


def test_snapshot_company_template_preserved() -> None:
    decision = _decision(company_id="corp-a", snapshot_id="snap-a", scenario_template_id="tmpl-a")
    out = decision.to_dict()

    assert out["company_id"] == "corp-a"
    assert out["snapshot_id"] == "snap-a"
    assert out["scenario_template_id"] == "tmpl-a"
