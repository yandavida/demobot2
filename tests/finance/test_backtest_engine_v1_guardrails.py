import pytest
from datetime import datetime, timedelta
from core.backtest import BacktestRequest, run_backtest_v1, build_backtest_hash_key
from core.marketdata.schemas import MarketSnapshot

class DummyPosition:
    def __init__(self, id, symbol):
        self.id = id
        self.symbol = symbol
    def __eq__(self, other):
        return isinstance(other, DummyPosition) and self.id == other.id and self.symbol == other.symbol
    def __hash__(self):
        return hash((self.id, self.symbol))
    def __repr__(self):
        return f"DummyPosition(id={self.id}, symbol={self.symbol})"

@pytest.fixture
def timeline():
    t0 = datetime(2025, 1, 1, 12, 0, 0)
    t1 = t0 + timedelta(days=1)
    snap0 = MarketSnapshot(
        asof=t0,
        spots={"AAPL": 100.0},
        vols={"AAPL": 0.2},
        rates={"USD": 0.03},
        divs={"AAPL": 0.01},
        fx_spots={},
        fx_forwards={},
    )
    snap1 = MarketSnapshot(
        asof=t1,
        spots={"AAPL": 101.0},
        vols={"AAPL": 0.21},
        rates={"USD": 0.03},
        divs={"AAPL": 0.01},
        fx_spots={},
        fx_forwards={},
    )
    return [snap0, snap1]

@pytest.fixture
def positions():
    return [DummyPosition(1, "AAPL"), DummyPosition(2, "AAPL")]

def test_determinism_and_permutation_invariance(timeline, positions):
    req1 = BacktestRequest(
        positions=positions,
        market_timeline=timeline,
        spot_shocks=[0.0],
        vol_shocks=[0.0],
        use_cache=True
    )
    req2 = BacktestRequest(
        positions=list(reversed(positions)),
        market_timeline=timeline,
        spot_shocks=[0.0],
        vol_shocks=[0.0],
        use_cache=True
    )
    res1 = run_backtest_v1(req1)
    res2 = run_backtest_v1(req2)
    assert res1.run_hash_key == res2.run_hash_key
    assert [(p.asof, p.scenario_hash_key, p.pnl_at_zero_shock) for p in res1.points] == [
        (p.asof, p.scenario_hash_key, p.pnl_at_zero_shock) for p in res2.points
    ]

def test_timeline_ordering_validation(positions):
    t0 = datetime(2025, 1, 1, 12, 0, 0)
    t1 = t0 + timedelta(days=1)
    snap0 = MarketSnapshot(
        asof=t1,
        spots={"AAPL": 100.0},
        vols={"AAPL": 0.2},
        rates={"USD": 0.03},
        divs={"AAPL": 0.01},
        fx_spots={},
        fx_forwards={},
    )
    snap1 = MarketSnapshot(
        asof=t0,
        spots={"AAPL": 101.0},
        vols={"AAPL": 0.21},
        rates={"USD": 0.03},
        divs={"AAPL": 0.01},
        fx_spots={},
        fx_forwards={},
    )
    req = BacktestRequest(
        positions=positions,
        market_timeline=[snap0, snap1],
        spot_shocks=[0.0],
        vol_shocks=[0.0],
        use_cache=True
    )
    with pytest.raises(ValueError):
        run_backtest_v1(req)

def test_zero_shock_invariant(timeline, positions):
    req = BacktestRequest(
        positions=positions,
        market_timeline=timeline,
        spot_shocks=[0.0],
        vol_shocks=[0.0],
        use_cache=False
    )
    res = run_backtest_v1(req)
    for pt in res.points:
        assert abs(pt.pnl_at_zero_shock) < 1e-8
