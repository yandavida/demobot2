from __future__ import annotations

from datetime import datetime
import json

from core.v2.errors import EventConflictError
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.models import V2Event
from core.v2.models import hash_payload
from core.v2.models import sha256_hex


ARTIFACT_BUNDLE_SESSION_ID = "__treasury_copilot_artifact_bundles_v1__"


class CopilotArtifactBundleNotFoundError(KeyError):
    def __init__(self, artifact_id: str) -> None:
        super().__init__(f"copilot artifact bundle not found: {artifact_id}")
        self.artifact_id = artifact_id


class CopilotArtifactBundleValidationError(ValueError):
    pass


def _dict_from_artifact_object(value: object | None, *, field_name: str) -> dict | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        result = to_dict()
        if isinstance(result, dict):
            return dict(result)
    raise CopilotArtifactBundleValidationError(f"invalid_{field_name}")


def _validate_payload_dict(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise CopilotArtifactBundleValidationError("invalid_artifact_bundle_payload")

    decision = payload.get("advisory_decision")
    explainability = payload.get("explainability")
    report_markdown = payload.get("report_markdown")
    scenario_table_markdown = payload.get("scenario_table_markdown")
    ladder_table_markdown = payload.get("ladder_table_markdown")

    if decision is not None and not isinstance(decision, dict):
        raise CopilotArtifactBundleValidationError("invalid_advisory_decision")
    if explainability is not None and not isinstance(explainability, dict):
        raise CopilotArtifactBundleValidationError("invalid_explainability")
    if report_markdown is not None and not isinstance(report_markdown, str):
        raise CopilotArtifactBundleValidationError("invalid_report_markdown")
    if scenario_table_markdown is not None and not isinstance(scenario_table_markdown, str):
        raise CopilotArtifactBundleValidationError("invalid_scenario_table_markdown")
    if ladder_table_markdown is not None and not isinstance(ladder_table_markdown, str):
        raise CopilotArtifactBundleValidationError("invalid_ladder_table_markdown")

    return {
        "advisory_decision": None if decision is None else dict(decision),
        "explainability": None if explainability is None else dict(explainability),
        "report_markdown": report_markdown,
        "scenario_table_markdown": scenario_table_markdown,
        "ladder_table_markdown": ladder_table_markdown,
    }


def _canonical_payload_dict(*, advisory_decision: object | None, explainability: object | None, report_markdown: str | None, scenario_table_markdown: str | None, ladder_table_markdown: str | None) -> dict:
    payload = {
        "advisory_decision": _dict_from_artifact_object(advisory_decision, field_name="advisory_decision"),
        "explainability": _dict_from_artifact_object(explainability, field_name="explainability"),
        "report_markdown": report_markdown,
        "scenario_table_markdown": scenario_table_markdown,
        "ladder_table_markdown": ladder_table_markdown,
    }
    return _validate_payload_dict(payload)


def _artifact_id(payload_dict: dict) -> str:
    canonical_json = json.dumps(payload_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_hex(canonical_json.encode("utf-8"))


def put_copilot_artifact_bundle_v1(*, advisory_decision: object | None, explainability: object | None, report_markdown: str | None, scenario_table_markdown: str | None, ladder_table_markdown: str | None) -> str:
    payload_dict = _canonical_payload_dict(
        advisory_decision=advisory_decision,
        explainability=explainability,
        report_markdown=report_markdown,
        scenario_table_markdown=scenario_table_markdown,
        ladder_table_markdown=ladder_table_markdown,
    )
    artifact_id = _artifact_id(payload_dict)

    event_store = SqliteEventStore()
    event = V2Event(
        event_id=artifact_id,
        session_id=ARTIFACT_BUNDLE_SESSION_ID,
        ts=datetime.fromisoformat("1970-01-01T00:00:00"),
        type="SNAPSHOT_CREATED",
        payload=payload_dict,
        payload_hash=hash_payload(payload_dict),
    )

    try:
        event_store.append(event)
    except EventConflictError:
        raise

    return artifact_id


def get_copilot_artifact_bundle_v1(artifact_id: str) -> dict:
    event_store = SqliteEventStore()
    events = event_store.list(ARTIFACT_BUNDLE_SESSION_ID)
    for event in events:
        if event.event_id == artifact_id:
            payload = dict(event.payload)
            return _validate_payload_dict(payload)

    raise CopilotArtifactBundleNotFoundError(artifact_id)


__all__ = [
    "ARTIFACT_BUNDLE_SESSION_ID",
    "CopilotArtifactBundleNotFoundError",
    "CopilotArtifactBundleValidationError",
    "put_copilot_artifact_bundle_v1",
    "get_copilot_artifact_bundle_v1",
]
