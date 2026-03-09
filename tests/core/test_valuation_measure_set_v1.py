from __future__ import annotations

from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1


def test_canonical_phase_c_measure_order_is_frozen() -> None:
    assert PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1 == (
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


def test_canonical_phase_c_measure_order_is_unique() -> None:
    assert len(PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1) == len(set(PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1))
