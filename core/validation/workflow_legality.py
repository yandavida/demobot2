from dataclasses import dataclass
from typing import Any, Optional

from .operational_outcome import ErrorEnvelope
from .error_taxonomy import make_error


@dataclass(frozen=True)
class WorkflowContext:
    # conservative, minimal session summary for legality checks
    has_any_quotes: bool = False
    applied_version: int = 0


def _extract_kind(cmd: Any) -> Optional[str]:
    if isinstance(cmd, dict):
        k = cmd.get("kind")
        return k if isinstance(k, str) else None
    # typed commands may expose `kind` attribute
    return getattr(cmd, "kind", None)


def check_workflow_legality(context: WorkflowContext, cmd: Any) -> Optional[ErrorEnvelope]:
    """Return None when the command is allowed by the workflow graph,
    otherwise return a canonical SEMANTIC ErrorEnvelope describing the violation.

    Conservative baseline rules (locked):
      - ComputeRequest (`COMPUTE_REQUEST`) requires `has_any_quotes == True`.
      - SnapshotRequest (`SNAPSHOT_REQUEST`) requires `applied_version > 0`.
      - IngestQuote (`INGEST_QUOTE`) always allowed.
      - IngestEvent (`INGEST_EVENT`) treated like IngestQuote (always allowed).
    """
    kind = _extract_kind(cmd)
    if kind is None:
        # unknown shape: delegate to other validators; here treat as allowed
        return None

    # Rule L3 / L4: INGEST_QUOTE and INGEST_EVENT always allowed
    if kind in {"INGEST_QUOTE", "INGEST_EVENT"}:
        return None

    # Rule L1: COMPUTE_REQUEST requires at least one accepted quote
    if kind == "COMPUTE_REQUEST":
        if not context.has_any_quotes:
            return make_error("ILLEGAL_SEQUENCE", details={"path": "workflow", "reason": "COMPUTE_REQUEST requires prior INGEST_QUOTE"})
        return None

    # Rule L2: SNAPSHOT_REQUEST requires applied_version > 0
    if kind == "SNAPSHOT_REQUEST":
        if context.applied_version <= 0:
            return make_error("ILLEGAL_SEQUENCE", details={"path": "workflow", "reason": "SNAPSHOT_REQUEST requires applied_version > 0"})
        return None

    # Default: allow other kinds (do not invent rules)
    return None
