from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from core.pricing.types import PriceResult


@dataclass(frozen=True)
class BacktestStepResult:
    t: int | str
    price: PriceResult


@dataclass(frozen=True)
class BacktestResult:
    steps: Tuple[BacktestStepResult, ...]
    final_price: PriceResult | None = None

    def __post_init__(self) -> None:  # type: ignore[override]
        # Ensure steps are a tuple
        object.__setattr__(self, "steps", tuple(self.steps))


__all__ = ["BacktestStepResult", "BacktestResult"]
