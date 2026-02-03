from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Tuple, Sequence, Mapping, Any, Optional

from core.pricing.types import PriceResult
from core.contracts.money import Currency
from core.fx.converter import FxConverter
from core.market_data.types import MarketSnapshot
# NOTE: this wiring module does not use numeric guards; remove unused imports.
# For wiring from v2 portfolio state -> totals
from core.portfolio.v2_models import PortfolioStateV2
from core.portfolio.v2_aggregation import aggregate_portfolio as aggregate_portfolio_v2

PnLMode = Literal["step", "cumulative"]

@dataclass(frozen=True)
class PnLAttribution:
    delta_pnl: float = 0.0
    theta_pnl: float = 0.0
    vega_pnl: float = 0.0
    gamma_pnl: float = 0.0
    residual: float = 0.0
    notes: Tuple[str, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class PositionPnL:
    position_id: str
    symbol: str
    pv: float
    pnl: float
    attribution: PnLAttribution
    currency: Currency

@dataclass(frozen=True)
class PortfolioPnL:
    total_pv: float
    total_pnl: float
    positions: Tuple[PositionPnL, ...]
    currency: Currency

def compute_position_pnl(
    *,
    position_id: str,
    symbol: str,
    prev_pr: Optional[PriceResult],
    curr_pr: PriceResult,
    prev_snapshot: Optional[MarketSnapshot],
    curr_snapshot: MarketSnapshot,
    quantity: float,
    base_currency: Currency,
    fx_converter: FxConverter,
    mode: PnLMode,
    t_prev: Any = None,
    t_curr: Any = None,
) -> PositionPnL:
    notes = []
    # Convert PVs to base currency
    curr_pv = float(curr_pr.pv) * quantity
    curr_pv_ccy = curr_pr.currency
    if curr_pv_ccy != base_currency:
        curr_pv = float(fx_converter.convert(curr_pv, curr_pv_ccy, base_currency))
    if prev_pr is not None:
        prev_pv = float(prev_pr.pv) * quantity
        prev_pv_ccy = prev_pr.currency
        if prev_pv_ccy != base_currency:
            prev_pv = float(fx_converter.convert(prev_pv, prev_pv_ccy, base_currency))
    else:
        prev_pv = 0.0
        notes.append("No previous price; using 0 as baseline.")
    if mode == "step":
        pnl = curr_pv - prev_pv
    elif mode == "cumulative":
        pnl = curr_pv - prev_pv  # For now, fallback to prev_pv if t0 not tracked
        notes.append("Cumulative mode fallback to prev_pv; t0 not tracked.")
    else:
        raise ValueError(f"Unknown PnLMode: {mode}")
    # Attribution
    delta = curr_pr.breakdown.get("delta", 0.0)
    theta = curr_pr.breakdown.get("theta", 0.0)
    vega = curr_pr.breakdown.get("vega", 0.0)
    gamma = curr_pr.breakdown.get("gamma", 0.0)
    # dS: spot change
    dS = 0.0
    if prev_snapshot is not None and hasattr(curr_snapshot, "get_spot") and hasattr(prev_snapshot, "get_spot"):
        try:
            curr_spot = curr_snapshot.get_spot(symbol)
            prev_spot = prev_snapshot.get_spot(symbol)
            dS = curr_spot - prev_spot
        except Exception:
            notes.append("Could not compute dS (spot change)")
    else:
        notes.append("No previous snapshot; dS=0")
    # dt (years)
    dt_years = 0.0
    if t_prev is not None and t_curr is not None:
        try:
            dt_years = float(t_curr) - float(t_prev)
        except Exception:
            notes.append("Could not compute dt_years; using 0.0")
    else:
        notes.append("No t_prev/t_curr; dt_years=0.0")
    # dIV (implied vol change)
    dIV = 0.0
    vega_in_breakdown = "vega" in curr_pr.breakdown
    prev_iv = None
    curr_iv = None
    if prev_snapshot is not None and hasattr(prev_snapshot, "get_iv"):
        try:
            prev_iv = prev_snapshot.get_iv(symbol)
        except Exception:
            prev_iv = None
    if curr_snapshot is not None and hasattr(curr_snapshot, "get_iv"):
        try:
            curr_iv = curr_snapshot.get_iv(symbol)
        except Exception:
            curr_iv = None
    vega_note_needed = False
    if vega_in_breakdown:
        if prev_iv is None or curr_iv is None:
            dIV = 0.0
            vega_note_needed = True
        else:
            try:
                dIV = float(curr_iv) - float(prev_iv)
            except Exception:
                dIV = 0.0
                vega_note_needed = True
        if dIV == 0.0:
            vega_note_needed = True
        if vega_note_needed:
            notes.append("dIV=0")
    delta_pnl = delta * dS * quantity
    theta_pnl = theta * dt_years * quantity
    vega_pnl = vega * dIV * quantity
    gamma_pnl = gamma * (dS ** 2) * quantity if gamma != 0.0 else 0.0
    components_sum = delta_pnl + theta_pnl + vega_pnl + gamma_pnl
    residual = pnl - components_sum
    attribution = PnLAttribution(
        delta_pnl=delta_pnl,
        theta_pnl=theta_pnl,
        vega_pnl=vega_pnl,
        gamma_pnl=gamma_pnl,
        residual=residual,
        notes=tuple(notes),
    )
    return PositionPnL(
        position_id=position_id,
        symbol=symbol,
        pv=curr_pv,
        pnl=pnl,
        attribution=attribution,
        currency=base_currency,
    )

def compute_portfolio_pnl(
    *,
    positions: Sequence[Any],
    prev_results: Mapping[str, PriceResult],
    curr_results: Mapping[str, PriceResult],
    prev_snapshot: Optional[MarketSnapshot],
    curr_snapshot: MarketSnapshot,
    base_currency: Currency,
    fx_converter: FxConverter,
    mode: PnLMode,
    t_prev: Any = None,
    t_curr: Any = None,
) -> PortfolioPnL:
    pos_pnls = []
    total_pv = 0.0
    total_pnl = 0.0
    for pos in positions:
        pos_id = getattr(pos, "id", getattr(pos, "symbol", "unknown"))
        symbol = getattr(pos, "symbol", "unknown")
        quantity = getattr(pos, "quantity", 0.0)
        prev_pr = prev_results.get(pos_id)
        curr_pr = curr_results.get(pos_id)
        if curr_pr is None:
            continue
        pos_pnl = compute_position_pnl(
            position_id=pos_id,
            symbol=symbol,
            prev_pr=prev_pr,
            curr_pr=curr_pr,
            prev_snapshot=prev_snapshot,
            curr_snapshot=curr_snapshot,
            quantity=quantity,
            base_currency=base_currency,
            fx_converter=fx_converter,
            mode=mode,
            t_prev=t_prev,
            t_curr=t_curr,
        )
        pos_pnls.append(pos_pnl)
        total_pv += pos_pnl.pv
        total_pnl += pos_pnl.pnl
    return PortfolioPnL(
        total_pv=total_pv,
        total_pnl=total_pnl,
        positions=tuple(pos_pnls),
        currency=base_currency,
    )


def compute_portfolio_theoretical_from_state(*, state: PortfolioStateV2, market_snapshot: MarketSnapshot, as_of_ts, fx_converter: FxConverter):
    """Wire a deterministic portfolio-level theoretical surface from a V2 portfolio state.

    Parameters
    - state: PortfolioStateV2 (required)
    - market_snapshot: MarketSnapshot (required)
    - as_of_ts: event timestamp (required) — must be provided by caller and is used as the deterministic as-of.
    - fx_converter: FxConverter for currency conversions

    Returns a dict with stable keys:
      {"as_of_ts": as_of_ts, "base_currency": ..., "pv": float, "greeks": {"delta":..., ...},
       "realized_pnl": 0.0, "unrealized_pnl": 0.0}

    Notes:
    - Realized PnL ledger/realization events are NOT implemented in this F6.2 slice; `realized_pnl` is 0.0.
    - This function is intentionally minimal: it delegates to `core.portfolio.v2_aggregation.aggregate_portfolio`.
    - Determinism: caller must pass `as_of_ts` (no defaults, no wall-clock usage).
    """
    if as_of_ts is None:
        raise ValueError("as_of_ts (event timestamp) is required and must be provided explicitly")

    totals = aggregate_portfolio_v2(state)

    # Convert greeks dataclass to a stable ordered mapping
    greeks_obj = totals.greeks
    greeks_map = {
        "delta": float(getattr(greeks_obj, "delta", 0.0)),
        "gamma": float(getattr(greeks_obj, "gamma", 0.0)),
        "vega": float(getattr(greeks_obj, "vega", 0.0)),
        "theta": float(getattr(greeks_obj, "theta", 0.0)),
        "rho": float(getattr(greeks_obj, "rho", 0.0)),
    }

    result = {
        "as_of_ts": as_of_ts,
        "base_currency": getattr(state, "base_currency", None),
        "pv": float(totals.pv),
        "greeks": tuple(sorted(greeks_map.items(), key=lambda kv: kv[0])),
        # Realized PnL not implemented in this slice
        "realized_pnl": 0.0,
        # Unrealized/theoretical PnL is not computed as delta vs prior in this minimal slice;
        # consumers can compute step/cumulative PnL using prior snapshots and this surface.
        "unrealized_pnl": 0.0,
    }
    return result
