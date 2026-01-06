import pytest
from dataclasses import FrozenInstanceError

from core.commands.snapshot_request_command import (
    SnapshotRequestPayload,
    SnapshotRequestCommand,
)


def test_defaults_and_shape():
    payload = SnapshotRequestPayload()
    assert payload.force is False

    cmd = SnapshotRequestCommand(command_id="c1", session_id="s1", payload=payload)
    assert cmd.strict is True
    assert cmd.meta is None
    assert cmd.kind == "SNAPSHOT_REQUEST"


def test_immutability_and_equality():
    payload = SnapshotRequestPayload()
    cmd1 = SnapshotRequestCommand(command_id="c2", session_id="s2", payload=payload)
    cmd2 = SnapshotRequestCommand(command_id="c2", session_id="s2", payload=payload)
    assert cmd1 == cmd2

    with pytest.raises(FrozenInstanceError):
        cmd1.strict = False


def test_payload_required():
    payload = SnapshotRequestPayload(force=True)
    cmd = SnapshotRequestCommand(command_id="id", session_id="sid", payload=payload)
    assert isinstance(cmd.payload, SnapshotRequestPayload)
