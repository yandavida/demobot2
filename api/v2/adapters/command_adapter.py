from uuid import uuid4
from datetime import datetime

from core.commands.base import CommandMeta
from core.commands.event_ingest import IngestEventCommand
from api.v2.schemas import IngestEventRequest

def ingest_request_to_command(req: IngestEventRequest) -> IngestEventCommand:
    return IngestEventCommand(
        meta=CommandMeta(
            command_id=uuid4(),
            created_at=datetime.utcnow(),
            source="api",
        ),
        event_id=req.event_id,
        ts=req.ts,
        type=req.type,
        payload=req.payload,
    )
