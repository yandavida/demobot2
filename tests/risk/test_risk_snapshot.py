from core.risk.snapshot import AggregatedGreeks, compute_risk_snapshot
from dataclasses import dataclass

@dataclass(frozen=True)
class DummyPosition:
    id: str
    pv: float
    greeks: AggregatedGreeks
    qty: float = 1.0
    contract_multiplier: float = 1.0

# Helper for canonical greeks
CANONICAL = AggregatedGreeks(delta=2.0, gamma=0.5, vega=1.0, theta=-0.2)


def test_linearity_qty():
    pos = DummyPosition(id="A", pv=100.0, greeks=CANONICAL, qty=2.0)
    snap = compute_risk_snapshot([pos])
    assert snap.pv == 200.0
    assert snap.greeks.delta == 4.0
    assert snap.greeks.gamma == 1.0
    assert snap.greeks.vega == 2.0
    assert snap.greeks.theta == -0.4

def test_linearity_contract_multiplier():
    pos = DummyPosition(id="B", pv=50.0, greeks=CANONICAL, contract_multiplier=3.0)
    snap = compute_risk_snapshot([pos])
    from pytest import approx
    assert snap.pv == approx(150.0)
    assert snap.greeks.delta == approx(6.0)
    assert snap.greeks.gamma == approx(1.5)
    assert snap.greeks.vega == approx(3.0)
    assert snap.greeks.theta == approx(-0.6)

def test_permutation_invariance():
    pos1 = DummyPosition(id="X", pv=10.0, greeks=CANONICAL, qty=1.0)
    pos2 = DummyPosition(id="Y", pv=20.0, greeks=CANONICAL, qty=2.0)
    snap1 = compute_risk_snapshot([pos1, pos2])
    snap2 = compute_risk_snapshot([pos2, pos1])
    assert snap1 == snap2

def test_unit_preservation():
    pos = DummyPosition(id="U", pv=1.0, greeks=AggregatedGreeks(delta=0.0, gamma=0.0, vega=1.0, theta=-1.0), qty=1.0)
    snap = compute_risk_snapshot([pos])
    # vega must remain per +1% IV, theta per day
    assert snap.greeks.vega == 1.0
    assert snap.greeks.theta == -1.0
    # No normalization or scaling beyond qty*contract_multiplier
