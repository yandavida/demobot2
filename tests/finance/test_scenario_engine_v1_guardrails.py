import pytest
from core.scenario.schemas import ScenarioMarketInputs, ScenarioRequest
from core.scenario.engine import compute_scenario

# Dummy position for permutation invariance (replace with real if available)
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
def base_market():
    return ScenarioMarketInputs(
        spot_by_symbol={"AAPL": 100.0},
        vol_by_symbol={"AAPL": 0.2},
        rate_by_symbol_or_ccy={},
        div_by_symbol={},
        fx_forward_by_pair={}
    )

@pytest.fixture
def base_positions():
    return [DummyPosition(1, "AAPL"), DummyPosition(2, "AAPL")]

@pytest.mark.parametrize("spot_shocks,vol_shocks", [([0.0, 0.1], [0.0, 0.05])])
def test_determinism_and_permutation_invariance(base_market, base_positions, spot_shocks, vol_shocks):
    req1 = ScenarioRequest(
        positions=base_positions,
        market=base_market,
        spot_shocks=spot_shocks,
        vol_shocks=vol_shocks,
        use_cache=True
    )
    req2 = ScenarioRequest(
        positions=list(reversed(base_positions)),
        market=base_market,
        spot_shocks=list(spot_shocks),
        vol_shocks=list(vol_shocks),
        use_cache=True
    )
    resp1 = compute_scenario(req1)
    resp2 = compute_scenario(req2)
    assert resp1.hash_key == resp2.hash_key
    assert resp1.points == resp2.points


def test_zero_shock_pnl_zero(base_market, base_positions):
    req = ScenarioRequest(
        positions=base_positions,
        market=base_market,
        spot_shocks=[0.0],
        vol_shocks=[0.0],
        use_cache=False
    )
    resp = compute_scenario(req)
    assert len(resp.points) == 1
    pt = resp.points[0]
    assert pt.spot_shock == 0.0 and pt.vol_shock == 0.0
    assert abs(pt.pnl) < 1e-8
    assert all(abs(v) < 1e-8 for v in pt.components.values())


def test_cache_hit_semantics(base_market, base_positions):
    req = ScenarioRequest(
        positions=base_positions,
        market=base_market,
        spot_shocks=[0.0],
        vol_shocks=[0.0],
        use_cache=True
    )
    resp1 = compute_scenario(req)
    resp2 = compute_scenario(req)
    assert not resp1.cache_hit
    assert resp2.cache_hit
