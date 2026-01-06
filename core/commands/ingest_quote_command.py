from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class IngestQuotePayload:
    symbol: str
    price: float
    currency: str
    # optional, purely data-carrying; no time semantics implied
    asof: Optional[str] = None


@dataclass(frozen=True)
class IngestQuoteCommand:
    schema_version: int
    command_id: str
    session_id: str
    client_sequence: int
    payload: IngestQuotePayload
    kind: Literal["INGEST_QUOTE"] = "INGEST_QUOTE"
    strict: bool = True
    meta: Optional[dict] = None
