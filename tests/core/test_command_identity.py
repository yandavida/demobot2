from core.validation.command_identity import get_command_identity

class DummyCmd:
    def __init__(self, session_id, command_id, payload=None, meta=None):
        self.session_id = session_id
        self.command_id = command_id
        self.payload = payload
        self.meta = meta

def test_same_session_and_command_id():
    cmd1 = DummyCmd("sess1", "cmdA")
    cmd2 = DummyCmd("sess1", "cmdA")
    assert get_command_identity(cmd1) == get_command_identity(cmd2)

def test_same_command_id_different_session():
    cmd1 = DummyCmd("sess1", "cmdA")
    cmd2 = DummyCmd("sess2", "cmdA")
    assert get_command_identity(cmd1) != get_command_identity(cmd2)

def test_same_session_different_command_id():
    cmd1 = DummyCmd("sess1", "cmdA")
    cmd2 = DummyCmd("sess1", "cmdB")
    assert get_command_identity(cmd1) != get_command_identity(cmd2)

def test_payload_does_not_affect_identity():
    cmd1 = DummyCmd("sess1", "cmdA", payload={"foo": 1})
    cmd2 = DummyCmd("sess1", "cmdA", payload={"foo": 2})
    assert get_command_identity(cmd1) == get_command_identity(cmd2)

def test_meta_does_not_affect_identity():
    cmd1 = DummyCmd("sess1", "cmdA", meta={"bar": "x"})
    cmd2 = DummyCmd("sess1", "cmdA", meta={"bar": "y"})
    assert get_command_identity(cmd1) == get_command_identity(cmd2)
