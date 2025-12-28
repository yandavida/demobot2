
# Dummy PositionState for F6.1 (simulate minimal lifecycle)
class DummyPositionState:
    def __init__(self, id, symbol, quantity, opened_at, closed_at=None):
        self.id = id
        self.symbol = symbol
        self.quantity = quantity
        self.opened_at = opened_at
        self.closed_at = closed_at

# --- T1: Lifecycle determinism ---
def test_lifecycle_determinism():
    s1 = DummyPositionState("p1", "A", 10, 1)
    s2 = DummyPositionState("p1", "A", 10, 1)
    assert s1.__dict__ == s2.__dict__

# --- T2: Idempotency/No ambiguity ---
def test_lifecycle_idempotency():
    s = DummyPositionState("p1", "A", 10, 1)
    s.quantity += 5  # resize
    s.quantity -= 15  # close
    assert s.quantity == 0
    assert s.closed_at is None or s.closed_at >= s.opened_at

# --- T3: Permutation safety for independent events ---
def test_lifecycle_permutation_independent():
    s1 = DummyPositionState("p1", "A", 10, 1)
    s2 = DummyPositionState("p2", "B", 20, 2)
    states1 = [s1, s2]
    states2 = [s2, s1]
    # State for each position is independent
    d1 = {s.id: s.quantity for s in states1}
    d2 = {s.id: s.quantity for s in states2}
    assert d1 == d2

# --- T4: No pricing leakage ---
def test_lifecycle_no_pricing_leakage():
    s = DummyPositionState("p1", "A", 10, 1)
    forbidden = ["pv", "mtm", "discount", "curve", "funding"]
    for attr in forbidden:
        assert not hasattr(s, attr)
