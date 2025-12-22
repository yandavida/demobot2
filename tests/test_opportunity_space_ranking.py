from core.arbitrage.opportunity_space.ranking import (
    RankingConfig,
    ParetoDim,
    pareto_frontier,
    dominates,
    rank_execution_options,
    explain_ranking,
)
from core.arbitrage.models import ArbitrageOpportunity, ArbitrageLeg


def _make_opp(id_suffix: str, buy_p: float, sell_p: float, size: float, as_of=None):
    buy = ArbitrageLeg(action="buy", venue="V", price=buy_p, quantity=size)
    sell = ArbitrageLeg(action="sell", venue="W", price=sell_p, quantity=size)
    opp = ArbitrageOpportunity(
        symbol="S",
        buy=buy,
        sell=sell,
        gross_edge=(sell_p - buy_p),
        net_edge=(sell_p - buy_p),
        edge_bps=((sell_p - buy_p) / buy_p) * 10_000,
        size=size,
        ccy="USD",
        notes=[],
        opportunity_id=f"opp-{id_suffix}",
        as_of=as_of,
    )
    return opp


def test_dominance_and_frontier():
    cfg = RankingConfig(
        max_results=10,
        pareto_dimensions=(ParetoDim("edge_bps", "max"), ParetoDim("notional", "max")),
        tie_break=("edge_bps", "notional"),
        epsilon={"edge_bps": 1e-6, "notional": 1e-6},
    )

    # Create options with clear dominance relations
    a = _make_opp("a", 100.0, 102.0, 10.0)  # strong edge, notional 1000
    b = _make_opp("b", 100.0, 101.0, 10.0)  # weaker edge
    c = _make_opp("c", 90.0, 95.0, 20.0)    # weaker edge but larger notional
    d = _make_opp("d", 80.0, 85.0, 5.0)     # dominated

    options = [a, b, c, d]

    frontier = pareto_frontier(options, cfg)
    frontier_ids = [o.opportunity_id for o in frontier]

    # Expected frontier contains c and d (non-dominated given edge and notional)
    assert set(frontier_ids) == {"opp-c", "opp-d"}

    # Dominance checks
    assert dominates(a, b, cfg) is True
    assert dominates(b, a, cfg) is False

    ranked = rank_execution_options(options, cfg)
    ranked_ids = [o.opportunity_id for o in ranked]
    # deterministic ranking: first ranked item should be from frontier
    assert ranked_ids[0] in frontier_ids


def test_epsilon_tolerance_and_determinism():
    cfg = RankingConfig(
        max_results=10,
        pareto_dimensions=(ParetoDim("edge_bps", "max"),),
        tie_break=("edge_bps",),
        epsilon={"edge_bps": 1e-2},
    )

    base = _make_opp("x", 100.0, 102.0, 1.0)
    noisy = _make_opp("y", 100.0, 102.0000001, 1.0)

    # within epsilon: treat equal
    assert dominates(base, noisy, cfg) is False
    assert dominates(noisy, base, cfg) is False

    # Deterministic ordering irrespective of input order
    ordered1 = rank_execution_options([base, noisy], cfg)
    ordered2 = rank_execution_options([noisy, base], cfg)
    assert [o.opportunity_id for o in ordered1] == [o.opportunity_id for o in ordered2]


def test_explain_ranking_payload():
    cfg = RankingConfig(
        max_results=10,
        pareto_dimensions=(ParetoDim("edge_bps", "max"), ParetoDim("notional", "max")),
        tie_break=("edge_bps", "notional"),
        epsilon={"edge_bps": 1e-6, "notional": 1e-6},
    )

    a = _make_opp("a", 100.0, 103.0, 10.0)
    b = _make_opp("b", 100.0, 101.0, 10.0)
    c = _make_opp("c", 90.0, 95.0, 20.0)

    report = explain_ranking([a, b, c], cfg)
    assert "frontier_ids" in report and "ranked_ids" in report and "dominance_reasons" in report
    # dominated item b should have an entry in dominance_reasons
    assert "opp-b" in report["dominance_reasons"]
