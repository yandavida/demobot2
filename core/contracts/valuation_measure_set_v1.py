from __future__ import annotations

from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1


PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1: tuple[ValuationMeasureNameV1, ...] = (
    ValuationMeasureNameV1.PRESENT_VALUE,
    ValuationMeasureNameV1.INTRINSIC_VALUE,
    ValuationMeasureNameV1.TIME_VALUE,
    ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED,
    ValuationMeasureNameV1.GAMMA_SPOT,
    ValuationMeasureNameV1.VEGA_1VOL_ABS,
    ValuationMeasureNameV1.THETA_1D_CALENDAR,
    ValuationMeasureNameV1.RHO_DOMESTIC_1PCT,
    ValuationMeasureNameV1.RHO_FOREIGN_1PCT,
)

PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1: tuple[ValuationMeasureNameV1, ...] = (
    ValuationMeasureNameV1.PRESENT_VALUE,
    ValuationMeasureNameV1.INTRINSIC_VALUE,
    ValuationMeasureNameV1.TIME_VALUE,
)

if len(PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1) != len(set(PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1)):
    raise RuntimeError("PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1 must be unique")

if len(PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1) != len(set(PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1)):
    raise RuntimeError("PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1 must be unique")


__all__ = [
    "PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1",
    "PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1",
]
