from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Sequence, Dict
import math
from core.contracts.money import Currency
from core.pnl.theoretical import PositionPnL

@dataclass(frozen=True)
class PortfolioPnLBreakdown:
    base_currency: Currency
    total_pnl: float
    delta_pnl: float
    gamma_pnl: float
    vega_pnl: float
    theta_pnl: float
    residual: float
    items: Tuple[PositionPnL, ...]
    notes_summary: Dict[str, int] = field(default_factory=dict)

def compute_portfolio_pnl_breakdown(
    *,
    positions_inputs: Sequence[PositionPnL],
    base_currency: Currency,
) -> PortfolioPnLBreakdown:
    # Sort items deterministically by (symbol, position_id)
    items = tuple(sorted(positions_inputs, key=lambda x: (x.symbol, x.position_id)))
    total_pnl = math.fsum(p.pnl for p in items)
    delta_pnl = math.fsum(p.attribution.delta_pnl for p in items)
    gamma_pnl = math.fsum(p.attribution.gamma_pnl for p in items)
    vega_pnl = math.fsum(p.attribution.vega_pnl for p in items)
    theta_pnl = math.fsum(p.attribution.theta_pnl for p in items)
    residual = math.fsum(p.attribution.residual for p in items)
    # notes_summary: count occurrences of each note
    notes_summary: Dict[str, int] = {}
    for p in items:
        for note in p.attribution.notes:
            notes_summary[note] = notes_summary.get(note, 0) + 1
    return PortfolioPnLBreakdown(
        base_currency=base_currency,
        total_pnl=total_pnl,
        delta_pnl=delta_pnl,
        gamma_pnl=gamma_pnl,
        vega_pnl=vega_pnl,
        theta_pnl=theta_pnl,
        residual=residual,
        items=items,
        notes_summary=notes_summary,
    )
