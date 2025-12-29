
from api.v2.adapters.command_adapter import ingest_request_to_command
from api.v2.schemas import IngestEventRequest
from core.v2.models import EventType

def test_ingest_request_to_command_mapping():
    req = IngestEventRequest(
        event_id="e1",
        ts=None,
        type="QUOTE_INGESTED",
        payload={"k": "v"},
    )

    cmd = ingest_request_to_command(req)

    assert cmd.event_id == req.event_id
    assert cmd.ts == req.ts
    assert cmd.type == req.type
    assert cmd.payload == req.payload

    assert cmd.meta.source == "api"
    assert cmd.meta.command_id is not None

    assert cmd.meta.source == "api"
    assert cmd.meta.command_id is not None
