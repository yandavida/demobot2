from __future__ import annotations

from core.services.advisory_output_contract_v1 import AdvisoryDecisionV1
from core.services.counterparty_limits_v1 import LimitApplicationResultV1
from core.services.explainability_pack_v1 import build_explainability_pack_v1
from core.services.hedge_policy_constraints_v1 import PolicyApplicationResultV1
from core.services.hedge_recommendation_v1 import HedgeRecommendationV1
from core.services.rolling_hedge_ladder_v1 import BucketRowV1
from core.services.rolling_hedge_ladder_v1 import LadderTotalsV1
from core.services.rolling_hedge_ladder_v1 import RollingHedgeLadderResultV1
from core.services.scenario_risk_summary_v1 import ScenarioRiskSummaryV1
from core.services.scenario_risk_summary_v1 import ScenarioRowV1


def _risk_summary() -> ScenarioRiskSummaryV1:
    return ScenarioRiskSummaryV1(
        contract_version="v1",
        snapshot_id="snap-1",
        base_total_pv_domestic=1000000.0,
        worst_scenario_id="s_worst",
        worst_total_pv_domestic=850000.0,
        worst_loss_domestic=-150000.0,
        scenario_rows=[
            ScenarioRowV1(
                scenario_id="s_worst",
                label="spot_shock=+7.00%,df_domestic_shock=+0.00%,df_foreign_shock=+0.00%",
                total_pv_domestic=850000.0,
                pnl_vs_base_domestic=-150000.0,
            ),
            ScenarioRowV1(
                scenario_id="s_base",
                label="spot_shock=+0.00%,df_domestic_shock=+0.00%,df_foreign_shock=+0.00%",
                total_pv_domestic=1000000.0,
                pnl_vs_base_domestic=0.0,
            ),
        ],
    )


def _decision() -> AdvisoryDecisionV1:
    risk = _risk_summary()
    return AdvisoryDecisionV1(
        company_id="treasury-demo",
        snapshot_id="snap-1",
        scenario_template_id="usdils_spot_pm7",
        risk_summary=risk,
        hedge_recommendation=HedgeRecommendationV1(
            contract_version="v1",
            current_hedge_ratio=0.35,
            target_worst_loss_domestic=100000.0,
            implied_worst_loss_unhedged_domestic=200000.0,
            recommended_hedge_ratio=0.70,
            expected_worst_loss_domestic=100000.0,
        ),
        delta_exposure_aggregate_domestic=12345.67,
        notes=("MAX_HEDGE_RATIO",),
    )


def _ladder() -> RollingHedgeLadderResultV1:
    risk = _risk_summary()
    b1 = BucketRowV1(
        bucket_label="0-30",
        bucket_day_max=30,
        exposures_count=2,
        current_hedge_ratio_effective=0.30,
        risk_summary=risk,
        hedge_recommendation=HedgeRecommendationV1(
            contract_version="v1",
            current_hedge_ratio=0.30,
            target_worst_loss_domestic=60000.0,
            implied_worst_loss_unhedged_domestic=100000.0,
            recommended_hedge_ratio=0.60,
            expected_worst_loss_domestic=60000.0,
        ),
        policy_result=PolicyApplicationResultV1(
            contract_version="v1",
            policy_id="p1",
            input_recommended_hedge_ratio=0.62,
            output_hedge_ratio=0.60,
            binding_constraints=("MAX_HEDGE_RATIO",),
            unmet_target_reason="MAX_HEDGE_CAP",
            notes=(),
        ),
        recommended_forward_notional=300000.0,
    )
    b2 = BucketRowV1(
        bucket_label="31-60",
        bucket_day_max=60,
        exposures_count=1,
        current_hedge_ratio_effective=0.20,
        risk_summary=risk,
        hedge_recommendation=HedgeRecommendationV1(
            contract_version="v1",
            current_hedge_ratio=0.20,
            target_worst_loss_domestic=40000.0,
            implied_worst_loss_unhedged_domestic=80000.0,
            recommended_hedge_ratio=0.50,
            expected_worst_loss_domestic=40000.0,
        ),
        policy_result=None,
        recommended_forward_notional=200000.0,
    )
    return RollingHedgeLadderResultV1(
        contract_version="v1",
        company_id="treasury-demo",
        snapshot_id="snap-1",
        scenario_template_id="usdils_spot_pm7",
        buckets=(b1, b2),
        totals=LadderTotalsV1(
            total_exposures=3,
            total_recommended_forward_notional=500000.0,
            total_expected_worst_loss_domestic=100000.0,
        ),
        notes=(),
    )


def _limit_result() -> LimitApplicationResultV1:
    return LimitApplicationResultV1(
        requested_additional_notional_foreign=500000.0,
        allowed_additional_notional_foreign=300000.0,
        requested_total_hedge_notional_foreign=700000.0,
        allowed_total_hedge_notional_foreign=500000.0,
        requested_post_policy_ratio=0.70,
        allowed_post_policy_ratio=0.50,
        binding_constraints=("COUNTERPARTY_MAX_TOTAL_NOTIONAL",),
        unmet_target_reason="COUNTERPARTY_MAX_TOTAL_CAP",
    )


def test_pack_determinism() -> None:
    pack1 = build_explainability_pack_v1(
        decision=_decision(),
        risk_summary=_risk_summary(),
        ladder=_ladder(),
        limit_result=_limit_result(),
    )
    pack2 = build_explainability_pack_v1(
        decision=_decision(),
        risk_summary=_risk_summary(),
        ladder=_ladder(),
        limit_result=_limit_result(),
    )

    assert pack1.to_dict() == pack2.to_dict()


def test_item_order_and_codes() -> None:
    pack = build_explainability_pack_v1(
        decision=_decision(),
        risk_summary=_risk_summary(),
        ladder=_ladder(),
        limit_result=_limit_result(),
    )

    assert [item.code for item in pack.items] == [
        "TAIL_RISK",
        "OBJECTIVE",
        "COVERAGE_UPLIFT",
        "POLICY_BINDINGS",
        "LIMIT_BINDINGS",
        "DELTA_UNITS",
        "LADDER_DETAIL",
    ]


def test_summary_line_contains_key_facts() -> None:
    pack = build_explainability_pack_v1(
        decision=_decision(),
        risk_summary=_risk_summary(),
        ladder=_ladder(),
        limit_result=_limit_result(),
    )

    assert "→" in pack.summary_line
    assert "tail=" in pack.summary_line
    assert "bindings=" in pack.summary_line


def test_no_ladder_behavior() -> None:
    pack = build_explainability_pack_v1(
        decision=_decision(),
        risk_summary=_risk_summary(),
        ladder=None,
        limit_result=None,
    )

    codes = [item.code for item in pack.items]
    assert "OBJECTIVE" in codes
    assert "LADDER_DETAIL" not in codes

    objective = next(item for item in pack.items if item.code == "OBJECTIVE")
    assert objective.data["target_worst_loss_total_domestic"] == "N/A"


def test_delta_units_item_present() -> None:
    pack = build_explainability_pack_v1(
        decision=_decision(),
        risk_summary=_risk_summary(),
        ladder=None,
        limit_result=None,
    )

    delta_item = next(item for item in pack.items if item.code == "DELTA_UNITS")
    assert "per 1%" in delta_item.message
