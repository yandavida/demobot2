import json
import hashlib
from typing import Any

def compute_command_fingerprint(cmd: Any) -> str:
    """
    Canonical fingerprint for idempotency:
    Includes: kind, payload.event_type, payload.data, payload.client_sequence
    Excludes: command_id, session_id, meta, timestamps
    """
    def canonical_json(obj):
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    payload = getattr(cmd, "payload", None)
    if payload is None:
        raise ValueError("Command missing payload")
    # Extract relevant fields
    fp_obj = {
        "kind": getattr(cmd, "kind", None),
        "event_type": getattr(payload, "event_type", None),
        "data": getattr(payload, "data", None),
        "client_sequence": getattr(payload, "client_sequence", None),
    }
    canon = canonical_json(fp_obj)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
