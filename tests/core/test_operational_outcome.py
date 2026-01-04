from core.validation.operational_outcome import map_classification_to_outcome, ErrorEnvelope

def test_new_accepted():
    identity = ("sess1", "cmdA")
    state_hash = "abc123"
    out = map_classification_to_outcome("NEW", identity, state_hash)
    assert out.status == "ACCEPTED"
    assert out.error is None
    assert out.state_hash == state_hash

def test_idempotent_replay():
    identity = ("sess1", "cmdA")
    state_hash = "xyz789"
    out = map_classification_to_outcome("IDEMPOTENT_REPLAY", identity, state_hash)
    assert out.status == "IDEMPOTENT_REPLAY"
    assert out.error is None
    assert out.state_hash == state_hash

def test_conflict_rejected():
    identity = ("sess1", "cmdA")
    state_hash = "zzz111"
    out = map_classification_to_outcome("CONFLICT", identity, state_hash)
    assert out.status == "REJECTED"
    assert isinstance(out.error, ErrorEnvelope)
    assert out.error.category == "CONFLICT"
    assert out.error.code == "IDEMPOTENCY_CONFLICT"
    assert out.error.message == "command conflicts with previous execution"
    assert out.error.error_count == 1
    assert out.state_hash == state_hash

def test_state_hash_passthrough():
    identity = ("sess1", "cmdA")
    state_hash = "hashval"
    out = map_classification_to_outcome("NEW", identity, state_hash)
    assert out.state_hash == state_hash

def test_determinism():
    identity = ("sess1", "cmdA")
    state_hash = "abc"
    out1 = map_classification_to_outcome("CONFLICT", identity, state_hash)
    out2 = map_classification_to_outcome("CONFLICT", identity, state_hash)
    assert out1 == out2
