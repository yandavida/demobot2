from core.arbitrage.intelligence.scoring import score_signals


def test_score_monotonicity_with_net_edge() -> None:
    signals_low = {"net_edge_bps": 1.0, "edge_bps_stability": 1.0, "freshness_ms": 0}
    signals_high = {"net_edge_bps": 10.0, "edge_bps_stability": 1.0, "freshness_ms": 0}
    assert score_signals(signals_high) > score_signals(signals_low)


def test_score_penalizes_stale_quotes() -> None:
    fresh = {"net_edge_bps": 5.0, "edge_bps_stability": 1.0, "freshness_ms": 0}
    stale = {"net_edge_bps": 5.0, "edge_bps_stability": 1.0, "freshness_ms": 60_000}
    assert score_signals(fresh) > score_signals(stale)
