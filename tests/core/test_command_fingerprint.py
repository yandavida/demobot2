from core.validation.command_fingerprint import compute_command_fingerprint

class DummyPayload:
    def __init__(self, event_type, data, client_sequence=None):
        self.event_type = event_type
        self.data = data
        self.client_sequence = client_sequence

class DummyCmd:
    def __init__(self, kind, payload, command_id=None, session_id=None, meta=None):
        self.kind = kind
        self.payload = payload
        self.command_id = command_id
        self.session_id = session_id
        self.meta = meta

def test_same_content_same_fingerprint():
    p1 = DummyPayload("EV", {"a": 1, "b": 2}, 5)
    c1 = DummyCmd("INGEST_EVENT", p1)
    p2 = DummyPayload("EV", {"a": 1, "b": 2}, 5)
    c2 = DummyCmd("INGEST_EVENT", p2)
    assert compute_command_fingerprint(c1) == compute_command_fingerprint(c2)

def test_different_payload_value():
    p1 = DummyPayload("EV", {"a": 1, "b": 2}, 5)
    p2 = DummyPayload("EV", {"a": 1, "b": 3}, 5)
    c1 = DummyCmd("INGEST_EVENT", p1)
    c2 = DummyCmd("INGEST_EVENT", p2)
    assert compute_command_fingerprint(c1) != compute_command_fingerprint(c2)

def test_different_event_type():
    p1 = DummyPayload("EV1", {"a": 1}, 5)
    p2 = DummyPayload("EV2", {"a": 1}, 5)
    c1 = DummyCmd("INGEST_EVENT", p1)
    c2 = DummyCmd("INGEST_EVENT", p2)
    assert compute_command_fingerprint(c1) != compute_command_fingerprint(c2)

def test_different_client_sequence():
    p1 = DummyPayload("EV", {"a": 1}, 5)
    p2 = DummyPayload("EV", {"a": 1}, 6)
    c1 = DummyCmd("INGEST_EVENT", p1)
    c2 = DummyCmd("INGEST_EVENT", p2)
    assert compute_command_fingerprint(c1) != compute_command_fingerprint(c2)

def test_dict_key_order_irrelevant():
    p1 = DummyPayload("EV", {"a": 1, "b": 2}, 5)
    p2 = DummyPayload("EV", {"b": 2, "a": 1}, 5)
    c1 = DummyCmd("INGEST_EVENT", p1)
    c2 = DummyCmd("INGEST_EVENT", p2)
    assert compute_command_fingerprint(c1) == compute_command_fingerprint(c2)

def test_command_id_does_not_affect_fingerprint():
    p = DummyPayload("EV", {"a": 1}, 5)
    c1 = DummyCmd("INGEST_EVENT", p, command_id="X")
    c2 = DummyCmd("INGEST_EVENT", p, command_id="Y")
    assert compute_command_fingerprint(c1) == compute_command_fingerprint(c2)

def test_session_id_does_not_affect_fingerprint():
    p = DummyPayload("EV", {"a": 1}, 5)
    c1 = DummyCmd("INGEST_EVENT", p, session_id="S1")
    c2 = DummyCmd("INGEST_EVENT", p, session_id="S2")
    assert compute_command_fingerprint(c1) == compute_command_fingerprint(c2)
