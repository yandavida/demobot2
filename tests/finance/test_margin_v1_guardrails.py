from core.risk.snapshot import AggregatedGreeks, compute_risk_snapshot
from dataclasses import dataclass
from pytest import approx

@dataclass(frozen=True)
class DummyPosition:
    id: str
    pv: float
    greeks: AggregatedGreeks
    qty: float = 1.0
    contract_multiplier: float = 1.0
    notional: float = 0.0  # for FX

def test_non_negativity():
    pos = DummyPosition(id="A", pv=10, greeks=AggregatedGreeks(1,2,3,4), qty=1, contract_multiplier=1)
    snap = compute_risk_snapshot([pos])
    assert snap.margin.required >= 0

def test_determinism():
    pos = DummyPosition(id="B", pv=5, greeks=AggregatedGreeks(1,1,1,1), qty=2, contract_multiplier=1.5)
    snap1 = compute_risk_snapshot([pos])
    snap2 = compute_risk_snapshot([pos])
    assert snap1.margin.required == approx(snap2.margin.required)
    assert snap1.margin.components == snap2.margin.components

def test_permutation_invariance():
    pos1 = DummyPosition(id="X", pv=1, greeks=AggregatedGreeks(1,0,0,0), qty=1, contract_multiplier=1)
    pos2 = DummyPosition(id="Y", pv=2, greeks=AggregatedGreeks(0,1,0,0), qty=2, contract_multiplier=1)
    pos3 = DummyPosition(id="Z", pv=3, greeks=AggregatedGreeks(0,0,1,0), qty=3, contract_multiplier=1)
    positions = [pos1, pos2, pos3]
    snap1 = compute_risk_snapshot(positions)
    snap2 = compute_risk_snapshot(list(reversed(positions)))
    assert snap1.margin.required == approx(snap2.margin.required)
    assert snap1.margin.components == snap2.margin.components

def test_scaling_sanity():
    pos = DummyPosition(id="S", pv=10, greeks=AggregatedGreeks(2,3,4,0), qty=1, contract_multiplier=1, notional=100)
    snap1 = compute_risk_snapshot([pos])
    # scale everything by 2
    pos2 = DummyPosition(id="S", pv=10, greeks=AggregatedGreeks(2,3,4,0), qty=2, contract_multiplier=1, notional=100)
    snap2 = compute_risk_snapshot([pos2])
    # margin.required should not decrease
    assert snap2.margin.required >= snap1.margin.required
    # FX margin is exactly linear in notional
    fx1 = snap1.margin.components["fx"]
    fx2 = snap2.margin.components["fx"]
    assert fx2 == approx(2 * fx1)
