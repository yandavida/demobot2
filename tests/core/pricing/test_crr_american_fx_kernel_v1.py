from __future__ import annotations

from decimal import Decimal

import pytest

from core.numeric_policy import EXERCISE_EPSILON_ABS_V1
from core.pricing.black_scholes_fx_kernel_v1 import black_scholes_fx_measures_v1
from core.pricing.crr_american_fx_kernel_v1 import apply_american_exercise_decision_v1
from core.pricing.crr_american_fx_kernel_v1 import crr_american_fx_kernel_v1


def test_deterministic_rerun_identity() -> None:
    kwargs = {
        "option_type": "put",
        "spot": Decimal("95"),
        "strike": Decimal("100"),
        "domestic_rate": Decimal("0.05"),
        "foreign_rate": Decimal("0.00"),
        "volatility": Decimal("0.20"),
        "time_to_expiry_years": Decimal("1"),
        "step_count": 200,
    }

    first = crr_american_fx_kernel_v1(**kwargs)
    second = crr_american_fx_kernel_v1(**kwargs)

    assert first == second


def test_near_zero_time_branch_is_explicit() -> None:
    result = crr_american_fx_kernel_v1(
        option_type="call",
        spot=Decimal("120"),
        strike=Decimal("100"),
        domestic_rate=Decimal("0.03"),
        foreign_rate=Decimal("0.01"),
        volatility=Decimal("0.30"),
        time_to_expiry_years=Decimal("0"),
        step_count=50,
    )

    assert result.present_value == Decimal("20")
    assert result.intrinsic_value == Decimal("20")
    assert result.time_value == Decimal("0")


def test_zero_vol_branch_is_explicit_and_no_vol_flooring() -> None:
    zero_vol = crr_american_fx_kernel_v1(
        option_type="put",
        spot=Decimal("100"),
        strike=Decimal("105"),
        domestic_rate=Decimal("0.05"),
        foreign_rate=Decimal("0.05"),
        volatility=Decimal("0"),
        time_to_expiry_years=Decimal("1"),
        step_count=100,
    )
    near_zero_vol = crr_american_fx_kernel_v1(
        option_type="put",
        spot=Decimal("100"),
        strike=Decimal("105"),
        domestic_rate=Decimal("0.05"),
        foreign_rate=Decimal("0.05"),
        volatility=Decimal("1e-13"),
        time_to_expiry_years=Decimal("1"),
        step_count=100,
    )

    assert zero_vol == near_zero_vol


def test_invalid_state_rejection_is_strict() -> None:
    with pytest.raises(ValueError, match="step_count"):
        crr_american_fx_kernel_v1(
            option_type="put",
            spot=Decimal("100"),
            strike=Decimal("100"),
            domestic_rate=Decimal("0.01"),
            foreign_rate=Decimal("0.00"),
            volatility=Decimal("0.20"),
            time_to_expiry_years=Decimal("1"),
            step_count=0,
        )

    with pytest.raises(ValueError, match="step_count"):
        crr_american_fx_kernel_v1(
            option_type="put",
            spot=Decimal("100"),
            strike=Decimal("100"),
            domestic_rate=Decimal("0.01"),
            foreign_rate=Decimal("0.00"),
            volatility=Decimal("0.20"),
            time_to_expiry_years=Decimal("1"),
            step_count=True,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="invalid CRR risk-neutral probability"):
        crr_american_fx_kernel_v1(
            option_type="call",
            spot=Decimal("100"),
            strike=Decimal("100"),
            domestic_rate=Decimal("2.0"),
            foreign_rate=Decimal("0.0"),
            volatility=Decimal("0.05"),
            time_to_expiry_years=Decimal("1"),
            step_count=1,
        )


def test_early_exercise_strict_rule_tie_and_dominance() -> None:
    continuation = Decimal("10")

    # near-tie inside epsilon boundary -> continuation
    near_tie = apply_american_exercise_decision_v1(
        exercise_value=continuation + (EXERCISE_EPSILON_ABS_V1 / Decimal("2")),
        continuation_value=continuation,
    )
    assert near_tie == continuation

    # strict dominance beyond epsilon -> exercise
    dominance = apply_american_exercise_decision_v1(
        exercise_value=continuation + (EXERCISE_EPSILON_ABS_V1 * Decimal("2")),
        continuation_value=continuation,
    )
    assert dominance == continuation + (EXERCISE_EPSILON_ABS_V1 * Decimal("2"))


def test_intrinsic_time_value_consistency_and_non_negative_pv() -> None:
    result = crr_american_fx_kernel_v1(
        option_type="put",
        spot=Decimal("95"),
        strike=Decimal("100"),
        domestic_rate=Decimal("0.03"),
        foreign_rate=Decimal("0.01"),
        volatility=Decimal("0.20"),
        time_to_expiry_years=Decimal("1"),
        step_count=250,
    )

    assert result.time_value == result.present_value - result.intrinsic_value
    assert result.present_value >= result.intrinsic_value
    assert result.present_value >= Decimal("0")


def test_american_not_below_european_sanity() -> None:
    params = {
        "option_type": "put",
        "spot": Decimal("95"),
        "strike": Decimal("100"),
        "domestic_rate": Decimal("0.05"),
        "foreign_rate": Decimal("0.00"),
        "volatility": Decimal("0.25"),
        "time_to_expiry_years": Decimal("1"),
    }

    american = crr_american_fx_kernel_v1(step_count=500, **params)
    european_measures = black_scholes_fx_measures_v1(**params)
    european_pv = next(m.value for m in european_measures if m.measure_name.value == "present_value")

    assert american.present_value >= european_pv


def test_basic_regime_coverage_call_put_itm_otm_and_carry() -> None:
    call_otm = crr_american_fx_kernel_v1(
        option_type="call",
        spot=Decimal("95"),
        strike=Decimal("100"),
        domestic_rate=Decimal("0.02"),
        foreign_rate=Decimal("0.05"),
        volatility=Decimal("0.20"),
        time_to_expiry_years=Decimal("0.75"),
        step_count=200,
    )
    put_itm = crr_american_fx_kernel_v1(
        option_type="put",
        spot=Decimal("95"),
        strike=Decimal("100"),
        domestic_rate=Decimal("0.02"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.20"),
        time_to_expiry_years=Decimal("0.75"),
        step_count=200,
    )

    assert call_otm.present_value >= Decimal("0")
    assert put_itm.present_value >= put_itm.intrinsic_value
