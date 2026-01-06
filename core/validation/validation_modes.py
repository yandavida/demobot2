from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Set

from .operational_outcome import ErrorEnvelope


class ValidationMode(Enum):
    STRICT = "strict"
    LENIENT = "lenient"


@dataclass(frozen=True)
class ValidationDecision:
    accepted: bool
    errors: List[ErrorEnvelope]
    warnings: List[ErrorEnvelope]


# Small explicit allowlist for semantic errors that may be downgraded to warnings
# Operators must intentionally add codes here; default is conservative.
DOWNGRADEABLE_SEMANTIC_CODES: Set[str] = set()


def apply_validation_mode(mode: ValidationMode, errors: List[ErrorEnvelope]) -> ValidationDecision:
    """Apply the institutional validation mode policy.

    Rules (conservative/default):
      - strict: any error (any category) => REJECT (accepted=False), return errors as-is
      - lenient: VALIDATION and CONFLICT => REJECT
                SEMANTIC => REJECT unless error.code in DOWNGRADEABLE_SEMANTIC_CODES
                If downgraded, move to warnings.

    Deterministic precedence: any rejecting error present yields accepted=False.
    Warnings may be present but cannot override a rejecting error.
    """
    if not errors:
        return ValidationDecision(accepted=True, errors=[], warnings=[])

    errors_out: List[ErrorEnvelope] = []
    warnings_out: List[ErrorEnvelope] = []

    # Helper to classify
    def is_validation(err: ErrorEnvelope) -> bool:
        return getattr(err, "category", None) == "VALIDATION"

    def is_semantic(err: ErrorEnvelope) -> bool:
        return getattr(err, "category", None) == "SEMANTIC"

    def is_conflict(err: ErrorEnvelope) -> bool:
        return getattr(err, "category", None) == "CONFLICT"

    if mode == ValidationMode.STRICT:
        # Any error => reject
        return ValidationDecision(accepted=False, errors=list(errors), warnings=[])

    # LENIENT
    # First, deterministically examine errors and separate downgradeable semantic ones.
    for err in errors:
        if is_semantic(err) and err.code in DOWNGRADEABLE_SEMANTIC_CODES:
            warnings_out.append(err)
        else:
            errors_out.append(err)

    # If any remaining errors (validation or conflict or non-downgradable semantic), reject.
    if errors_out:
        return ValidationDecision(accepted=False, errors=errors_out, warnings=warnings_out)

    # No rejecting errors remain, only warnings
    return ValidationDecision(accepted=True, errors=[], warnings=warnings_out)
