from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1


@dataclass(frozen=True)
class ValuationMeasureResultV1:
    """Immutable value container for a governed single-trade valuation measure."""

    measure_name: ValuationMeasureNameV1
    value: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.measure_name, ValuationMeasureNameV1):
            raise ValueError("measure_name must be ValuationMeasureNameV1")
        if not isinstance(self.value, Decimal):
            raise ValueError("value must be Decimal")
        if not self.value.is_finite():
            raise ValueError("value must be finite")


__all__ = ["ValuationMeasureResultV1"]
