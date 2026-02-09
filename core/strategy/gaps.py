from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import math


@dataclass(frozen=True)
class PortfolioExposures:
    delta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0

    def __post_init__(self) -> None:
        for name in ("delta", "gamma", "vega"):
            val = getattr(self, name)
            try:
                f = float(val)
            except Exception as e:
                raise ValueError(f"{name} must be a finite float") from e
            if not math.isfinite(f):
                raise ValueError(f"{name} must be finite (not NaN/Inf)")


@dataclass(frozen=True)
class PortfolioGaps:
    delta: Optional[float] = None
    gamma: Optional[float] = None
    vega: Optional[float] = None


def compute_portfolio_gaps(current: PortfolioExposures, targets) -> PortfolioGaps:
    """Compute portfolio-level gaps: target - current, or None if target is None.

    `targets` is expected to be an object with attributes `delta`, `gamma`, `vega`
    (e.g., `PortfolioTargets`). This function performs no pricing or exposure
    computation — it is purely an analysis artifact.
    """
    # validate current exposures
    for name in ("delta", "gamma", "vega"):
        val = getattr(current, name)
        try:
            f = float(val)
        except Exception as e:
            raise ValueError(f"current {name} must be finite float") from e
        if not math.isfinite(f):
            raise ValueError(f"current {name} must be finite (not NaN/Inf)")

    def gap_for(name: str) -> Optional[float]:
        target_val = getattr(targets, name)
        if target_val is None:
            return None
        return float(target_val) - float(getattr(current, name))

    return PortfolioGaps(delta=gap_for("delta"), gamma=gap_for("gamma"), vega=gap_for("vega"))
