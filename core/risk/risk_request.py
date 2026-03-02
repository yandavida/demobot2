"""Gate G9.1: RiskRequest v1 — versioned deterministic risk request contract.

Defines the canonical contract for submitting a risk computation request
to Gate 9's risk layer. No pricing logic. No lifecycle coupling.

Validation rules:
- schema_version missing or None → MISSING_SCHEMA_VERSION
- schema_version unsupported → UNSUPPORTED_SCHEMA_VERSION
- instrument_ids empty → VALIDATION_ERROR
- market_snapshot_id empty → VALIDATION_ERROR
- instrument_ids normalized to sorted unique tuple (ordering freeze rule)

strict=True (default):
  Raise RiskValidationError immediately on first violation.

strict=False:
  Same rejection (no partial accept), but ErrorEnvelope includes richer
  diagnostics metadata in details dict.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.pricing.fx.valuation_context import ValuationContext
from core.risk.scenario_spec import ScenarioSpec
from core.validation.error_envelope import ErrorEnvelope
from core.validation.error_taxonomy import make_error


SUPPORTED_SCHEMA_VERSION: int = 1


class RiskValidationError(ValueError):
    """Raised when a RiskRequest fails validation. Carries a structured ErrorEnvelope."""

    def __init__(self, envelope: ErrorEnvelope) -> None:
        super().__init__(envelope.message)
        self.envelope = envelope


def _reject(code: str, details: dict[str, str], strict: bool) -> None:
    envelope = make_error(code, {k: str(v) for k, v in details.items()})  # type: ignore[arg-type]
    if strict:
        raise RiskValidationError(envelope)
    else:
        # Lenient mode: still reject — no partial accept.
        # Diagnostics are richer: details include mode and all context keys.
        diag_details = dict(details)
        diag_details["validation_mode"] = "lenient"
        envelope_with_diag = make_error(code, {k: str(v) for k, v in diag_details.items()})  # type: ignore[arg-type]
        raise RiskValidationError(envelope_with_diag)


@dataclass(frozen=True)
class RiskRequest:
    schema_version: int
    valuation_context: ValuationContext
    market_snapshot_id: str
    instrument_ids: tuple[str, ...]
    scenario_spec: ScenarioSpec
    strict: bool = True

    def __post_init__(self) -> None:
        strict = self.strict

        # schema_version: missing
        if self.schema_version is None:
            _reject(
                "MISSING_SCHEMA_VERSION",
                {"field": "schema_version"},
                strict,
            )

        # schema_version: unsupported
        if self.schema_version != SUPPORTED_SCHEMA_VERSION:
            _reject(
                "UNSUPPORTED_SCHEMA_VERSION",
                {
                    "given": str(self.schema_version),
                    "supported": str(SUPPORTED_SCHEMA_VERSION),
                },
                strict,
            )

        # market_snapshot_id: non-empty
        if not isinstance(self.market_snapshot_id, str) or not self.market_snapshot_id.strip():
            _reject(
                "VALIDATION_ERROR",
                {"field": "market_snapshot_id", "reason": "must be a non-empty string"},
                strict,
            )

        # instrument_ids: non-empty
        if not self.instrument_ids:
            _reject(
                "VALIDATION_ERROR",
                {"field": "instrument_ids", "reason": "must be a non-empty list"},
                strict,
            )

        # Normalize instrument_ids: sorted unique tuple (deterministic ordering freeze rule)
        object.__setattr__(
            self,
            "instrument_ids",
            tuple(sorted(set(self.instrument_ids))),
        )


__all__ = ["RiskRequest", "RiskValidationError", "SUPPORTED_SCHEMA_VERSION"]
