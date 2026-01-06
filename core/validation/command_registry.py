from typing import Optional, Set

from .operational_outcome import ErrorEnvelope


# Allowlist of command kinds that exist in the codebase today.
# Keep this set minimal and only include kinds already used elsewhere.
ALLOWED_COMMAND_KINDS: Set[str] = {
    "INGEST_EVENT",
    "SNAPSHOT",
    "PORTFOLIO_RISK",
    "SCENARIO_GRID",
}


def validate_command_kind(kind: str) -> Optional[ErrorEnvelope]:
    """Validate that a command `kind` is allowed.

    Returns None when supported, otherwise returns an ErrorEnvelope with
    the canonical VALIDATION error described by the spec.
    """
    if kind in ALLOWED_COMMAND_KINDS:
        return None

    return ErrorEnvelope(
        category="VALIDATION",
        code="UNKNOWN_COMMAND_KIND",
        message="unsupported command kind",
        details={"path": "kind", "reason": f"unknown kind: {kind}"},
        error_count=1,
    )
