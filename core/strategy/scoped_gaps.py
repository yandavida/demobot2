from __future__ import annotations

from typing import Dict
from core.strategy.gaps import PortfolioExposures, PortfolioGaps
from core.strategy.targets import ScopedTargets
import math


def compute_scoped_gaps(current_by_strategy: Dict[str, PortfolioExposures], scoped_targets: ScopedTargets) -> Dict[str, PortfolioGaps]:
    """Compute per-strategy gaps for strategies that have scoped overrides.

    Returns a mapping StrategyId -> PortfolioGaps. Strategies without scoped
    overrides are omitted from the result. Values are None where the scoped
    target is None.
    """
    res: Dict[str, PortfolioGaps] = {}
    overrides = getattr(scoped_targets, "overrides", {}) or {}

    for sid, exposure in current_by_strategy.items():
        # validate strategy id
        if not isinstance(sid, str) or sid.strip() == "":
            raise ValueError("StrategyId must be a non-empty string")
        # skip if no scoped override for this strategy
        if sid not in overrides:
            continue
        st = overrides[sid]
        # validate exposure numeric finiteness
        for name in ("delta", "gamma", "vega"):
            val = getattr(exposure, name)
            try:
                f = float(val)
            except Exception as e:
                raise ValueError(f"current {name} for strategy {sid} must be finite float") from e
            if not math.isfinite(f):
                raise ValueError(f"current {name} for strategy {sid} must be finite (not NaN/Inf)")

        # compute gaps per-dimension
        def gap(name: str):
            tgt = getattr(st, name)
            if tgt is None:
                return None
            return float(tgt) - float(getattr(exposure, name))

        res[sid] = PortfolioGaps(delta=gap("delta"), gamma=gap("gamma"), vega=gap("vega"))

    return res
