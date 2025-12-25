from __future__ import annotations
from typing import Sequence, Dict, Optional
from core.v2.models import V2Event
from core.portfolio.v2_models import PortfolioStateV2, PositionV2, LegV2, PortfolioConstraintsV2, Currency

def stable_sort_events(events: Sequence[V2Event]) -> list[V2Event]:
    return sorted(events, key=lambda e: (e.ts, e.event_id))

def reduce_portfolio_state(events: Sequence[V2Event]) -> Optional[PortfolioStateV2]:
    # Dedup strictly by event_id, stable sort
    seen = set()
    ordered_events = []
    for e in stable_sort_events(events):
        if e.event_id in seen:
            continue
        seen.add(e.event_id)
        ordered_events.append(e)

    state: Optional[PortfolioStateV2] = None
    positions: Dict[str, PositionV2] = {}
    base_currency: Optional[Currency] = None
    constraints: Optional[PortfolioConstraintsV2] = None

    for e in ordered_events:
        if e.type == "PORTFOLIO_CREATED":
            payload = e.payload or {}
            base_currency = payload.get("base_currency")
            constraints_dict = payload.get("constraints", {})
            constraints = PortfolioConstraintsV2(
                max_notional=constraints_dict.get("max_notional"),
                max_abs_delta=constraints_dict.get("max_abs_delta"),
                max_concentration_pct=constraints_dict.get("max_concentration_pct"),
            )
            positions = {}
        elif e.type == "PORTFOLIO_POSITION_UPSERTED":
            payload = e.payload or {}
            # Canonical: expect payload["position"]
            position_obj = payload.get("position")
            if isinstance(position_obj, dict):
                pos_id = position_obj.get("position_id") or position_obj.get("id")
                legs = position_obj.get("legs")
            else:
                # Fallback: legacy flat payload
                pos_id = payload.get("position_id") or payload.get("id")
                legs = payload.get("legs")
            if pos_id is None or legs is None:
                raise ValueError(f"PORTFOLIO_POSITION_UPSERTED missing position_id or legs (event_id={e.event_id})")
            # Optionally sort legs by leg_id for determinism if legs are dicts
            if isinstance(legs, list) and all(isinstance(l, dict) and "leg_id" in l for l in legs):
                legs = sorted(legs, key=lambda l: l["leg_id"])
            # Ensure greeks_per_unit is always a Greeks object
            def _leg_obj(leg):
                leg = dict(leg)
                g = leg.get("greeks_per_unit")
                if isinstance(g, dict):
                    from core.portfolio.v2_models import Greeks
                    leg["greeks_per_unit"] = Greeks(**g)
                return LegV2(**leg)
            legs_objs = tuple(_leg_obj(leg) for leg in legs)
            positions[pos_id] = PositionV2(position_id=pos_id, legs=legs_objs)
        elif e.type == "PORTFOLIO_POSITION_REMOVED":
            payload = e.payload or {}
            pos_id = payload.get("position_id")
            if pos_id in positions:
                positions.pop(pos_id)
        # Ignore all other event types

    if base_currency is None or constraints is None:
        return None
    return PortfolioStateV2(
        base_currency=base_currency,
        constraints=constraints,
        positions=dict(positions),
    )
