from __future__ import annotations
import hashlib
import json
from typing import Any

from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0


def market_snapshot_id(snapshot: MarketSnapshotPayloadV0) -> str:
    """Deterministic canonical id for a MarketSnapshotPayloadV0.

    Serializes the payload with sorted keys and no extra whitespace, then
    returns the SHA256 hex digest. Pure and deterministic.
    """
    # Use Pydantic v2 model_dump to get native Python structures
    try:
        data = snapshot.model_dump()
    except Exception:
        # Fallback: if a raw dict-like passed
        if isinstance(snapshot, dict):
            data = snapshot
        else:
            raise

    canon = json.dumps(data, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    return h
