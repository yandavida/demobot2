from datetime import datetime
from core.scenario.schemas import ScenarioRequest
from core.scenario.engine import compute_scenario
from core.marketdata.schemas import Quote
from core.marketdata.adapters import build_market_snapshot_v1

def make_snapshot(spot=100.0):
    quotes = [
        Quote(kind="spot", key="AAPL", value=spot),
        Quote(kind="vol", key="AAPL", value=0.2),
        Quote(kind="rate", key="USD", value=0.03),
        Quote(kind="div", key="AAPL", value=0.01),
    ]
    return build_market_snapshot_v1(datetime(2025, 1, 1, 12, 0, 0), quotes)

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

def test_market_fingerprint_affects_cache_key():
    positions = [DummyPosition(1, "AAPL")]
    req1 = ScenarioRequest(
        positions=positions,
        market=make_snapshot(spot=100.0),
        spot_shocks=[0.0],
        vol_shocks=[0.0],
        use_cache=False
    )
    req2 = ScenarioRequest(
        positions=positions,
        market=make_snapshot(spot=101.0),
        spot_shocks=[0.0],
        vol_shocks=[0.0],
        use_cache=False
    )
    resp1 = compute_scenario(req1)
    resp2 = compute_scenario(req2)
    assert resp1.hash_key != resp2.hash_key
