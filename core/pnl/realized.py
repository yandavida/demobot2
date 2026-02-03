from __future__ import annotations

from typing import Any, Dict
from datetime import datetime

from core.portfolio.v2_models import PortfolioStateV2
from core.v2.models import V2Event
from core.fx.converter import FxConverter


def compute_realized_pnl_from_close(
    *,
    state_before: PortfolioStateV2,
    close_event: V2Event,
    market_snapshot,
    as_of_ts: datetime,
    fx_converter: FxConverter,
) -> float:
    """Compute deterministic realized PnL for a full close event.

        Rules:
        - `as_of_ts` is required and must equal `close_event.ts`.
        - If the event is not a `PORTFOLIO_POSITION_REMOVED`, return 0.0.
        - Position entry PVs are taken from `state_before`'s `PositionV2.legs[*].pv_per_unit` unless
            the close event payload carries an explicit `entry_pv` per leg.
        - Exit PVs are expected in `close_event.payload["legs"]` as list of dicts with `leg_id` and `pv_per_unit`.
        - Realized PnL = sum_over_legs( (exit_pv - entry_pv) * leg.quantity ).
        - Function is pure and does not modify state.

        Notes on fallback behavior:
        - The canonical source for `entry_pv` is an event-supplied trade record (i.e., the
            `entry_pv` value carried in the close event payload). When present, that value
            takes precedence and is treated as the audited trade entry price.
        - If `entry_pv` is absent in the event payload, this function falls back to the
            in-memory `state_before` `LegV2.pv_per_unit`. This fallback is a compatibility
            mode to support legacy callers and may differ from an audited trade record.
            Consumers that require ledger-grade provenance MUST supply `entry_pv` in the event.
    """
    if as_of_ts is None:
        raise ValueError("as_of_ts is required and must be provided explicitly")
    if close_event.ts != as_of_ts:
        raise ValueError("close_event.ts must equal as_of_ts")

    if close_event.type != "PORTFOLIO_POSITION_REMOVED":
        return 0.0

    payload: Dict[str, Any] = close_event.payload or {}
    pos_id = payload.get("position_id")
    if pos_id is None:
        return 0.0

    pos = state_before.positions.get(pos_id)
    if pos is None:
        return 0.0

    # Build exit map from event payload; support optional entry_pv carried by the event
    exit_legs = payload.get("legs") or []
    exit_map: Dict[str, Dict[str, float]] = {}
    for l in exit_legs:
        lid = l.get("leg_id")
        if lid is None:
            continue
        exit_map[lid] = {
            "exit_pv": float(l.get("pv_per_unit", 0.0)),
            # allow event to carry entry_pv (e.g., trade record) which takes precedence
            "entry_pv": float(l.get("entry_pv")) if l.get("entry_pv") is not None else None,
            "quantity": float(l.get("quantity", 0.0)),
        }

    realized = 0.0
    for leg in pos.legs:
        # Prefer entry_pv supplied by the event payload if present; otherwise use state
        entry_override = None
        if leg.leg_id in exit_map:
            entry_override = exit_map[leg.leg_id].get("entry_pv")
        entry_pv = float(entry_override) if entry_override is not None else float(getattr(leg, "pv_per_unit", 0.0))
        qty = float(getattr(leg, "quantity", 0.0))
        exit_pv = exit_map.get(leg.leg_id, {}).get("exit_pv", entry_pv)
        realized += (exit_pv - entry_pv) * qty

    return float(realized)
