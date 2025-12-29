from uuid import uuid4
from datetime import datetime

from core.commands.base import CommandMeta
from core.commands.ingest import IngestQuoteCommand
from core.commands.compute import ComputeRequestCommand
from core.commands.snapshot import SnapshotRequestCommand

from api.v2.schemas import (
    IngestQuoteRequest,
    ComputeRequest,
    SnapshotRequest,
)


def ingest_request_to_command(req: IngestQuoteRequest) -> IngestQuoteCommand:
    return IngestQuoteCommand(
        meta=CommandMeta(
            command_id=uuid4(),
            created_at=datetime.utcnow(),
            source="api",
        ),
        symbol=req.symbol,
        price=req.price,
        currency=req.currency,
        as_of=req.as_of,
    )


def compute_request_to_command(req: ComputeRequest) -> ComputeRequestCommand:
    return ComputeRequestCommand(
        meta=CommandMeta(
            command_id=uuid4(),
            created_at=datetime.utcnow(),
            source="api",
        ),
        portfolio_id=req.portfolio_id,
        strict=req.strict,
    )


def snapshot_request_to_command(req: SnapshotRequest) -> SnapshotRequestCommand:
    return SnapshotRequestCommand(
        meta=CommandMeta(
            command_id=uuid4(),
            created_at=datetime.utcnow(),
            source="api",
        ),
        reason=req.reason,
    )
