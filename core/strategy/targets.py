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


class ScopedTargets:
    """Scoped per-strategy targets overlaying a portfolio baseline.

    `overrides` is a mapping StrategyId (str) -> `PortfolioTargets`.
    StrategyId must be a non-empty, non-whitespace string. Equality and
    `repr` are canonicalized (sorted by StrategyId) to ensure deterministic
    ordering and permutation-invariance.
    """

    def __init__(self, baseline: Optional[PortfolioTargets] = None, overrides: Optional[dict] = None):
        self.baseline = baseline
        self.overrides = {}
        if overrides:
            for k, v in overrides.items():
                if not isinstance(k, str) or k.strip() == "":
                    raise ValueError("StrategyId must be a non-empty string")
                if not isinstance(v, PortfolioTargets):
                    raise ValueError("override values must be PortfolioTargets")
                # validate numeric constraints via PortfolioTargets constructor
                # (which will raise if invalid)
                # store
                self.overrides[k] = v

    def canonical_items(self):
        return tuple(sorted(self.overrides.items(), key=lambda kv: kv[0]))

    def __eq__(self, other):
        if not isinstance(other, ScopedTargets):
            return False
        if self.baseline != other.baseline:
            return False
        return dict(self.canonical_items()) == dict(other.canonical_items())

    def __repr__(self):
        items = self.canonical_items()
        return f"ScopedTargets(baseline={self.baseline!r}, overrides={items!r})"
