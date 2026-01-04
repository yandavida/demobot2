from core.validation.seen_command import has_seen_command

class DummyState:
    def __init__(self):
        self.seen_command_ids = {}
    def get_seen_command_ids(self, session_id):
        return self.seen_command_ids.get(session_id, set())
    def add_seen(self, session_id, command_id):
        self.seen_command_ids.setdefault(session_id, set()).add(command_id)

def test_new_command_identity():
    state = DummyState()
    identity = ("sess1", "cmdA")
    assert has_seen_command(state, identity) is False

def test_seen_command_identity():
    state = DummyState()
    identity = ("sess1", "cmdA")
    state.add_seen("sess1", "cmdA")
    assert has_seen_command(state, identity) is True

def test_detection_survives_restart():
    state1 = DummyState()
    state1.add_seen("sess1", "cmdA")
    # simulate restart: new state object with same data
    state2 = DummyState()
    state2.seen_command_ids = dict(state1.seen_command_ids)
    identity = ("sess1", "cmdA")
    assert has_seen_command(state2, identity) is True

def test_determinism():
    state = DummyState()
    state.add_seen("sess1", "cmdA")
    identity = ("sess1", "cmdA")
    result1 = has_seen_command(state, identity)
    result2 = has_seen_command(state, identity)
    assert result1 == result2
