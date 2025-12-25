from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from core.finance.market import MarketSnapshot


@dataclass(frozen=True)
class TimePoint:
    t: int | str
    snapshot: MarketSnapshot


@dataclass(frozen=True)
class BacktestTimeline:
    points: Tuple[TimePoint, ...]

    def __post_init__(self) -> None:  # type: ignore[override]
        # Deterministic ordering by string of t
        sorted_points = tuple(sorted(self.points, key=lambda p: str(p.t)))
        object.__setattr__(self, "points", sorted_points)


__all__ = ["TimePoint", "BacktestTimeline"]
