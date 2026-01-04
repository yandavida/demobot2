from core.validation.command_classification import classify_command

def test_unseen_command_new():
    assert classify_command(False, None, "abc") == "NEW"
    assert classify_command(False, "xyz", "abc") == "NEW"

def test_seen_same_fingerprint_idempotent():
    assert classify_command(True, "abc", "abc") == "IDEMPOTENT_REPLAY"
    assert classify_command(True, "123", "123") == "IDEMPOTENT_REPLAY"

def test_seen_different_fingerprint_conflict():
    assert classify_command(True, "abc", "def") == "CONFLICT"
    assert classify_command(True, "123", "456") == "CONFLICT"

def test_determinism():
    result1 = classify_command(True, "abc", "def")
    result2 = classify_command(True, "abc", "def")
    assert result1 == result2
