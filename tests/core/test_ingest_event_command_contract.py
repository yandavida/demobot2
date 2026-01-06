import pytest
from dataclasses import FrozenInstanceError

from core.commands.ingest_event_command import (
    IngestEventPayload,
    IngestEventCommand,
)


def test_defaults_and_shape():
    payload = IngestEventPayload(event_type="EV", data={"x": 1})
    assert payload.client_sequence is None

    cmd = IngestEventCommand(command_id="c1", session_id="s1", payload=payload)
    assert cmd.strict is True
    assert cmd.meta is None
    assert cmd.kind == "INGEST_EVENT"


def test_immutability():
    payload = IngestEventPayload(event_type="EV", data={})
    cmd = IngestEventCommand(command_id="c2", session_id="s2", payload=payload)

    with pytest.raises(FrozenInstanceError):
        cmd.strict = False

    with pytest.raises(FrozenInstanceError):
        payload.event_type = "OTHER"


def test_payload_required():
    payload = IngestEventPayload(event_type="EV", data={})
    cmd = IngestEventCommand(command_id="id", session_id="sid", payload=payload)
    assert isinstance(cmd.payload, IngestEventPayload)
