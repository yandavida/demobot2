from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CounterpartyLimitV1:
    counterparty_id: str
    max_additional_notional_foreign: float | None = None
    max_total_hedge_notional_foreign: float | None = None
    max_hedge_ratio: float | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.counterparty_id, str) or not self.counterparty_id.strip():
            raise ValueError("counterparty_id must be non-empty")

        for field_name, value in (
            ("max_additional_notional_foreign", self.max_additional_notional_foreign),
            ("max_total_hedge_notional_foreign", self.max_total_hedge_notional_foreign),
        ):
            if value is None:
                continue
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{field_name} must be >= 0 when provided")

        if self.max_hedge_ratio is not None:
            if not math.isfinite(self.max_hedge_ratio):
                raise ValueError("max_hedge_ratio must be finite when provided")
            if not (0.0 <= self.max_hedge_ratio <= 1.0):
                raise ValueError("max_hedge_ratio must be in [0,1] when provided")

    def to_dict(self) -> dict[str, object]:
        return {
            "counterparty_id": self.counterparty_id,
            "max_additional_notional_foreign": self.max_additional_notional_foreign,
            "max_total_hedge_notional_foreign": self.max_total_hedge_notional_foreign,
            "max_hedge_ratio": self.max_hedge_ratio,
            "currency": self.currency,
        }


@dataclass(frozen=True)
class LimitApplicationResultV1:
    requested_additional_notional_foreign: float
    allowed_additional_notional_foreign: float
    requested_total_hedge_notional_foreign: float
    allowed_total_hedge_notional_foreign: float
    requested_post_policy_ratio: float
    allowed_post_policy_ratio: float
    binding_constraints: tuple[str, ...]
    unmet_target_reason: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_additional_notional_foreign": self.requested_additional_notional_foreign,
            "allowed_additional_notional_foreign": self.allowed_additional_notional_foreign,
            "requested_total_hedge_notional_foreign": self.requested_total_hedge_notional_foreign,
            "allowed_total_hedge_notional_foreign": self.allowed_total_hedge_notional_foreign,
            "requested_post_policy_ratio": self.requested_post_policy_ratio,
            "allowed_post_policy_ratio": self.allowed_post_policy_ratio,
            "binding_constraints": list(self.binding_constraints),
            "unmet_target_reason": self.unmet_target_reason,
        }


def _validate_finite_non_negative(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and >= 0")


def apply_counterparty_limits_v1(
    *,
    limit: CounterpartyLimitV1,
    net_exposure_abs_foreign: float,
    current_hedge_notional_foreign: float,
    requested_post_policy_ratio: float,
) -> LimitApplicationResultV1:
    if not isinstance(limit, CounterpartyLimitV1):
        raise ValueError("limit must be CounterpartyLimitV1")

    _validate_finite_non_negative("net_exposure_abs_foreign", net_exposure_abs_foreign)
    _validate_finite_non_negative("current_hedge_notional_foreign", current_hedge_notional_foreign)
    _validate_finite_non_negative("requested_post_policy_ratio", requested_post_policy_ratio)

    if net_exposure_abs_foreign == 0.0:
        return LimitApplicationResultV1(
            requested_additional_notional_foreign=0.0,
            allowed_additional_notional_foreign=0.0,
            requested_total_hedge_notional_foreign=0.0,
            allowed_total_hedge_notional_foreign=0.0,
            requested_post_policy_ratio=requested_post_policy_ratio,
            allowed_post_policy_ratio=0.0,
            binding_constraints=(),
            unmet_target_reason=None,
        )

    requested_total = net_exposure_abs_foreign * requested_post_policy_ratio
    requested_additional = max(0.0, requested_total - current_hedge_notional_foreign)

    allowed_total = requested_total
    allowed_additional = requested_additional
    allowed_ratio = requested_post_policy_ratio

    bindings: list[str] = []

    ratio_bound = False
    total_bound = False
    additional_bound = False

    if limit.max_hedge_ratio is not None:
        capped_ratio = min(allowed_ratio, limit.max_hedge_ratio)
        if capped_ratio < allowed_ratio:
            bindings.append("COUNTERPARTY_MAX_HEDGE_RATIO")
            ratio_bound = True
        allowed_ratio = capped_ratio
        allowed_total = net_exposure_abs_foreign * allowed_ratio
        allowed_additional = max(0.0, allowed_total - current_hedge_notional_foreign)

    if limit.max_total_hedge_notional_foreign is not None:
        capped_total = min(allowed_total, limit.max_total_hedge_notional_foreign)
        if capped_total < allowed_total:
            bindings.append("COUNTERPARTY_MAX_TOTAL_NOTIONAL")
            total_bound = True
        allowed_total = capped_total
        allowed_additional = max(0.0, allowed_total - current_hedge_notional_foreign)
        allowed_ratio = allowed_total / net_exposure_abs_foreign

    if limit.max_additional_notional_foreign is not None:
        capped_additional = min(allowed_additional, limit.max_additional_notional_foreign)
        if capped_additional < allowed_additional:
            bindings.append("COUNTERPARTY_MAX_ADDITIONAL_NOTIONAL")
            additional_bound = True
        allowed_additional = capped_additional
        allowed_total = current_hedge_notional_foreign + allowed_additional
        allowed_ratio = allowed_total / net_exposure_abs_foreign

    unmet_target_reason: str | None = None
    if bindings and allowed_ratio < requested_post_policy_ratio:
        if total_bound:
            unmet_target_reason = "COUNTERPARTY_MAX_TOTAL_CAP"
        elif additional_bound:
            unmet_target_reason = "COUNTERPARTY_MAX_ADD_CAP"
        elif ratio_bound:
            unmet_target_reason = "COUNTERPARTY_MAX_RATIO_CAP"

    return LimitApplicationResultV1(
        requested_additional_notional_foreign=requested_additional,
        allowed_additional_notional_foreign=allowed_additional,
        requested_total_hedge_notional_foreign=requested_total,
        allowed_total_hedge_notional_foreign=allowed_total,
        requested_post_policy_ratio=requested_post_policy_ratio,
        allowed_post_policy_ratio=allowed_ratio,
        binding_constraints=tuple(bindings),
        unmet_target_reason=unmet_target_reason,
    )


def derive_trade_action_v1(net_exposure_foreign: float, ccy: str) -> str:
    if not math.isfinite(net_exposure_foreign):
        raise ValueError("net_exposure_foreign must be finite")
    if not isinstance(ccy, str) or not ccy.strip():
        raise ValueError("ccy must be non-empty")
    if net_exposure_foreign > 0:
        return f"SELL {ccy} FWD"
    if net_exposure_foreign < 0:
        return f"BUY {ccy} FWD"
    return "NO TRADE (NATURAL HEDGE)"


__all__ = [
    "CounterpartyLimitV1",
    "LimitApplicationResultV1",
    "apply_counterparty_limits_v1",
    "derive_trade_action_v1",
]
