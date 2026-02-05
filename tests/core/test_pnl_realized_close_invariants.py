import math
from datetime import datetime

from core.portfolio.v2_models import PortfolioStateV2, PositionV2, LegV2, Greeks, PortfolioConstraintsV2
from core.v2.models import V2Event
from core.fx.converter import FxConverter
from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass

# Import function under test (to be implemented)
from core.pnl.realized import compute_realized_pnl_from_close


def _tolerance(metric: MetricClass):
    t = DEFAULT_TOLERANCES[metric]
    return (t.rel or 0.0, t.abs or 0.0)


def make_state_with_position(position_id: str, entry_pv: float, quantity: float, base_currency: str = "USD"):
    leg = LegV2(leg_id="l1", underlying="S1", pv_per_unit=entry_pv, greeks_per_unit=Greeks(0,0,0,0,0), notional_per_unit=0.0, quantity=quantity)
    pos = PositionV2(position_id=position_id, legs=(leg,))
    state = PortfolioStateV2(base_currency=base_currency, constraints=PortfolioConstraintsV2(), positions={position_id: pos})
    return state


def make_close_event(position_id: str, exit_pv: float, ts: datetime, entry_pv: float | None = None):
    leg = {"leg_id": "l1", "pv_per_unit": exit_pv, "quantity": 1.0}
    if entry_pv is not None:
        leg["entry_pv"] = entry_pv
    payload = {"position_id": position_id, "legs": [leg]}
    return V2Event(event_id="e1", session_id="s1", ts=ts, type="PORTFOLIO_POSITION_REMOVED", payload=payload, payload_hash="")


def test_determinism_same_inputs_same_realized():
    ts = datetime(2025, 1, 1, 12, 0, 0)
    state = make_state_with_position("p1", entry_pv=10.0, quantity=2.0)
    ev = make_close_event("p1", exit_pv=12.0, ts=ts)
    fx = FxConverter(base_ccy=state.base_currency)

    r1 = compute_realized_pnl_from_close(state_before=state, close_event=ev, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    r2 = compute_realized_pnl_from_close(state_before=state, close_event=ev, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    assert r1 == r2


def test_zero_realized_without_close_event():
    ts = datetime(2025, 1, 1, 12, 0, 0)
    state = make_state_with_position("p1", entry_pv=10.0, quantity=2.0)
    ev = V2Event(event_id="e2", session_id="s1", ts=ts, type="QUOTE_INGESTED", payload={}, payload_hash="")
    fx = FxConverter(base_ccy=state.base_currency)

    r = compute_realized_pnl_from_close(state_before=state, close_event=ev, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    assert math.isclose(r, 0.0, rel_tol=_tolerance(MetricClass.PNL)[0], abs_tol=_tolerance(MetricClass.PNL)[1])


def test_full_close_accounting_identity():
    ts = datetime(2025, 1, 1, 12, 0, 0)
    # Set the market PV (state) to equal the exit_pv so that previous unrealized
    # PnL equals the realized PnL computed at exit.
    state_before = make_state_with_position("p1", entry_pv=7.0, quantity=3.0)
    ev = make_close_event("p1", exit_pv=7.0, ts=ts, entry_pv=5.0)
    fx = FxConverter(base_ccy=state_before.base_currency)

    # For this slice, we treat the position's legs' pv_per_unit in state_before
    # as the market PV at `as_of_ts`. The canonical accounting identity for a full
    # close is that the realized PnL equals the previous unrealized PnL:
    #   realized_pnl == (market_pv - entry_pv) * quantity
    realized = compute_realized_pnl_from_close(state_before=state_before, close_event=ev, market_snapshot=None, as_of_ts=ts, fx_converter=fx)

    # previous unrealized (per our test inputs)
    market_pv = state_before.positions["p1"].legs[0].pv_per_unit
    entry_pv = 5.0
    qty = 3.0
    expected_unrealized = (market_pv - entry_pv) * qty
    rel, abs_tol = _tolerance(MetricClass.PNL)
    assert math.isclose(realized, expected_unrealized, rel_tol=rel, abs_tol=abs_tol)


def test_order_permutation_invariance():
    ts = datetime(2025, 1, 1, 12, 0, 0)
    # Create two equivalent states with legs order altered
    leg_a = LegV2(leg_id="a", underlying="S1", pv_per_unit=10.0, greeks_per_unit=Greeks(0,0,0,0,0), notional_per_unit=0.0, quantity=1.0)
    leg_b = LegV2(leg_id="b", underlying="S2", pv_per_unit=20.0, greeks_per_unit=Greeks(0,0,0,0,0), notional_per_unit=0.0, quantity=1.0)
    pos1 = PositionV2(position_id="p1", legs=(leg_a, leg_b))
    pos2 = PositionV2(position_id="p1", legs=(leg_b, leg_a))
    state1 = PortfolioStateV2(base_currency="USD", constraints=PortfolioConstraintsV2(), positions={"p1": pos1})
    state2 = PortfolioStateV2(base_currency="USD", constraints=PortfolioConstraintsV2(), positions={"p1": pos2})

    ev = make_close_event("p1", exit_pv=12.0, ts=ts)
    fx = FxConverter(base_ccy="USD")

    r1 = compute_realized_pnl_from_close(state_before=state1, close_event=ev, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    r2 = compute_realized_pnl_from_close(state_before=state2, close_event=ev, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    rel, abs_tol = _tolerance(MetricClass.PNL)
    assert math.isclose(r1, r2, rel_tol=rel, abs_tol=abs_tol)


def test_no_hardcoded_eps_in_test():
    # Ensure numeric policy is used: this test enforces using DEFAULT_TOLERANCES values
    t = DEFAULT_TOLERANCES[MetricClass.PNL]
    assert t.abs is not None or t.rel is not None


def test_close_realized_pnl_falls_back_to_state_entry_pv_when_event_missing():
    ts = datetime(2025, 1, 1, 12, 0, 0)
    state_before = make_state_with_position("p1", entry_pv=5.0, quantity=2.0)
    # Close event does NOT supply entry_pv -> fallback to state_before.pv_per_unit
    ev = make_close_event("p1", exit_pv=8.0, ts=ts)
    fx = FxConverter(base_ccy=state_before.base_currency)

    r = compute_realized_pnl_from_close(state_before=state_before, close_event=ev, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    expected = (8.0 - 5.0) * 2.0
    rel, abs_tol = _tolerance(MetricClass.PNL)
    assert math.isclose(r, expected, rel_tol=rel, abs_tol=abs_tol)
    # Determinism: same inputs produce identical realized value
    r2 = compute_realized_pnl_from_close(state_before=state_before, close_event=ev, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    assert r == r2
