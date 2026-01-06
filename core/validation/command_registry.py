from typing import Optional, Set, Dict, Any

from .operational_outcome import ErrorEnvelope
from .error_taxonomy import make_error


# Centralized, canonical supported schema versions per command kind.
# This is the single source-of-truth for schema_version enforcement for Gate B.
SUPPORTED_SCHEMA_VERSIONS_BY_KIND: Dict[str, Set[int]] = {
    "INGEST_EVENT": {1},
    "INGEST_QUOTE": {1},
    "SNAPSHOT": {1},
    "PORTFOLIO_RISK": {1},
    "SCENARIO_GRID": {1},
}


# Allowlist of command kinds that exist in the codebase today.
# Keep this set minimal and only include kinds already used elsewhere.
ALLOWED_COMMAND_KINDS: Set[str] = {
    "INGEST_EVENT",
    "INGEST_QUOTE",
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
    return make_error("UNKNOWN_COMMAND_KIND", details={"path": "kind", "reason": f"unknown kind: {kind}"})


def validate_command_dict(cmd: Dict[str, Any]) -> Optional[ErrorEnvelope]:
    """Centralized validation for raw command dicts.

    Order of checks enforced here:
      1. kind known? else UNKNOWN_COMMAND_KIND
      2. schema_version present and int? else MISSING_SCHEMA_VERSION
      3. schema_version supported for this kind? else UNSUPPORTED_SCHEMA_VERSION

    Returns None on success, or an ErrorEnvelope describing the validation failure.
    """
    kind = cmd.get("kind")
    if not isinstance(kind, str):
        return make_error("UNKNOWN_COMMAND_KIND", details={"path": "kind", "reason": "missing or invalid kind"})

    unknown = validate_command_kind(kind)
    if unknown is not None:
        return unknown

    # schema_version presence and type
    if "schema_version" not in cmd:
        return make_error("MISSING_SCHEMA_VERSION", details={"path": "schema_version", "reason": "missing"})
    sv = cmd.get("schema_version")
    if not isinstance(sv, int):
        return make_error("MISSING_SCHEMA_VERSION", details={"path": "schema_version", "reason": "type"})

    # supported versions
    allowed = SUPPORTED_SCHEMA_VERSIONS_BY_KIND.get(kind)
    if allowed is None or sv not in allowed:
        return make_error("UNSUPPORTED_SCHEMA_VERSION", details={"path": "schema_version", "reason": f"unsupported: {sv}"})

    return None
