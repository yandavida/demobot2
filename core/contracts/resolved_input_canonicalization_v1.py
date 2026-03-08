from __future__ import annotations

import datetime
from dataclasses import fields
from dataclasses import is_dataclass
from decimal import Decimal
from decimal import InvalidOperation
import hashlib
import json
from typing import Any
from typing import Mapping


CANONICAL_HASH_ALGORITHM = "sha256"


def canonical_decimal_str_v1(value: Decimal | str | int | float) -> str:
    """Return a deterministic canonical decimal string (no exponent form)."""

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("value must be a valid decimal") from exc

    if not decimal_value.is_finite():
        raise ValueError("value must be finite")

    if decimal_value == Decimal("0"):
        return "0"

    normalized = decimal_value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def canonical_timestamp_str_v1(value: datetime.datetime) -> str:
    """Return a deterministic UTC timestamp string using fixed microsecond precision."""

    if not isinstance(value, datetime.datetime):
        raise ValueError("value must be a datetime")
    if value.tzinfo is None:
        raise ValueError("value must be timezone-aware")

    utc_value = value.astimezone(datetime.timezone.utc)
    return utc_value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonicalize_value(value: Any) -> Any:
    if value is None:
        # Explicit null handling: preserve null in canonical JSON.
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        return value

    if isinstance(value, Decimal):
        return canonical_decimal_str_v1(value)

    if isinstance(value, float):
        return canonical_decimal_str_v1(value)

    if isinstance(value, datetime.datetime):
        return canonical_timestamp_str_v1(value)

    if isinstance(value, datetime.date):
        return value.isoformat()

    if isinstance(value, datetime.time):
        return value.isoformat()

    if is_dataclass(value):
        canonical: dict[str, Any] = {}
        for field in fields(value):
            canonical[field.name] = _canonicalize_value(getattr(value, field.name))
        return canonical

    if isinstance(value, Mapping):
        canonical_mapping: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda k: str(k)):
            canonical_mapping[str(key)] = _canonicalize_value(value[key])
        return canonical_mapping

    if isinstance(value, tuple):
        return [_canonicalize_value(item) for item in value]

    if isinstance(value, list):
        return [_canonicalize_value(item) for item in value]

    raise TypeError(f"unsupported canonicalization type: {type(value).__name__}")


def canonical_resolved_input_hash_v1(payload: object) -> str:
    """Hash canonicalized resolved-input payload with deterministic SHA-256 rules."""

    canonical_payload = _canonicalize_value(payload)
    encoded = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )

    if CANONICAL_HASH_ALGORITHM != "sha256":
        raise ValueError("unsupported canonical hash algorithm")

    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = [
    "CANONICAL_HASH_ALGORITHM",
    "canonical_decimal_str_v1",
    "canonical_resolved_input_hash_v1",
    "canonical_timestamp_str_v1",
]
