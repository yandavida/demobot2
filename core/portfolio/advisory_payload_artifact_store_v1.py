from __future__ import annotations

from datetime import datetime
import json

from core.services.advisory_input_contract_v1 import normalize_advisory_input_v1
from core.v2.errors import EventConflictError
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.models import V2Event
from core.v2.models import hash_payload
from core.v2.models import sha256_hex


ARTIFACT_SESSION_ID = "__treasury_advisory_payload_artifacts__"
LINEAGE_SESSION_ID = "__treasury_advisory_payload_artifact_lineage__"


class AdvisoryPayloadArtifactNotFoundError(KeyError):
    def __init__(self, artifact_id: str) -> None:
        super().__init__(f"advisory payload artifact not found: {artifact_id}")
        self.artifact_id = artifact_id


def _canonical_payload_dict(payload: dict) -> dict:
    normalized = normalize_advisory_input_v1(payload)
    return {
        "contract_version": normalized.contract_version,
        "company_id": normalized.company_id,
        "snapshot_id": normalized.snapshot_id,
        "scenario_template_id": normalized.scenario_template_id,
        "exposures": [
            {
                "currency_pair": row.currency_pair,
                "direction": row.direction,
                "notional": str(row.notional),
                "maturity_date": row.maturity_date.isoformat(),
                "hedge_ratio": None if row.hedge_ratio is None else str(row.hedge_ratio),
            }
            for row in normalized.exposures
        ],
    }


def _artifact_id(payload_dict: dict) -> str:
    canonical_json = json.dumps(payload_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_hex(canonical_json.encode("utf-8"))


def _canonical_lineage_dict(*, artifact_id: str, valuation_run_id: str) -> dict:
    if not isinstance(valuation_run_id, str) or not valuation_run_id.strip():
        raise ValueError("valuation_run_id must be a non-empty string")
    if valuation_run_id != valuation_run_id.strip():
        raise ValueError("valuation_run_id must not contain leading or trailing whitespace")
    return {
        "artifact_id": artifact_id,
        "valuation_run_id": valuation_run_id,
    }


def put_advisory_payload_artifact_v1(payload: dict, *, valuation_run_id: str | None = None) -> str:
    payload_dict = _canonical_payload_dict(payload)
    artifact_id = _artifact_id(payload_dict)

    event_store = SqliteEventStore()
    event = V2Event(
        event_id=artifact_id,
        session_id=ARTIFACT_SESSION_ID,
        ts=datetime.fromisoformat("1970-01-01T00:00:00"),
        type="SNAPSHOT_CREATED",
        payload=payload_dict,
        payload_hash=hash_payload(payload_dict),
    )

    try:
        event_store.append(event)
    except EventConflictError:
        raise

    if valuation_run_id is not None:
        lineage_payload = _canonical_lineage_dict(
            artifact_id=artifact_id,
            valuation_run_id=valuation_run_id,
        )
        lineage_event = V2Event(
            event_id=artifact_id,
            session_id=LINEAGE_SESSION_ID,
            ts=datetime.fromisoformat("1970-01-01T00:00:00"),
            type="SNAPSHOT_CREATED",
            payload=lineage_payload,
            payload_hash=hash_payload(lineage_payload),
        )
        try:
            event_store.append(lineage_event)
        except EventConflictError:
            raise

    return artifact_id


def get_advisory_payload_artifact_v1(artifact_id: str) -> dict:
    event_store = SqliteEventStore()
    events = event_store.list(ARTIFACT_SESSION_ID)
    for event in events:
        if event.event_id == artifact_id:
            payload = dict(event.payload)
            _canonical_payload_dict(payload)
            return payload

    raise AdvisoryPayloadArtifactNotFoundError(artifact_id)


def get_advisory_payload_artifact_lineage_v1(artifact_id: str) -> dict | None:
    event_store = SqliteEventStore()
    events = event_store.list(LINEAGE_SESSION_ID)
    for event in events:
        if event.event_id == artifact_id:
            payload = dict(event.payload)
            return _canonical_lineage_dict(
                artifact_id=artifact_id,
                valuation_run_id=str(payload.get("valuation_run_id", "")),
            )
    return None


__all__ = [
    "ARTIFACT_SESSION_ID",
    "LINEAGE_SESSION_ID",
    "AdvisoryPayloadArtifactNotFoundError",
    "get_advisory_payload_artifact_lineage_v1",
    "put_advisory_payload_artifact_v1",
    "get_advisory_payload_artifact_v1",
]
