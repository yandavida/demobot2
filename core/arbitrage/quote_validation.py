from __future__ import annotations

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple

from core.arbitrage.models import VenueQuote

MAX_VALIDATION_ISSUES = 50


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    field: str | None = None
    symbol: str | None = None
    venue: str | None = None

    def sort_key(self) -> Tuple[str, str, str, str, str]:
        return (
            self.code,
            self.field or "",
            self.venue or "",
            self.symbol or "",
            self.message,
        )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code,
            "message": self.message,
        }
        if self.field is not None:
            payload["field"] = self.field
        if self.symbol is not None:
            payload["symbol"] = self.symbol
        if self.venue is not None:
            payload["venue"] = self.venue
        return payload


@dataclass
class ValidationSummary:
    total_quotes: int
    invalid_quotes: int
    issues: List[ValidationIssue]
    max_issues: int = MAX_VALIDATION_ISSUES

    @property
    def total_issues(self) -> int:
        return len(self.issues)

    def _sorted_issues(self) -> List[ValidationIssue]:
        return sorted(self.issues, key=lambda issue: issue.sort_key())

    def to_dict(self) -> dict[str, object]:
        sorted_issues = self._sorted_issues()
        capped = sorted_issues[: self.max_issues]
        return {
            "total_quotes": self.total_quotes,
            "invalid_quotes": self.invalid_quotes,
            "total_issues": len(sorted_issues),
            "issues": [issue.to_dict() for issue in capped],
            "capped": len(sorted_issues) > len(capped),
        }

    def is_empty(self) -> bool:
        return self.total_issues == 0


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _validate_quote(
    payload: dict[str, Any], default_ccy: str = "USD"
) -> Tuple[VenueQuote | None, List[ValidationIssue]]:
    symbol_raw = payload.get("symbol")
    venue_raw = payload.get("venue")
    symbol = symbol_raw.strip() if isinstance(symbol_raw, str) else None
    venue = venue_raw.strip() if isinstance(venue_raw, str) else None

    issues: list[ValidationIssue] = []

    if not symbol:
        issues.append(
            ValidationIssue(
                code="missing_symbol",
                message="Quote is missing symbol",
                field="symbol",
                symbol=symbol_raw if isinstance(symbol_raw, str) else None,
                venue=venue,
            )
        )

    if not venue:
        issues.append(
            ValidationIssue(
                code="missing_venue",
                message="Quote is missing venue",
                field="venue",
                symbol=symbol,
                venue=venue_raw if isinstance(venue_raw, str) else None,
            )
        )

    bid_raw = payload.get("bid")
    ask_raw = payload.get("ask")
    bid = _coerce_float(bid_raw) if bid_raw is not None else None
    ask = _coerce_float(ask_raw) if ask_raw is not None else None

    if bid is None:
        issues.append(
            ValidationIssue(
                code="missing_bid",
                message="Bid is required",
                field="bid",
                symbol=symbol,
                venue=venue,
            )
        )
    elif bid <= 0:
        issues.append(
            ValidationIssue(
                code="non_positive_bid",
                message="Bid must be positive",
                field="bid",
                symbol=symbol,
                venue=venue,
            )
        )

    if ask is None:
        issues.append(
            ValidationIssue(
                code="missing_ask",
                message="Ask is required",
                field="ask",
                symbol=symbol,
                venue=venue,
            )
        )
    elif ask <= 0:
        issues.append(
            ValidationIssue(
                code="non_positive_ask",
                message="Ask must be positive",
                field="ask",
                symbol=symbol,
                venue=venue,
            )
        )

    size_raw = payload.get("size")
    size = _coerce_float(size_raw) if size_raw is not None else None
    if size is not None and size <= 0:
        issues.append(
            ValidationIssue(
                code="non_positive_size",
                message="Size must be positive when provided",
                field="size",
                symbol=symbol,
                venue=venue,
            )
        )

    if issues:
        return None, issues

    return (
        VenueQuote(
            venue=venue or "",
            symbol=symbol or "",
            bid=bid,
            ask=ask,
            ccy=str(payload.get("ccy", default_ccy)),
            size=size,
            fees_bps=float(payload.get("fees_bps", 0.0) or 0.0),
            latency_ms=_coerce_float(payload.get("latency_ms")),
        ),
        issues,
    )


def validate_quotes(
    quotes_payload: Iterable[dict[str, Any]],
    max_issues: int = MAX_VALIDATION_ISSUES,
    default_ccy: str = "USD",
) -> Tuple[List[VenueQuote], ValidationSummary]:
    issues: list[ValidationIssue] = []
    valid_quotes: list[VenueQuote] = []
    invalid_quotes = 0
    processed_quotes = list(quotes_payload)

    for quote in processed_quotes:
        valid, quote_issues = _validate_quote(quote, default_ccy=default_ccy)
        if quote_issues:
            invalid_quotes += 1
            issues.extend(quote_issues)
        else:
            valid_quotes.append(valid)  # type: ignore[arg-type]

    summary = ValidationSummary(
        total_quotes=len(processed_quotes),
        invalid_quotes=invalid_quotes,
        issues=issues,
        max_issues=max_issues,
    )

    return valid_quotes, summary


__all__ = [
    "ValidationIssue",
    "ValidationSummary",
    "validate_quotes",
    "MAX_VALIDATION_ISSUES",
]
