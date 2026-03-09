from __future__ import annotations

from decimal import Decimal

import pytest

from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
from core.pricing.black_scholes_fx_kernel_v1 import NORMAL_CDF_POLICY_V1
from core.pricing.black_scholes_fx_kernel_v1 import NUMERICAL_BOUNDARY_POLICY_V1
from core.pricing.black_scholes_fx_kernel_v1 import RHO_1PCT_BUMP_V1
from core.pricing.black_scholes_fx_kernel_v1 import THETA_1D_CALENDAR_YEAR_FRACTION_V1
from core.pricing.black_scholes_fx_kernel_v1 import TIME_FRACTION_POLICY_V1
from core.pricing.black_scholes_fx_kernel_v1 import VEGA_1VOL_ABS_BUMP_V1
from core.pricing.black_scholes_fx_kernel_v1 import black_scholes_fx_measures_v1


PRICE_TOL = Decimal("1e-10")
GREEK_TOL = Decimal("1e-10")
PARITY_TOL = Decimal("1e-10")
MONOTONICITY_TOL = Decimal("1e-12")


def _measure_map(option_type: str, **overrides: Decimal) -> dict[ValuationMeasureNameV1, Decimal]:
    params: dict[str, Decimal] = {
        "spot": Decimal("100"),
        "strike": Decimal("100"),
        "domestic_rate": Decimal("0.05"),
        "foreign_rate": Decimal("0.02"),
        "volatility": Decimal("0.20"),
        "time_to_expiry_years": Decimal("1"),
    }
    params.update(overrides)
    measures = black_scholes_fx_measures_v1(option_type=option_type, **params)
    assert tuple(item.measure_name for item in measures) == PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
    return {item.measure_name: item.value for item in measures}


def _abs_diff(a: Decimal, b: Decimal) -> Decimal:
    return abs(a - b)


def test_policy_constants_are_frozen() -> None:
    assert NORMAL_CDF_POLICY_V1 == "math.erf_standard_normal_cdf"
    assert NUMERICAL_BOUNDARY_POLICY_V1 == "decimal_inputs_float_transcendentals_decimal_outputs"
    assert TIME_FRACTION_POLICY_V1 == "resolved_time_fraction_input"
    assert VEGA_1VOL_ABS_BUMP_V1 == Decimal("0.01")
    assert RHO_1PCT_BUMP_V1 == Decimal("0.01")
    assert THETA_1D_CALENDAR_YEAR_FRACTION_V1 == Decimal("1") / Decimal("365")


def test_benchmark_call_and_put_prices_are_stable() -> None:
    call = _measure_map("call")
    put = _measure_map("put")

    assert _abs_diff(call[ValuationMeasureNameV1.PRESENT_VALUE], Decimal("9.227005508154036")) <= PRICE_TOL
    assert _abs_diff(put[ValuationMeasureNameV1.PRESENT_VALUE], Decimal("6.330080627549918")) <= PRICE_TOL


def test_put_call_parity_holds_under_fx_gk_formulation() -> None:
    spot = Decimal("100")
    strike = Decimal("95")
    rd = Decimal("0.03")
    rf = Decimal("0.01")
    t = Decimal("0.75")

    call = _measure_map(
        "call",
        spot=spot,
        strike=strike,
        domestic_rate=rd,
        foreign_rate=rf,
        volatility=Decimal("0.2"),
        time_to_expiry_years=t,
    )
    put = _measure_map(
        "put",
        spot=spot,
        strike=strike,
        domestic_rate=rd,
        foreign_rate=rf,
        volatility=Decimal("0.2"),
        time_to_expiry_years=t,
    )

    parity_lhs = call[ValuationMeasureNameV1.PRESENT_VALUE] - put[ValuationMeasureNameV1.PRESENT_VALUE]

    # RHS uses the same governed domestic/foreign discounting semantics as GK.
    from math import exp

    rhs = Decimal(str(float(spot) * exp(-float(rf) * float(t)) - float(strike) * exp(-float(rd) * float(t))))
    assert _abs_diff(parity_lhs, rhs) <= PARITY_TOL


def test_monotonicity_spot_and_volatility() -> None:
    call_low_spot = _measure_map("call", spot=Decimal("99"))
    call_high_spot = _measure_map("call", spot=Decimal("101"))
    assert call_high_spot[ValuationMeasureNameV1.PRESENT_VALUE] + MONOTONICITY_TOL >= call_low_spot[ValuationMeasureNameV1.PRESENT_VALUE]

    put_low_spot = _measure_map("put", spot=Decimal("99"))
    put_high_spot = _measure_map("put", spot=Decimal("101"))
    assert put_low_spot[ValuationMeasureNameV1.PRESENT_VALUE] + MONOTONICITY_TOL >= put_high_spot[ValuationMeasureNameV1.PRESENT_VALUE]

    call_low_vol = _measure_map("call", volatility=Decimal("0.10"))
    call_high_vol = _measure_map("call", volatility=Decimal("0.40"))
    assert call_high_vol[ValuationMeasureNameV1.PRESENT_VALUE] + MONOTONICITY_TOL >= call_low_vol[ValuationMeasureNameV1.PRESENT_VALUE]


