from __future__ import annotations

from typing import Optional

from core.portfolio.v2_models import PortfolioStateV2
from core.fx.converter import FxConverter
from core.market_data.types import MarketSnapshot
from core.pnl.theoretical import compute_portfolio_theoretical_from_state


def compute_unrealized_from_pvs(pv0: Optional[float], pv1: float) -> float:
    """Pure helper: compute unrealized given two PVs.

    Compatibility mode: if `pv0` is None (no anchor), return 0.0 deterministically.
    """
    if pv0 is None:
        return 0.0
    return float(pv1) - float(pv0)


def compute_unrealized_pnl(*, state_before: PortfolioStateV2 | None, state_after: PortfolioStateV2, market_snapshot: MarketSnapshot, as_of_ts, fx_converter: FxConverter) -> float:
    """Compute theoretical unrealized PnL = PV(state_after) - PV(state_before).

    Determinism and purity:
    - `as_of_ts` is required and used as the deterministic as-of timestamp.
    - No wall-clock usage, no mutation.

    Compatibility:
    - If `state_before` is None or no reference PV is available, returns 0.0.

    This function delegates valuation to `compute_portfolio_theoretical_from_state` to
    remain consistent with existing theoretical mark-to-model wiring.
    """
    if as_of_ts is None:
        raise ValueError("as_of_ts (event timestamp) is required and must be provided explicitly")

    # pv0: reference; compatibility mode if missing
    if state_before is None:
        pv0 = None
    else:
        prev = compute_portfolio_theoretical_from_state(state=state_before, market_snapshot=market_snapshot, as_of_ts=as_of_ts, fx_converter=fx_converter)
        pv0 = prev.get("pv")

    curr = compute_portfolio_theoretical_from_state(state=state_after, market_snapshot=market_snapshot, as_of_ts=as_of_ts, fx_converter=fx_converter)
    pv1 = curr.get("pv")

    return compute_unrealized_from_pvs(pv0=pv0, pv1=pv1)
