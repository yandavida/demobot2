from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import math


@dataclass(frozen=True)
class PortfolioTargets:
    """Declarative portfolio-level strategy targets.

    Attributes may be `None` (unset) or a finite float. `0.0` is a valid
    explicit target. NaN/Inf are rejected.
    """

    delta: Optional[float] = None
    gamma: Optional[float] = None
    vega: Optional[float] = None

    def __post_init__(self) -> None:
        for name in ("delta", "gamma", "vega"):
            val = getattr(self, name)
            if val is None:
                continue
            # Accept ints as well, but ensure finiteness.
            try:
                f = float(val)
            except Exception as e:
                raise ValueError(f"{name} must be float or None") from e
            if not math.isfinite(f):
                raise ValueError(f"{name} must be finite (not NaN/Inf)")
