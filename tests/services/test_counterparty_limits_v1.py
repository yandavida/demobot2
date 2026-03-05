from __future__ import annotations

import json

from core.services.counterparty_limits_v1 import CounterpartyLimitV1
from core.services.counterparty_limits_v1 import apply_counterparty_limits_v1


def test_no_limits_no_change() -> None:
    limit = CounterpartyLimitV1(counterparty_id="cp-a")

    out = apply_counterparty_limits_v1(
        limit=limit,
        net_exposure_abs_foreign=1_000_000.0,
        current_hedge_notional_foreign=200_000.0,
        requested_post_policy_ratio=0.70,
    )

    assert out.requested_total_hedge_notional_foreign == 700_000.0
    assert out.allowed_total_hedge_notional_foreign == 700_000.0
    assert out.requested_additional_notional_foreign == 500_000.0
    assert out.allowed_additional_notional_foreign == 500_000.0
    assert out.allowed_post_policy_ratio == 0.70
    assert out.binding_constraints == ()
    assert out.unmet_target_reason is None


def test_max_total_cap_binds() -> None:
    limit = CounterpartyLimitV1(
        counterparty_id="cp-a",
        max_total_hedge_notional_foreign=600_000.0,
    )

    out = apply_counterparty_limits_v1(
        limit=limit,
        net_exposure_abs_foreign=1_000_000.0,
        current_hedge_notional_foreign=200_000.0,
        requested_post_policy_ratio=0.80,
    )

    assert out.allowed_total_hedge_notional_foreign == 600_000.0
    assert out.allowed_additional_notional_foreign == 400_000.0
    assert "COUNTERPARTY_MAX_TOTAL_NOTIONAL" in out.binding_constraints
    assert out.unmet_target_reason == "COUNTERPARTY_MAX_TOTAL_CAP"


def test_max_additional_cap_binds() -> None:
    limit = CounterpartyLimitV1(
        counterparty_id="cp-a",
        max_additional_notional_foreign=150_000.0,
    )

    out = apply_counterparty_limits_v1(
        limit=limit,
        net_exposure_abs_foreign=1_000_000.0,
        current_hedge_notional_foreign=200_000.0,
        requested_post_policy_ratio=0.60,
    )

    assert out.requested_additional_notional_foreign == 400_000.0
    assert out.allowed_additional_notional_foreign == 150_000.0
    assert "COUNTERPARTY_MAX_ADDITIONAL_NOTIONAL" in out.binding_constraints
    assert out.unmet_target_reason == "COUNTERPARTY_MAX_ADD_CAP"


def test_max_ratio_cap_binds() -> None:
    limit = CounterpartyLimitV1(
        counterparty_id="cp-a",
        max_hedge_ratio=0.50,
    )

    out = apply_counterparty_limits_v1(
        limit=limit,
        net_exposure_abs_foreign=1_000_000.0,
        current_hedge_notional_foreign=100_000.0,
        requested_post_policy_ratio=0.80,
    )

    assert out.allowed_post_policy_ratio == 0.50
    assert out.allowed_total_hedge_notional_foreign == 500_000.0
    assert out.binding_constraints == ("COUNTERPARTY_MAX_HEDGE_RATIO",)
    assert out.unmet_target_reason == "COUNTERPARTY_MAX_RATIO_CAP"


def test_binding_order_stable() -> None:
    limit = CounterpartyLimitV1(
        counterparty_id="cp-a",
        max_hedge_ratio=0.90,
        max_total_hedge_notional_foreign=800_000.0,
        max_additional_notional_foreign=200_000.0,
    )

    out = apply_counterparty_limits_v1(
        limit=limit,
        net_exposure_abs_foreign=1_000_000.0,
        current_hedge_notional_foreign=500_000.0,
        requested_post_policy_ratio=1.20,
    )

    assert out.binding_constraints == (
        "COUNTERPARTY_MAX_HEDGE_RATIO",
        "COUNTERPARTY_MAX_TOTAL_NOTIONAL",
        "COUNTERPARTY_MAX_ADDITIONAL_NOTIONAL",
    )
    assert out.unmet_target_reason == "COUNTERPARTY_MAX_TOTAL_CAP"


def test_zero_exposure() -> None:
    limit = CounterpartyLimitV1(
        counterparty_id="cp-a",
        max_hedge_ratio=0.50,
        max_total_hedge_notional_foreign=1.0,
        max_additional_notional_foreign=1.0,
    )

    out = apply_counterparty_limits_v1(
        limit=limit,
        net_exposure_abs_foreign=0.0,
        current_hedge_notional_foreign=500_000.0,
        requested_post_policy_ratio=0.80,
    )

    assert out.requested_total_hedge_notional_foreign == 0.0
    assert out.allowed_total_hedge_notional_foreign == 0.0
    assert out.requested_additional_notional_foreign == 0.0
    assert out.allowed_additional_notional_foreign == 0.0
    assert out.allowed_post_policy_ratio == 0.0
    assert out.binding_constraints == ()
    assert out.unmet_target_reason is None


def test_to_dict_is_deterministic() -> None:
    limit = CounterpartyLimitV1(
        counterparty_id="cp-a",
        max_hedge_ratio=0.70,
        max_total_hedge_notional_foreign=700_000.0,
        max_additional_notional_foreign=300_000.0,
        currency="USD",
    )

    out_a = apply_counterparty_limits_v1(
        limit=limit,
        net_exposure_abs_foreign=1_000_000.0,
        current_hedge_notional_foreign=200_000.0,
        requested_post_policy_ratio=0.90,
    )
    out_b = apply_counterparty_limits_v1(
        limit=limit,
        net_exposure_abs_foreign=1_000_000.0,
        current_hedge_notional_foreign=200_000.0,
        requested_post_policy_ratio=0.90,
    )

    json_a = json.dumps(out_a.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    json_b = json.dumps(out_b.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    assert out_a.to_dict() == out_b.to_dict()
    assert json_a == json_b
