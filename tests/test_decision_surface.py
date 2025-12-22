from datetime import datetime

from core.arbitrage.models import ArbitrageOpportunity, ArbitrageLeg
from core.arbitrage.opportunity_space.ranking import (
    RankingConfig,
    ParetoDim,
    pareto_frontier,
    rank_execution_options,
    explain_ranking,
)


def _make_opp(id: str, buy_v: str, sell_v: str, buy_p: float, sell_p: float, size: float, as_of: datetime | None = None) -> ArbitrageOpportunity:
    buy = ArbitrageLeg(action="buy", venue=buy_v, price=buy_p, quantity=size)
    sell = ArbitrageLeg(action="sell", venue=sell_v, price=sell_p, quantity=size)
    opp = ArbitrageOpportunity(
        symbol="SYM",
        buy=buy,
        sell=sell,
        gross_edge=(sell_p - buy_p),
        net_edge=(sell_p - buy_p),
        edge_bps=((sell_p - buy_p) / buy_p) * 10_000,
        size=size,
        ccy="USD",
        notes=[],
        opportunity_id=id,
        as_of=as_of,
    )
    return opp


def test_pareto_and_ranking_determinism():
    now = datetime(2025, 1, 1, 0, 0, 0)
    # Construct options with clear dominance relationships
    opts = [
        _make_opp("A", "V1", "V2", 100.0, 102.0, 1.0, as_of=now),  # best edge
        _make_opp("B", "V1", "V2", 100.0, 101.5, 1.0, as_of=now),
        _make_opp("C", "V1", "V2", 100.5, 101.6, 1.0, as_of=now),
        _make_opp("D", "V1", "V2", 99.0, 100.0, 1.0, as_of=now),
        _make_opp("E", "V1", "V2", 100.0, 101.0, 2.0, as_of=now),
    ]

    cfg = RankingConfig(
        max_results=10,
        pareto_dimensions=(
            ParetoDim("edge_bps", "max", 1.0),
            ParetoDim("size", "max", 1.0),
        ),
        tie_break=("edge_bps", "size", "notional"),
        epsilon={"edge_bps": 1e-6, "size": 1e-9},
    )

    # Frontier should contain non-dominated items (A and E likely)
    frontier = pareto_frontier(opts, cfg)
    frontier_ids = [o.opportunity_id for o in frontier]
    assert set(frontier_ids)  # non-empty

    # Ranking determinsim: shuffle inputs and expect same ranked order
    ranked1 = [o.opportunity_id for o in rank_execution_options(opts, cfg)]
    shuffled = list(reversed(opts))
    ranked2 = [o.opportunity_id for o in rank_execution_options(shuffled, cfg)]
    assert ranked1 == ranked2


def test_tie_break_and_epsilon_behavior():
    now = datetime(2025, 1, 1, 0, 0, 0)
    # Two options identical within epsilon on edge_bps
    o1 = _make_opp("T1", "V", "W", 100.0, 101.0, 1.0, as_of=now)
    o2 = _make_opp("T2", "V", "W", 100.0, 101.00000005, 1.0, as_of=now)

    cfg = RankingConfig(
        max_results=10,
        pareto_dimensions=(ParetoDim("edge_bps", "max", 1.0),),
        tie_break=("edge_bps", "notional"),
        epsilon={"edge_bps": 1e-5},
    )

    ranked = rank_execution_options([o1, o2], cfg)
    # within epsilon they should be considered equal; tie-break by notional then id
    assert len(ranked) == 2
    # Ensure deterministic order regardless of input order
    r1 = [o.opportunity_id for o in rank_execution_options([o1, o2], cfg)]
    r2 = [o.opportunity_id for o in rank_execution_options([o2, o1], cfg)]
    assert r1 == r2


def test_explain_ranking_payload_and_no_now_usage():
    now = datetime(2025, 1, 1, 0, 0, 0)
    o1 = _make_opp("X", "V", "W", 100.0, 101.0, 1.0, as_of=now)
    o2 = _make_opp("Y", "V", "W", 100.0, 100.5, 1.0, as_of=now)

    cfg = RankingConfig(
        max_results=10,
        pareto_dimensions=(ParetoDim("edge_bps", "max", 1.0),),
        tie_break=("edge_bps",),
        epsilon={"edge_bps": 1e-9},
    )

    report = explain_ranking([o1, o2], cfg)
    assert "frontier_ids" in report and "ranked_ids" in report
    assert isinstance(report["dominance_reasons"], dict)

    # Guard: ensure module does not use datetime.now/utcnow/time.time
    import os

    path = os.path.join("core", "arbitrage", "opportunity_space", "ranking.py")
    txt = open(path, "r", encoding="utf-8").read()
    assert "now(" not in txt
    assert "utcnow" not in txt
    assert "time.time" not in txt
