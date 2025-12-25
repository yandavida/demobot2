from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable, List

from core.finance.currency import normalize_currency


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    normalized: dict[str, Any] | None = None


def _coerce_float(value: Any, field_name: str, errors: List[str]) -> float | None:
    if value is None:
        errors.append(f"{field_name} is missing")
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name} must be a number")
        return None


def _validate_timestamp(raw: Any, warnings: List[str]) -> datetime | None:
    if raw is None:
        return None

    ts: datetime | None
    if isinstance(raw, datetime):
        ts = raw
    elif isinstance(raw, str):
        try:
            ts = datetime.fromisoformat(raw)
        except ValueError:
            warnings.append("timestamp is not a valid ISO-8601 string")
            return None
    else:
        warnings.append("timestamp is of unsupported type")
        return None

    future_cutoff = datetime.utcnow() + timedelta(minutes=5)
    past_cutoff = datetime.utcnow() - timedelta(days=7)
    if ts > future_cutoff:
        warnings.append("timestamp is in the future")
    if ts < past_cutoff:
        warnings.append("timestamp is stale")
    return ts


def validate_quote_payload(payload: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    normalized: dict[str, Any] = {}

    if not isinstance(payload, dict):
        return ValidationResult(
            is_valid=False, errors=["payload must be a dict"], warnings=warnings
        )

    symbol = payload.get("symbol")
    if not symbol or not str(symbol).strip():
        errors.append("symbol is required")
    else:
        normalized["symbol"] = str(symbol).strip()

    venue = payload.get("venue")
    if not venue or not str(venue).strip():
        errors.append("venue is required")
    else:
        normalized["venue"] = str(venue).strip()

    raw_ccy = payload.get("ccy") or payload.get("currency")
    if raw_ccy is None:
        errors.append("ccy is required")
    else:
        try:
            normalized["ccy"] = normalize_currency(raw_ccy, field_name="Quote.ccy")
        except Exception:
            errors.append("ccy must be a supported currency")

    bid = _coerce_float(payload.get("bid"), "bid", errors)
    ask = _coerce_float(payload.get("ask"), "ask", errors)

    if bid is not None:
        if bid < 0:
            errors.append("bid must be non-negative")
        else:
            normalized["bid"] = bid

    if ask is not None:
        if ask < 0:
            errors.append("ask must be non-negative")
        else:
            normalized["ask"] = ask

    if bid is not None and ask is not None:
        if bid > ask:
            errors.append("bid must be less than or equal to ask")
        elif bid == ask:
            warnings.append("bid/ask are equal — zero spread")

    size = payload.get("size")
    if size is not None:
        size_f = _coerce_float(size, "size", errors)
        if size_f is not None:
            if size_f < 0:
                errors.append("size must be non-negative")
            else:
                normalized["size"] = size_f

    fees_bps = payload.get("fees_bps", 0.0)
    fees_bps_value = _coerce_float(fees_bps, "fees_bps", errors)
    if fees_bps_value is not None:
        normalized["fees_bps"] = fees_bps_value

    latency = payload.get("latency_ms")
    if latency is not None:
        latency_value = _coerce_float(latency, "latency_ms", errors)
        if latency_value is not None:
            if latency_value < 0:
                errors.append("latency_ms must be non-negative")
            else:
                normalized["latency_ms"] = latency_value

    ts = _validate_timestamp(payload.get("timestamp") or payload.get("as_of"), warnings)
    if ts:
        normalized["as_of"] = ts

    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid, errors=errors, warnings=warnings, normalized=normalized
    )


def validate_quotes_payload(payloads: Iterable[dict[str, Any]]) -> list[ValidationResult]:
    return [validate_quote_payload(p) for p in payloads]


__all__ = [
    "ValidationResult",
    "validate_quote_payload",
    "validate_quotes_payload",
]
