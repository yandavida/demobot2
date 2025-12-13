from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


class QuoteValidationError(Exception):
    """Exception raised when quote validation fails in strict mode."""

    def __init__(self, summary: "ValidationSummary") -> None:
        super().__init__("Quote validation failed")
        self.summary = summary


@dataclass
class ValidationSummary:
    """Collects validation errors and warnings while keeping counters stable."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    max_items: int = 20

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic mapping with capped lists.

        Lists are capped to ``max_items`` but counters reflect the full length to
        allow clients to understand whether additional issues were truncated.
        """

        errors_capped = self.errors[: self.max_items]
        warnings_capped = self.warnings[: self.max_items]

        return {
            "errors": errors_capped,
            "warnings": warnings_capped,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


def _validate_single_quote(raw_quote: Mapping[str, object], summary: ValidationSummary) -> None:
    symbol = raw_quote.get("symbol")
    venue = raw_quote.get("venue")
    bid = raw_quote.get("bid")
    ask = raw_quote.get("ask")

    if not symbol:
        summary.add_error("Missing symbol")
    if not venue:
        summary.add_error("Missing venue")

    if bid is None or ask is None:
        summary.add_error("Bid/ask must be provided")
    else:
        try:
            if float(bid) <= 0 or float(ask) <= 0:
                summary.add_error("Bid/ask must be positive")
            elif float(bid) >= float(ask):
                summary.add_warning("Bid is not lower than ask")
        except Exception:
            summary.add_error("Bid/ask must be numeric")


def validate_quotes_payload(quotes_payload: Iterable[Mapping[str, object]]) -> ValidationSummary:
    """Perform basic validation on an iterable of quotes."""

    summary = ValidationSummary()
    for quote in quotes_payload:
        _validate_single_quote(quote, summary)
    return summary
