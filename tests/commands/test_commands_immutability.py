import pytest
from dataclasses import FrozenInstanceError
from uuid import uuid4
from datetime import datetime

from core.commands.base import CommandMeta
from core.commands.event_ingest import IngestEventCommand


def test_ingest_command_is_immutable():
    cmd = IngestEventCommand(
        meta=CommandMeta(
            command_id=uuid4(),
            created_at=datetime.utcnow(),
            source="test",
        ),
        event_id="e1",
        ts=None,
        type="QUOTE_INGESTED",
        payload={"k": "v"},
    )

    with pytest.raises(FrozenInstanceError):
        cmd.event_id = "e2"
