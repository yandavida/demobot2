from core.validation.ingest_event_ordering import IngestOrderState, ErrorEnvelope, validate_ingest_event_ordering

class DummyPayload:
    def __init__(self, client_sequence):
        self.client_sequence = client_sequence

class DummyCmd:
    def __init__(self, client_sequence):
        self.payload = DummyPayload(client_sequence)

def test_none_ok():
    state = IngestOrderState(next_client_sequence=5)
    cmd = DummyCmd(None)
    assert validate_ingest_event_ordering(state, cmd) is None

def test_equal_ok():
    state = IngestOrderState(next_client_sequence=7)
    cmd = DummyCmd(7)
    assert validate_ingest_event_ordering(state, cmd) is None

def test_less_than_expected():
    state = IngestOrderState(next_client_sequence=10)
    cmd = DummyCmd(8)
    err = validate_ingest_event_ordering(state, cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.category == "SEMANTIC"
    assert err.code == "OUT_OF_ORDER"
    assert err.details["path"] == "payload.client_sequence"
    assert err.details["reason"] == "expected=10, got=8"
    assert err.error_count == 1

def test_greater_than_expected():
    state = IngestOrderState(next_client_sequence=3)
    cmd = DummyCmd(5)
    err = validate_ingest_event_ordering(state, cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.details["reason"] == "expected=3, got=5"
    assert err.error_count == 1

def test_determinism():
    state = IngestOrderState(next_client_sequence=42)
    cmd = DummyCmd(99)
    err1 = validate_ingest_event_ordering(state, cmd)
    err2 = validate_ingest_event_ordering(state, cmd)
    assert err1 == err2
