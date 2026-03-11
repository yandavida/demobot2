from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import math

from core.numeric_policy import EXERCISE_EPSILON_ABS_V1
from core.numeric_policy import TIME_EPSILON_YEARS_V1
from core.numeric_policy import VOL_EPSILON_ABS_V1


SUPPORTED_OPTION_TYPES_V1 = {"call", "put"}


def _require_finite_decimal(value: Decimal, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_option_type(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("option_type must be a string")
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_OPTION_TYPES_V1:
        raise ValueError("option_type must be 'call' or 'put'")
    return normalized


def _decimal_from_float(value: float, field_name: str) -> Decimal:
    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    return Decimal(str(value))


def _float_from_decimal(value: Decimal, field_name: str) -> float:
    _require_finite_decimal(value, field_name)
    as_float = float(value)
    if not math.isfinite(as_float):
        raise ValueError(f"{field_name} must be finite")
    return as_float


def _intrinsic_value_spot_v1(*, option_type: str, spot: Decimal, strike: Decimal) -> Decimal:
    if option_type == "call":
        return max(spot - strike, Decimal("0"))
    return max(strike - spot, Decimal("0"))


def apply_american_exercise_decision_v1(*, exercise_value: Decimal, continuation_value: Decimal) -> Decimal:
    """Apply frozen Phase D early-exercise rule with strict tie-to-continuation semantics."""

    exercise = _require_finite_decimal(exercise_value, "exercise_value")
    continuation = _require_finite_decimal(continuation_value, "continuation_value")

    if exercise > continuation + EXERCISE_EPSILON_ABS_V1:
        return exercise
    return continuation


@dataclass(frozen=True)
class CrrAmericanKernelResultV1:
    """Pure CRR American kernel direct outputs for Phase D model-math stage."""

    present_value: Decimal
    intrinsic_value: Decimal
    time_value: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "present_value", _require_finite_decimal(self.present_value, "present_value"))
        object.__setattr__(self, "intrinsic_value", _require_finite_decimal(self.intrinsic_value, "intrinsic_value"))
        object.__setattr__(self, "time_value", _require_finite_decimal(self.time_value, "time_value"))


def crr_american_fx_kernel_v1(
    *,
    option_type: str,
    spot: Decimal,
    strike: Decimal,
    domestic_rate: Decimal,
    foreign_rate: Decimal,
    volatility: Decimal,
    time_to_expiry_years: Decimal,
    step_count: int,
) -> CrrAmericanKernelResultV1:
    """Compute pure Phase D CRR American model-direct outputs for a single-trade vanilla FX option."""

    option = _require_option_type(option_type)

    spot_value = _require_finite_decimal(spot, "spot")
    strike_value = _require_finite_decimal(strike, "strike")
    domestic_rate_value = _require_finite_decimal(domestic_rate, "domestic_rate")
    foreign_rate_value = _require_finite_decimal(foreign_rate, "foreign_rate")
    volatility_value = _require_finite_decimal(volatility, "volatility")
    time_value = _require_finite_decimal(time_to_expiry_years, "time_to_expiry_years")

    if spot_value <= 0:
        raise ValueError("spot must be > 0")
    if strike_value <= 0:
        raise ValueError("strike must be > 0")
    if volatility_value < 0:
        raise ValueError("volatility must be >= 0")
    if time_value < 0:
        raise ValueError("time_to_expiry_years must be >= 0")
    if isinstance(step_count, bool) or not isinstance(step_count, int) or step_count <= 0:
        raise ValueError("step_count must be a positive integer")

    intrinsic_value = _intrinsic_value_spot_v1(option_type=option, spot=spot_value, strike=strike_value)

    if time_value <= TIME_EPSILON_YEARS_V1:
        return CrrAmericanKernelResultV1(
            present_value=intrinsic_value,
            intrinsic_value=intrinsic_value,
            time_value=Decimal("0"),
        )

    spot_float = _float_from_decimal(spot_value, "spot")
    strike_float = _float_from_decimal(strike_value, "strike")
    rd_float = _float_from_decimal(domestic_rate_value, "domestic_rate")
    rf_float = _float_from_decimal(foreign_rate_value, "foreign_rate")
    time_float = _float_from_decimal(time_value, "time_to_expiry_years")

    dt = time_float / float(step_count)
    if not math.isfinite(dt) or dt <= 0.0:
        raise ValueError("degenerate CRR parameterization")

    discount = math.exp(-rd_float * dt)

    if volatility_value <= VOL_EPSILON_ABS_V1:
        # Explicit deterministic branch: no vol flooring, no stochastic lattice.
        values = [Decimal("0")] * (step_count + 1)
        for j in range(step_count, -1, -1):
            spot_j = _decimal_from_float(spot_float * math.exp((rd_float - rf_float) * dt * float(j)), "spot_path")
            exercise_j = _intrinsic_value_spot_v1(option_type=option, spot=spot_j, strike=strike_value)
            if j == step_count:
                values[j] = exercise_j
            else:
                continuation_j = _decimal_from_float(discount * float(values[j + 1]), "continuation")
                values[j] = apply_american_exercise_decision_v1(
                    exercise_value=exercise_j,
                    continuation_value=continuation_j,
                )

        present_value = values[0]
        return CrrAmericanKernelResultV1(
            present_value=present_value,
            intrinsic_value=intrinsic_value,
            time_value=present_value - intrinsic_value,
        )

    vol_float = _float_from_decimal(volatility_value, "volatility")
    u = math.exp(vol_float * math.sqrt(dt))
    d = 1.0 / u

    if u == d:
        raise ValueError("degenerate CRR parameterization")

    p = (math.exp((rd_float - rf_float) * dt) - d) / (u - d)
    if p < 0.0 or p > 1.0:
        raise ValueError("invalid CRR risk-neutral probability")

    terminal_values: list[Decimal] = []
    for i in range(step_count + 1):
        node_spot = _decimal_from_float(spot_float * (u ** i) * (d ** (step_count - i)), "node_spot")
        terminal_values.append(_intrinsic_value_spot_v1(option_type=option, spot=node_spot, strike=strike_value))

    for j in range(step_count - 1, -1, -1):
        next_values: list[Decimal] = []
        for i in range(j + 1):
            continuation = _decimal_from_float(
                discount * (p * float(terminal_values[i + 1]) + (1.0 - p) * float(terminal_values[i])),
                "continuation",
            )
            node_spot = _decimal_from_float(spot_float * (u ** i) * (d ** (j - i)), "node_spot")
            exercise = _intrinsic_value_spot_v1(option_type=option, spot=node_spot, strike=strike_value)
            next_values.append(
                apply_american_exercise_decision_v1(
                    exercise_value=exercise,
                    continuation_value=continuation,
                )
            )
        terminal_values = next_values

    present_value = terminal_values[0]
    return CrrAmericanKernelResultV1(
        present_value=present_value,
        intrinsic_value=intrinsic_value,
        time_value=present_value - intrinsic_value,
    )


__all__ = [
    "CrrAmericanKernelResultV1",
    "SUPPORTED_OPTION_TYPES_V1",
    "apply_american_exercise_decision_v1",
    "crr_american_fx_kernel_v1",
]
