from __future__ import annotations

from dataclasses import asdict
import json
import math

from core.numeric_policy import DEFAULT_TOLERANCES
from core.numeric_policy import MetricClass
from core.services.hedge_policy_constraints_v1 import HedgePolicyV1
from core.services.hedge_policy_constraints_v1 import apply_hedge_policy_v1


def _close(a: float, b: float) -> bool:
    tol = DEFAULT_TOLERANCES[MetricClass.PNL]
    return math.isclose(a, b, rel_tol=float(tol.rel or 0.0), abs_tol=float(tol.abs or 0.0))


def _canon(obj) -> str:
    return json.dumps(asdict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_ratio_below_min_clamps_to_min() -> None:
    policy = HedgePolicyV1(
        policy_id="p-min",
        min_hedge_ratio=0.50,
        max_hedge_ratio=0.90,
        rounding_lot_notional=None,
    )
    out = apply_hedge_policy_v1(policy=policy, recommended_hedge_ratio=0.40)

    assert _close(out.output_hedge_ratio, 0.50)
    assert out.binding_constraints == ("MIN_HEDGE_RATIO",)
    assert out.unmet_target_reason is None


def test_ratio_above_max_clamps_to_max_and_sets_reason() -> None:
    policy = HedgePolicyV1(
        policy_id="p-max",
        min_hedge_ratio=0.20,
        max_hedge_ratio=0.80,
        rounding_lot_notional=None,
    )
    out = apply_hedge_policy_v1(policy=policy, recommended_hedge_ratio=0.95)

    assert _close(out.output_hedge_ratio, 0.80)
    assert out.binding_constraints == ("MAX_HEDGE_RATIO",)
    assert out.unmet_target_reason == "MAX_HEDGE_CAP"


def test_rounding_changes_ratio_and_sets_binding() -> None:
    policy = HedgePolicyV1(
        policy_id="p-round",
        min_hedge_ratio=0.0,
        max_hedge_ratio=1.0,
        rounding_lot_notional=50000.0,
    )
    out = apply_hedge_policy_v1(policy=policy, recommended_hedge_ratio=0.758795)

    assert _close(out.output_hedge_ratio, 0.76)
    assert out.binding_constraints == ("RATIO_ROUNDING",)
    assert out.notes == ("ROUNDING_STEP_RATIO_0.01",)


def test_deterministic_output_on_repeated_calls() -> None:
    policy = HedgePolicyV1(
        policy_id="p-det",
        min_hedge_ratio=0.1,
        max_hedge_ratio=0.9,
        rounding_lot_notional=50000.0,
    )
    out_a = apply_hedge_policy_v1(policy=policy, recommended_hedge_ratio=0.758795)
    out_b = apply_hedge_policy_v1(policy=policy, recommended_hedge_ratio=0.758795)

    assert _canon(out_a) == _canon(out_b)
