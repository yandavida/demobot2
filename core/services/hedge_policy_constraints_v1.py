from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

from core.numeric_policy import DEFAULT_TOLERANCES
from core.numeric_policy import MetricClass


@dataclass(frozen=True)
class HedgePolicyV1:
    contract_version: Literal["v1"] = "v1"
    policy_id: str = ""
    min_hedge_ratio: float = 0.0
    max_hedge_ratio: float = 1.0
    rounding_lot_notional: float | None = None
    allow_overhedge: bool = False

    def __post_init__(self) -> None:
        if self.contract_version != "v1":
            raise ValueError("contract_version must be v1")
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise ValueError("policy_id must be non-empty")
        if not math.isfinite(self.min_hedge_ratio) or not math.isfinite(self.max_hedge_ratio):
            raise ValueError("min_hedge_ratio and max_hedge_ratio must be finite")
        if not (0.0 <= self.min_hedge_ratio <= 1.0):
            raise ValueError("min_hedge_ratio must be in [0,1]")
        if self.max_hedge_ratio < self.min_hedge_ratio:
            raise ValueError("max_hedge_ratio must be >= min_hedge_ratio")
        if self.rounding_lot_notional is not None:
            if not math.isfinite(self.rounding_lot_notional) or self.rounding_lot_notional <= 0:
                raise ValueError("rounding_lot_notional must be positive when provided")


@dataclass(frozen=True)
class PolicyApplicationResultV1:
    contract_version: Literal["v1"]
    policy_id: str
    input_recommended_hedge_ratio: float
    output_hedge_ratio: float
    binding_constraints: tuple[str, ...]
    unmet_target_reason: str | None
    notes: tuple[str, ...]


def _pnl_tolerances() -> tuple[float, float]:
    tol = DEFAULT_TOLERANCES[MetricClass.PNL]
    return float(tol.abs or 0.0), float(tol.rel or 0.0)


def _rounding_step_ratio() -> float:
    abs_tol, rel_tol = _pnl_tolerances()
    base = max(abs_tol, rel_tol)
    return max(0.01, round(base, 2))


def _is_close(a: float, b: float) -> bool:
    abs_tol, rel_tol = _pnl_tolerances()
    return math.isclose(a, b, abs_tol=abs_tol, rel_tol=rel_tol)


def _clamp(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def apply_hedge_policy_v1(
    *,
    policy: HedgePolicyV1,
    recommended_hedge_ratio: float,
) -> PolicyApplicationResultV1:
    if not isinstance(policy, HedgePolicyV1):
        raise ValueError("policy must be HedgePolicyV1")
    if not math.isfinite(recommended_hedge_ratio):
        raise ValueError("recommended_hedge_ratio must be finite")

    input_ratio = float(recommended_hedge_ratio)

    effective_max = policy.max_hedge_ratio
    if not policy.allow_overhedge:
        effective_max = min(effective_max, 1.0)

    binding: list[str] = []

    clamped = _clamp(input_ratio, policy.min_hedge_ratio, effective_max)
    if clamped < input_ratio and not _is_close(clamped, input_ratio):
        binding.append("MAX_HEDGE_RATIO")
    if clamped > input_ratio and not _is_close(clamped, input_ratio):
        binding.append("MIN_HEDGE_RATIO")

    output_ratio = clamped
    if policy.rounding_lot_notional is not None:
        step = _rounding_step_ratio()
        rounded = round(output_ratio / step) * step
        rounded = _clamp(rounded, policy.min_hedge_ratio, effective_max)
        rounded = round(rounded, 2)
        if not _is_close(rounded, output_ratio):
            binding.append("RATIO_ROUNDING")
        output_ratio = rounded

    unmet_target_reason = None
    if "MAX_HEDGE_RATIO" in binding and _is_close(output_ratio, effective_max):
        unmet_target_reason = "MAX_HEDGE_CAP"

    notes = ("ROUNDING_STEP_RATIO_0.01",) if policy.rounding_lot_notional is not None else ()

    return PolicyApplicationResultV1(
        contract_version="v1",
        policy_id=policy.policy_id,
        input_recommended_hedge_ratio=input_ratio,
        output_hedge_ratio=output_ratio,
        binding_constraints=tuple(binding),
        unmet_target_reason=unmet_target_reason,
        notes=notes,
    )


__all__ = [
    "HedgePolicyV1",
    "PolicyApplicationResultV1",
    "apply_hedge_policy_v1",
]