def test_intrinsic_and_time_value_relationships_hold() -> None:
    call = _measure_map("call", spot=Decimal("120"), strike=Decimal("100"))
    put = _measure_map("put", spot=Decimal("80"), strike=Decimal("100"))

    assert call[ValuationMeasureNameV1.INTRINSIC_VALUE] == Decimal("20")
    assert put[ValuationMeasureNameV1.INTRINSIC_VALUE] == Decimal("20")

    assert call[ValuationMeasureNameV1.TIME_VALUE] == call[ValuationMeasureNameV1.PRESENT_VALUE] - call[ValuationMeasureNameV1.INTRINSIC_VALUE]
    assert put[ValuationMeasureNameV1.TIME_VALUE] == put[ValuationMeasureNameV1.PRESENT_VALUE] - put[ValuationMeasureNameV1.INTRINSIC_VALUE]


def test_vega_theta_and_rho_conventions_are_exact() -> None:
    params = {
        "spot": Decimal("100"),
        "strike": Decimal("100"),
        "domestic_rate": Decimal("0.05"),
        "foreign_rate": Decimal("0.02"),
        "volatility": Decimal("0.20"),
        "time_to_expiry_years": Decimal("1"),
    }
    base = _measure_map("call", **params)

    vol_up = _measure_map("call", **(params | {"volatility": params["volatility"] + VEGA_1VOL_ABS_BUMP_V1}))
    assert _abs_diff(
        base[ValuationMeasureNameV1.VEGA_1VOL_ABS],
        vol_up[ValuationMeasureNameV1.PRESENT_VALUE] - base[ValuationMeasureNameV1.PRESENT_VALUE],
    ) <= GREEK_TOL

    t_next = _measure_map("call", **(params | {"time_to_expiry_years": params["time_to_expiry_years"] + THETA_1D_CALENDAR_YEAR_FRACTION_V1}))
    assert _abs_diff(
        base[ValuationMeasureNameV1.THETA_1D_CALENDAR],
        t_next[ValuationMeasureNameV1.PRESENT_VALUE] - base[ValuationMeasureNameV1.PRESENT_VALUE],
    ) <= GREEK_TOL

    rd_up = _measure_map("call", **(params | {"domestic_rate": params["domestic_rate"] + RHO_1PCT_BUMP_V1}))
    assert _abs_diff(
        base[ValuationMeasureNameV1.RHO_DOMESTIC_1PCT],
        rd_up[ValuationMeasureNameV1.PRESENT_VALUE] - base[ValuationMeasureNameV1.PRESENT_VALUE],
    ) <= GREEK_TOL

    rf_up = _measure_map("call", **(params | {"foreign_rate": params["foreign_rate"] + RHO_1PCT_BUMP_V1}))
    assert _abs_diff(
        base[ValuationMeasureNameV1.RHO_FOREIGN_1PCT],
        rf_up[ValuationMeasureNameV1.PRESENT_VALUE] - base[ValuationMeasureNameV1.PRESENT_VALUE],
    ) <= GREEK_TOL


def test_near_zero_time_and_zero_volatility_policies_are_explicit() -> None:
    t0_call = _measure_map("call", time_to_expiry_years=Decimal("0"), spot=Decimal("120"), strike=Decimal("100"))
    assert t0_call[ValuationMeasureNameV1.PRESENT_VALUE] == Decimal("20")

    vol0_call = _measure_map(
        "call",
        spot=Decimal("120"),
        strike=Decimal("100"),
        domestic_rate=Decimal("0.02"),
        foreign_rate=Decimal("0.01"),
        volatility=Decimal("0"),
        time_to_expiry_years=Decimal("0.5"),
    )

    from math import exp

    expected = Decimal(
        str(
            exp(-0.02 * 0.5)
            * max(120.0 * exp((0.02 - 0.01) * 0.5) - 100.0, 0.0)
        )
    )
    assert _abs_diff(vol0_call[ValuationMeasureNameV1.PRESENT_VALUE], expected) <= PRICE_TOL


def test_invalid_inputs_are_rejected_explicitly() -> None:
    with pytest.raises(ValueError, match="option_type"):
        _measure_map("straddle")

    with pytest.raises(ValueError, match="spot"):
        _measure_map("call", spot=Decimal("0"))

    with pytest.raises(ValueError, match="strike"):
        _measure_map("call", strike=Decimal("0"))

    with pytest.raises(ValueError, match="volatility"):
        _measure_map("call", volatility=Decimal("-0.01"))

    with pytest.raises(ValueError, match="time_to_expiry_years"):
        _measure_map("call", time_to_expiry_years=Decimal("-0.01"))


def test_determinism_repeated_calls_same_inputs_same_outputs() -> None:
    first = black_scholes_fx_measures_v1(
        option_type="call",
        spot=Decimal("100"),
        strike=Decimal("102"),
        domestic_rate=Decimal("0.02"),
        foreign_rate=Decimal("0.01"),
        volatility=Decimal("0.23"),
        time_to_expiry_years=Decimal("0.8"),
    )
    second = black_scholes_fx_measures_v1(
        option_type="call",
        spot=Decimal("100"),
        strike=Decimal("102"),
        domestic_rate=Decimal("0.02"),
        foreign_rate=Decimal("0.01"),
        volatility=Decimal("0.23"),
        time_to_expiry_years=Decimal("0.8"),
    )

    assert first == second
