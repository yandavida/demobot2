from __future__ import annotations

from dataclasses import asdict
import json

import pytest

from core.services.hedge_recommendation_v1 import recommend_hedge_ratio_v1
from core.services.scenario_risk_summary_v1 import ScenarioRiskSummaryV1
from core.services.scenario_risk_summary_v1 import ScenarioRowV1


def _summary() -> ScenarioRiskSummaryV1:
    return ScenarioRiskSummaryV1(
        contract_version="v1",
        snapshot_id="snap-001",
        base_total_pv_domestic=0.0,
        worst_scenario_id="scn_worst",
        worst_total_pv_domestic=-331668.0,
        worst_loss_domestic=-331668.0,
        scenario_rows=[
            ScenarioRowV1(
                scenario_id="scn_worst",
                label="",
                total_pv_domestic=-331668.0,
                pnl_vs_base_domestic=-331668.0,
            )
        ],
    )


def _canon(obj) -> str:
    return json.dumps(asdict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_target_200k_computes_expected_ratio_precisely() -> None:
    out = recommend_hedge_ratio_v1(
        _summary(),
        current_hedge_ratio=0.60,
        target_worst_loss_domestic=200000.0,
    )

    assert out.contract_version == "v1"
    assert out.implied_worst_loss_unhedged_domestic == pytest.approx(829170.0)
    assert out.recommended_hedge_ratio == pytest.approx(0.7587954212061698)
    assert out.expected_worst_loss_domestic == pytest.approx(200000.0)


def test_target_at_or_above_current_loss_keeps_current_ratio() -> None:
    out = recommend_hedge_ratio_v1(
        _summary(),
        current_hedge_ratio=0.60,
        target_worst_loss_domestic=400000.0,
    )

    assert out.recommended_hedge_ratio == pytest.approx(0.60)
    assert out.expected_worst_loss_domestic == pytest.approx(331668.0)


def test_target_very_small_clamps_to_full_hedge() -> None:
    out = recommend_hedge_ratio_v1(
        _summary(),
        current_hedge_ratio=0.60,
        target_worst_loss_domestic=0.0,
    )

    assert out.recommended_hedge_ratio == pytest.approx(1.0)
    assert out.expected_worst_loss_domestic == pytest.approx(0.0)


def test_current_hedge_already_full_stays_full() -> None:
    out = recommend_hedge_ratio_v1(
        _summary(),
        current_hedge_ratio=1.0,
        target_worst_loss_domestic=200000.0,
    )

    assert out.recommended_hedge_ratio == pytest.approx(1.0)
    assert out.expected_worst_loss_domestic == pytest.approx(0.0)


def test_deterministic_stable_output_dict() -> None:
    out_a = recommend_hedge_ratio_v1(
        _summary(),
        current_hedge_ratio=0.60,
        target_worst_loss_domestic=200000.0,
    )
    out_b = recommend_hedge_ratio_v1(
        _summary(),
        current_hedge_ratio=0.60,
        target_worst_loss_domestic=200000.0,
    )

    assert _canon(out_a) == _canon(out_b)
