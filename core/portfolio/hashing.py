from __future__ import annotations

import hashlib
import json
from typing import Any


def _default_serializer(obj: Any) -> str:
    return repr(obj)


def stable_hash(value: Any) -> str:
    """Return a stable SHA256 hash for arbitrary JSON-serialisable data."""

    serialized = json.dumps(value, sort_keys=True, default=_default_serializer)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
