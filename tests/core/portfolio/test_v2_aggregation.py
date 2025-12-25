from core.portfolio.v2_models import PortfolioStateV2, PositionV2, LegV2, Greeks, PortfolioConstraintsV2
from core.portfolio.v2_aggregation import aggregate_portfolio
from core.portfolio.v2_constraints import evaluate_constraints

def make_state():
    legs1 = (
        LegV2(
            leg_id="l1",
            underlying="AAPL",
            pv_per_unit=2.0,
            greeks_per_unit=Greeks(1.0, 0.0, 0.0, 0.0, 0.0),
            notional_per_unit=100.0,
            quantity=2.0,
        ),
        LegV2(
            leg_id="l2",
            underlying="AAPL",
            pv_per_unit=1.0,
            greeks_per_unit=Greeks(0.5, 0.0, 0.0, 0.0, 0.0),
            notional_per_unit=50.0,
            quantity=-1.0,
        ),
    )
    legs2 = (
        LegV2(
            leg_id="l3",
            underlying="GOOG",
            pv_per_unit=3.0,
            greeks_per_unit=Greeks(2.0, 0.0, 0.0, 0.0, 0.0),
            notional_per_unit=200.0,
            quantity=1.0,
        ),
    )
    pos1 = PositionV2(position_id="p1", legs=legs1)
    pos2 = PositionV2(position_id="p2", legs=legs2)
    constraints = PortfolioConstraintsV2(max_notional=500.0, max_abs_delta=5.0, max_concentration_pct=60.0)
    return PortfolioStateV2(base_currency="USD", constraints=constraints, positions={"p1": pos1, "p2": pos2})

def test_sum_invariants():
    state = make_state()
    totals = aggregate_portfolio(state)
    # PV = 2*2 + 1*(-1) + 3*1 = 4 - 1 + 3 = 6
    assert totals.pv == 6.0
    # Delta = 2*1.0 + (-1)*0.5 + 1*2.0 = 2 - 0.5 + 2 = 3.5
    assert abs(totals.greeks.delta - 3.5) < 1e-8

def test_commutativity():
    state = make_state()
    # Swap positions
    state2 = PortfolioStateV2(
        base_currency=state.base_currency,
        constraints=state.constraints,
        positions={"p2": state.positions["p2"], "p1": state.positions["p1"]},
    )
    t1 = aggregate_portfolio(state)
    t2 = aggregate_portfolio(state2)
    assert t1 == t2

def test_concentration_breach():
    state = make_state()
    totals = aggregate_portfolio(state)
    report = evaluate_constraints(state, totals)
    # AAPL: abs_notional = 2*100 + 1*50 = 200 + 50 = 250
    # GOOG: abs_notional = 1*200 = 200
    # total = 250 + 200 = 450
    # AAPL: 250/450 ~ 55.56%, GOOG: 200/450 ~ 44.44%
    # max_concentration_pct=60, so no breach
    assert report.passed
    # Now set max_concentration_pct=50 to force breach
    state2 = PortfolioStateV2(
        base_currency=state.base_currency,
        constraints=PortfolioConstraintsV2(max_notional=500.0, max_abs_delta=5.0, max_concentration_pct=50.0),
        positions=state.positions,
    )
    totals2 = aggregate_portfolio(state2)
    report2 = evaluate_constraints(state2, totals2)
    assert not report2.passed
    assert any(b.rule == "max_concentration_pct" for b in report2.breaches)

def test_deterministic_ordering():
    state = make_state()
    totals = aggregate_portfolio(state)
    exposures = totals.exposures
    # Should be sorted by underlying
    assert [u for u, _ in exposures] == sorted([u for u, _ in exposures])
    # Breaches sorted by (rule, underlying)
    state2 = PortfolioStateV2(
        base_currency=state.base_currency,
        constraints=PortfolioConstraintsV2(max_notional=300.0, max_abs_delta=1.0, max_concentration_pct=50.0),
        positions=state.positions,
    )
    totals2 = aggregate_portfolio(state2)
    report = evaluate_constraints(state2, totals2)
    rules = [(b.rule, b.underlying or "") for b in report.breaches]
    assert rules == sorted(rules)
