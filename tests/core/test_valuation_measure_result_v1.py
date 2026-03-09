from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v1 import ValuationMeasureResultV1


def test_measure_result_is_immutable() -> None:
    result = ValuationMeasureResultV1(
        measure_name=ValuationMeasureNameV1.PRESENT_VALUE,
        value=Decimal("123.45"),
    )

    with pytest.raises(FrozenInstanceError):
        result.value = Decimal("200")


def test_measure_result_requires_decimal_value() -> None:
    with pytest.raises(ValueError, match="value must be Decimal"):
        ValuationMeasureResultV1(
            measure_name=ValuationMeasureNameV1.PRESENT_VALUE,
            value="123.45",
        )


def test_measure_result_rejects_invalid_measure_name_type() -> None:
    with pytest.raises(ValueError, match="measure_name must be ValuationMeasureNameV1"):
        ValuationMeasureResultV1(
            measure_name="present_value",
            value=Decimal("123.45"),
        )


def test_measure_result_rejects_non_finite_decimal() -> None:
    with pytest.raises(ValueError, match="value must be finite"):
        ValuationMeasureResultV1(
            measure_name=ValuationMeasureNameV1.PRESENT_VALUE,
            value=Decimal("NaN"),
        )
