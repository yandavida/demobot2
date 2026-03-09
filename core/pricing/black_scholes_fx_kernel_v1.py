from __future__ import annotations

from decimal import Decimal
import math

from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v1 import ValuationMeasureResultV1
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1


NORMAL_CDF_POLICY_V1 = "math.erf_standard_normal_cdf"
NUMERICAL_BOUNDARY_POLICY_V1 = "decimal_inputs_float_transcendentals_decimal_outputs"
TIME_FRACTION_POLICY_V1 = "resolved_time_fraction_input"

VEGA_1VOL_ABS_BUMP_V1 = Decimal("0.01")
RHO_1PCT_BUMP_V1 = Decimal("0.01")
THETA_1D_CALENDAR_YEAR_FRACTION_V1 = Decimal("1") / Decimal("365")

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


def _normal_cdf_v1(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _normal_pdf_v1(x: float) -> float:
    return math.exp(-(x * x) / 2.0) / math.sqrt(2.0 * math.pi)


def _discount_factor_v1(rate: Decimal, time_to_expiry_years: Decimal) -> Decimal:
    rate_float = _float_from_decimal(rate, "rate")
    time_float = _float_from_decimal(time_to_expiry_years, "time_to_expiry_years")
    return _decimal_from_float(math.exp(-rate_float * time_float), "discount_factor")


def _present_value_v1(
    *,
    option_type: str,
    spot: Decimal,
    strike: Decimal,
    domestic_rate: Decimal,
    foreign_rate: Decimal,
    volatility: Decimal,
    time_to_expiry_years: Decimal,
) -> Decimal:
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

    spot_float = _float_from_decimal(spot_value, "spot")
    strike_float = _float_from_decimal(strike_value, "strike")
    rate_d = _float_from_decimal(domestic_rate_value, "domestic_rate")
    rate_f = _float_from_decimal(foreign_rate_value, "foreign_rate")
    vol = _float_from_decimal(volatility_value, "volatility")
    time_float = _float_from_decimal(time_value, "time_to_expiry_years")

    if time_value == 0 or volatility_value == 0:
        forward = spot_float * math.exp((rate_d - rate_f) * time_float)
        discounted = math.exp(-rate_d * time_float)
        intrinsic_forward = max(forward - strike_float, 0.0) if option == "call" else max(strike_float - forward, 0.0)
        return _decimal_from_float(discounted * intrinsic_forward, "present_value")

    sqrt_t = math.sqrt(time_float)
    d1 = (math.log(spot_float / strike_float) + (rate_d - rate_f + 0.5 * vol * vol) * time_float) / (vol * sqrt_t)
    d2 = d1 - vol * sqrt_t

    discount_domestic = math.exp(-rate_d * time_float)
    discount_foreign = math.exp(-rate_f * time_float)

    if option == "call":
        pv = spot_float * discount_foreign * _normal_cdf_v1(d1) - strike_float * discount_domestic * _normal_cdf_v1(d2)
    else:
        pv = strike_float * discount_domestic * _normal_cdf_v1(-d2) - spot_float * discount_foreign * _normal_cdf_v1(-d1)

    return _decimal_from_float(pv, "present_value")


def _delta_gamma_v1(
    *,
    option_type: str,
    spot: Decimal,
    strike: Decimal,
    domestic_rate: Decimal,
    foreign_rate: Decimal,
    volatility: Decimal,
    time_to_expiry_years: Decimal,
) -> tuple[Decimal, Decimal]:
    option = _require_option_type(option_type)

    spot_float = _float_from_decimal(spot, "spot")
    strike_float = _float_from_decimal(strike, "strike")
    rate_d = _float_from_decimal(domestic_rate, "domestic_rate")
    rate_f = _float_from_decimal(foreign_rate, "foreign_rate")
    vol = _float_from_decimal(volatility, "volatility")
    time_float = _float_from_decimal(time_to_expiry_years, "time_to_expiry_years")

    if time_to_expiry_years == 0 or volatility == 0:
        forward = spot_float * math.exp((rate_d - rate_f) * time_float)
        discount_foreign = math.exp(-rate_f * time_float)
        if option == "call":
            if forward > strike_float:
                return _decimal_from_float(discount_foreign, "delta"), Decimal("0")
            if forward < strike_float:
                return Decimal("0"), Decimal("0")
            return _decimal_from_float(0.5 * discount_foreign, "delta"), Decimal("0")

        if forward < strike_float:
            return _decimal_from_float(-discount_foreign, "delta"), Decimal("0")
        if forward > strike_float:
            return Decimal("0"), Decimal("0")
        return _decimal_from_float(-0.5 * discount_foreign, "delta"), Decimal("0")

    sqrt_t = math.sqrt(time_float)
    d1 = (math.log(spot_float / strike_float) + (rate_d - rate_f + 0.5 * vol * vol) * time_float) / (vol * sqrt_t)
    discount_foreign = math.exp(-rate_f * time_float)

    if option == "call":
        delta = discount_foreign * _normal_cdf_v1(d1)
    else:
        delta = discount_foreign * (_normal_cdf_v1(d1) - 1.0)

    gamma = discount_foreign * _normal_pdf_v1(d1) / (spot_float * vol * sqrt_t)
    return _decimal_from_float(delta, "delta"), _decimal_from_float(gamma, "gamma")


def black_scholes_fx_measures_v1(
    *,
    option_type: str,
    spot: Decimal,
    strike: Decimal,
    domestic_rate: Decimal,
    foreign_rate: Decimal,
    volatility: Decimal,
    time_to_expiry_years: Decimal,
) -> tuple[ValuationMeasureResultV1, ...]:
    """Compute governed Phase C single-trade FX option valuation measures.

    Inputs are resolved numerics only. No day-count logic is performed here; the kernel consumes
    time_to_expiry_years exactly as provided by upstream resolved inputs.
    """

    option = _require_option_type(option_type)

    _require_finite_decimal(spot, "spot")
    _require_finite_decimal(strike, "strike")
    _require_finite_decimal(domestic_rate, "domestic_rate")
    _require_finite_decimal(foreign_rate, "foreign_rate")
    _require_finite_decimal(volatility, "volatility")
    _require_finite_decimal(time_to_expiry_years, "time_to_expiry_years")

    if spot <= 0:
        raise ValueError("spot must be > 0")
    if strike <= 0:
        raise ValueError("strike must be > 0")
    if volatility < 0:
        raise ValueError("volatility must be >= 0")
    if time_to_expiry_years < 0:
        raise ValueError("time_to_expiry_years must be >= 0")

    present_value = _present_value_v1(
        option_type=option,
        spot=spot,
        strike=strike,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        volatility=volatility,
        time_to_expiry_years=time_to_expiry_years,
    )

    if option == "call":
        intrinsic_value = max(spot - strike, Decimal("0"))
    else:
        intrinsic_value = max(strike - spot, Decimal("0"))

    time_value = present_value - intrinsic_value

    delta_spot_non_premium_adjusted, gamma_spot = _delta_gamma_v1(
        option_type=option,
        spot=spot,
        strike=strike,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        volatility=volatility,
        time_to_expiry_years=time_to_expiry_years,
    )

    pv_vol_up = _present_value_v1(
        option_type=option,
        spot=spot,
        strike=strike,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        volatility=volatility + VEGA_1VOL_ABS_BUMP_V1,
        time_to_expiry_years=time_to_expiry_years,
    )
    vega_1vol_abs = pv_vol_up - present_value

    pv_next_calendar_day = _present_value_v1(
        option_type=option,
        spot=spot,
        strike=strike,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate,
        volatility=volatility,
        time_to_expiry_years=time_to_expiry_years + THETA_1D_CALENDAR_YEAR_FRACTION_V1,
    )
    theta_1d_calendar = pv_next_calendar_day - present_value

    pv_rd_up = _present_value_v1(
        option_type=option,
        spot=spot,
        strike=strike,
        domestic_rate=domestic_rate + RHO_1PCT_BUMP_V1,
        foreign_rate=foreign_rate,
        volatility=volatility,
        time_to_expiry_years=time_to_expiry_years,
    )
    rho_domestic_1pct = pv_rd_up - present_value

    pv_rf_up = _present_value_v1(
        option_type=option,
        spot=spot,
        strike=strike,
        domestic_rate=domestic_rate,
        foreign_rate=foreign_rate + RHO_1PCT_BUMP_V1,
        volatility=volatility,
        time_to_expiry_years=time_to_expiry_years,
    )
    rho_foreign_1pct = pv_rf_up - present_value

    values = {
        ValuationMeasureNameV1.PRESENT_VALUE: present_value,
        ValuationMeasureNameV1.INTRINSIC_VALUE: intrinsic_value,
        ValuationMeasureNameV1.TIME_VALUE: time_value,
        ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED: delta_spot_non_premium_adjusted,
        ValuationMeasureNameV1.GAMMA_SPOT: gamma_spot,
        ValuationMeasureNameV1.VEGA_1VOL_ABS: vega_1vol_abs,
        ValuationMeasureNameV1.THETA_1D_CALENDAR: theta_1d_calendar,
        ValuationMeasureNameV1.RHO_DOMESTIC_1PCT: rho_domestic_1pct,
        ValuationMeasureNameV1.RHO_FOREIGN_1PCT: rho_foreign_1pct,
    }

    return tuple(
        ValuationMeasureResultV1(measure_name=measure_name, value=values[measure_name])
        for measure_name in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
    )


__all__ = [
    "NORMAL_CDF_POLICY_V1",
    "NUMERICAL_BOUNDARY_POLICY_V1",
    "RHO_1PCT_BUMP_V1",
    "THETA_1D_CALENDAR_YEAR_FRACTION_V1",
    "TIME_FRACTION_POLICY_V1",
    "VEGA_1VOL_ABS_BUMP_V1",
    "black_scholes_fx_measures_v1",
]
