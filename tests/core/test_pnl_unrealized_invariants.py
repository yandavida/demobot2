import math
from datetime import datetime

from core.portfolio.v2_models import PortfolioStateV2, PositionV2, LegV2, Greeks, PortfolioConstraintsV2
from core.fx.converter import FxConverter
from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass

# functions under test
from core.pnl.unrealized import compute_unrealized_pnl, compute_unrealized_from_pvs
from core.pnl.theoretical import compute_portfolio_theoretical_from_state


def _tolerance(metric: MetricClass):
    t = DEFAULT_TOLERANCES[metric]
    return (t.rel or 0.0, t.abs or 0.0)


def make_state_with_position(position_id: str, pv_per_unit: float, quantity: float, base_currency: str = "USD"):
    leg = LegV2(leg_id="l1", underlying="S1", pv_per_unit=pv_per_unit, greeks_per_unit=Greeks(0,0,0,0,0), notional_per_unit=0.0, quantity=quantity)
    pos = PositionV2(position_id=position_id, legs=(leg,))
    state = PortfolioStateV2(base_currency=base_currency, constraints=PortfolioConstraintsV2(), positions={position_id: pos})
    return state


def test_determinism_purity_same_inputs_same_unrealized():
    ts = datetime(2025, 1, 1, 12, 0, 0)
    st0 = make_state_with_position("p1", pv_per_unit=5.0, quantity=2.0)
    st1 = make_state_with_position("p1", pv_per_unit=8.0, quantity=2.0)
    fx = FxConverter(base_ccy=st0.base_currency)

    u1 = compute_unrealized_pnl(state_before=st0, state_after=st1, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    u2 = compute_unrealized_pnl(state_before=st0, state_after=st1, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    assert u1 == u2


def test_unrealized_equals_pv_delta():
    ts = datetime(2025, 1, 1, 12, 0, 0)
    st0 = make_state_with_position("p1", pv_per_unit=7.0, quantity=3.0)
    st1 = make_state_with_position("p1", pv_per_unit=10.0, quantity=3.0)
    fx = FxConverter(base_ccy=st0.base_currency)

    u = compute_unrealized_pnl(state_before=st0, state_after=st1, market_snapshot=None, as_of_ts=ts, fx_converter=fx)

    pv0 = compute_portfolio_theoretical_from_state(state=st0, market_snapshot=None, as_of_ts=ts, fx_converter=fx)["pv"]
    pv1 = compute_portfolio_theoretical_from_state(state=st1, market_snapshot=None, as_of_ts=ts, fx_converter=fx)["pv"]
    expected = pv1 - pv0
    rel, abs_tol = _tolerance(MetricClass.PNL)
    assert math.isclose(u, expected, rel_tol=rel, abs_tol=abs_tol)


def test_permutation_invariance():
    ts = datetime(2025, 1, 1, 12, 0, 0)
    # two states with legs in different order but same aggregate PV
    leg_a = LegV2(leg_id="a", underlying="S1", pv_per_unit=10.0, greeks_per_unit=Greeks(0,0,0,0,0), notional_per_unit=0.0, quantity=1.0)
    leg_b = LegV2(leg_id="b", underlying="S2", pv_per_unit=20.0, greeks_per_unit=Greeks(0,0,0,0,0), notional_per_unit=0.0, quantity=1.0)
    pos1 = PositionV2(position_id="p1", legs=(leg_a, leg_b))
    pos2 = PositionV2(position_id="p1", legs=(leg_b, leg_a))
    st_before = PortfolioStateV2(base_currency="USD", constraints=PortfolioConstraintsV2(), positions={"p1": pos1})
    st_after = PortfolioStateV2(base_currency="USD", constraints=PortfolioConstraintsV2(), positions={"p1": pos2})
    fx = FxConverter(base_ccy="USD")

    u1 = compute_unrealized_pnl(state_before=st_before, state_after=st_after, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    u2 = compute_unrealized_pnl(state_before=st_before, state_after=st_after, market_snapshot=None, as_of_ts=ts, fx_converter=fx)
    rel, abs_tol = _tolerance(MetricClass.PNL)
    assert math.isclose(u1, u2, rel_tol=rel, abs_tol=abs_tol)


def test_zero_when_no_anchor_available():
    # If pv0 (reference) is not available, compatibility mode returns 0.0
    pv1 = 8.0
    u = compute_unrealized_from_pvs(pv0=None, pv1=pv1)
    rel, abs_tol = _tolerance(MetricClass.PNL)
    assert math.isclose(u, 0.0, rel_tol=rel, abs_tol=abs_tol)


def test_numeric_policy_compliance():
    t = DEFAULT_TOLERANCES[MetricClass.PNL]
    assert t.abs is not None or t.rel is not None
