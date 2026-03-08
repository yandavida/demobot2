from __future__ import annotations

import datetime
from typing import Optional

from core.contracts.model_registry import ModelCapability
from core.contracts.model_registry import ModelRegistryEntry
from core.contracts.reference_data_set import ReferenceDataSet
from core.contracts.valuation_policy_set import ValuationPolicySet
from core.contracts.valuation_run import ValuationRun
from core.persistence.repositories import ModelRegistryRepository
from core.persistence.repositories import ReferenceDataSetRepository
from core.persistence.repositories import ValuationPolicySetRepository
from core.persistence.repositories import ValuationRunRepository
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.models import V2Event
from core.v2.models import hash_payload


_EPOCH_TS = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
_REFERENCE_DATA_SET_SESSION_ID = "__reference_data_set_repository__"
_VALUATION_POLICY_SET_SESSION_ID = "__valuation_policy_set_repository__"
_VALUATION_RUN_SESSION_ID = "__valuation_run_repository__"
_MODEL_REGISTRY_SESSION_ID = "__model_registry_repository__"


def _require_id_consistency(expected_id: str, actual_id: str, field_name: str) -> None:
    if expected_id != actual_id:
        raise ValueError(f"{field_name} mismatch between repository key and object field")


def _require_non_empty_id(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _to_datetime(value: str, field_name: str) -> datetime.datetime:
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return parsed


class _SqliteEventBackedRepository:
    def __init__(self, db_path: str | None = None) -> None:
        self._event_store = SqliteEventStore(db_path=db_path)

    def _save_payload(self, *, session_id: str, object_id: str, payload: dict[str, object]) -> None:
        _require_non_empty_id(session_id, "session_id")
        _require_non_empty_id(object_id, "object_id")
        event = V2Event(
            event_id=object_id,
            session_id=session_id,
            ts=_EPOCH_TS,
            type="SNAPSHOT_CREATED",
            payload=payload,
            payload_hash=hash_payload(payload),
        )
        self._event_store.append(event)

    def _get_payload(self, *, session_id: str, object_id: str) -> Optional[dict[str, object]]:
        _require_non_empty_id(session_id, "session_id")
        _require_non_empty_id(object_id, "object_id")
        events = self._event_store.list(session_id)
        for event in events:
            if event.event_id == object_id:
                return event.payload
        return None


class SqliteReferenceDataSetRepository(_SqliteEventBackedRepository, ReferenceDataSetRepository):
    """SQLite-backed adapter for ReferenceDataSetRepository."""

    def get_by_id(self, reference_data_set_id: str) -> Optional[ReferenceDataSet]:
        _require_non_empty_id(reference_data_set_id, "reference_data_set_id")
        payload = self._get_payload(
            session_id=_REFERENCE_DATA_SET_SESSION_ID,
            object_id=reference_data_set_id,
        )
        if payload is None:
            return None
        return ReferenceDataSet(
            calendar_version=str(payload["calendar_version"]),
            holiday_calendar_refs=tuple(payload["holiday_calendar_refs"]),
            day_count_convention_refs=tuple(payload["day_count_convention_refs"]),
            business_day_adjustment_refs=tuple(payload["business_day_adjustment_refs"]),
            settlement_convention_refs=tuple(payload["settlement_convention_refs"]),
            fixing_source_refs=tuple(payload["fixing_source_refs"]),
            exercise_convention_refs=tuple(payload["exercise_convention_refs"]),
            taxonomy_mapping_refs=tuple(payload["taxonomy_mapping_refs"]),
            reference_data_version_id=str(payload["reference_data_version_id"]),
        )

    def save(self, reference_data_set_id: str, reference_data_set: ReferenceDataSet) -> None:
        _require_non_empty_id(reference_data_set_id, "reference_data_set_id")
        _require_id_consistency(
            expected_id=reference_data_set_id,
            actual_id=reference_data_set.reference_data_version_id,
            field_name="reference_data_version_id",
        )
        payload: dict[str, object] = {
            "calendar_version": reference_data_set.calendar_version,
            "holiday_calendar_refs": list(reference_data_set.holiday_calendar_refs),
            "day_count_convention_refs": list(reference_data_set.day_count_convention_refs),
            "business_day_adjustment_refs": list(reference_data_set.business_day_adjustment_refs),
            "settlement_convention_refs": list(reference_data_set.settlement_convention_refs),
            "fixing_source_refs": list(reference_data_set.fixing_source_refs),
            "exercise_convention_refs": list(reference_data_set.exercise_convention_refs),
            "taxonomy_mapping_refs": list(reference_data_set.taxonomy_mapping_refs),
            "reference_data_version_id": reference_data_set.reference_data_version_id,
        }
        self._save_payload(
            session_id=_REFERENCE_DATA_SET_SESSION_ID,
            object_id=reference_data_set_id,
            payload=payload,
        )


class SqliteValuationPolicySetRepository(_SqliteEventBackedRepository, ValuationPolicySetRepository):
    """SQLite-backed adapter for ValuationPolicySetRepository."""

    def get_by_id(self, valuation_policy_set_id: str) -> Optional[ValuationPolicySet]:
        _require_non_empty_id(valuation_policy_set_id, "valuation_policy_set_id")
        payload = self._get_payload(
            session_id=_VALUATION_POLICY_SET_SESSION_ID,
            object_id=valuation_policy_set_id,
        )
        if payload is None:
            return None
        return ValuationPolicySet(
            valuation_policy_id=str(payload["valuation_policy_id"]),
            model_family=str(payload["model_family"]),
            pricing_engine_policy=str(payload["pricing_engine_policy"]),
            numeric_policy_id=str(payload["numeric_policy_id"]),
            tolerance_policy_id=str(payload["tolerance_policy_id"]),
            calibration_recipe_id=str(payload["calibration_recipe_id"]),
            approval_status=str(payload["approval_status"]),
            policy_version=str(payload["policy_version"]),
            policy_owner=str(payload["policy_owner"]),
            created_timestamp=_to_datetime(str(payload["created_timestamp"]), "created_timestamp"),
        )

    def save(self, valuation_policy_set_id: str, valuation_policy_set: ValuationPolicySet) -> None:
        _require_non_empty_id(valuation_policy_set_id, "valuation_policy_set_id")
        _require_id_consistency(
            expected_id=valuation_policy_set_id,
            actual_id=valuation_policy_set.valuation_policy_id,
            field_name="valuation_policy_id",
        )
        payload: dict[str, object] = {
            "valuation_policy_id": valuation_policy_set.valuation_policy_id,
            "model_family": valuation_policy_set.model_family,
            "pricing_engine_policy": valuation_policy_set.pricing_engine_policy,
            "numeric_policy_id": valuation_policy_set.numeric_policy_id,
            "tolerance_policy_id": valuation_policy_set.tolerance_policy_id,
            "calibration_recipe_id": valuation_policy_set.calibration_recipe_id,
            "approval_status": valuation_policy_set.approval_status,
            "policy_version": valuation_policy_set.policy_version,
            "policy_owner": valuation_policy_set.policy_owner,
            "created_timestamp": valuation_policy_set.created_timestamp.isoformat(),
        }
        self._save_payload(
            session_id=_VALUATION_POLICY_SET_SESSION_ID,
            object_id=valuation_policy_set_id,
            payload=payload,
        )


class SqliteValuationRunRepository(_SqliteEventBackedRepository, ValuationRunRepository):
    """SQLite-backed adapter for ValuationRunRepository."""

    def get_by_id(self, valuation_run_id: str) -> Optional[ValuationRun]:
        _require_non_empty_id(valuation_run_id, "valuation_run_id")
        payload = self._get_payload(
            session_id=_VALUATION_RUN_SESSION_ID,
            object_id=valuation_run_id,
        )
        if payload is None:
            return None
        return ValuationRun(
            valuation_run_id=str(payload["valuation_run_id"]),
            portfolio_state_id=str(payload["portfolio_state_id"]),
            market_snapshot_id=str(payload["market_snapshot_id"]),
            reference_data_set_id=str(payload["reference_data_set_id"]),
            valuation_policy_set_id=str(payload["valuation_policy_set_id"]),
            valuation_context_id=str(payload["valuation_context_id"]),
            scenario_set_id=str(payload["scenario_set_id"]),
            software_build_hash=str(payload["software_build_hash"]),
            run_timestamp=_to_datetime(str(payload["run_timestamp"]), "run_timestamp"),
            valuation_timestamp=_to_datetime(str(payload["valuation_timestamp"]), "valuation_timestamp"),
            run_purpose=str(payload["run_purpose"]),
        )

    def save(self, valuation_run: ValuationRun) -> None:
        payload: dict[str, object] = {
            "valuation_run_id": valuation_run.valuation_run_id,
            "portfolio_state_id": valuation_run.portfolio_state_id,
            "market_snapshot_id": valuation_run.market_snapshot_id,
            "reference_data_set_id": valuation_run.reference_data_set_id,
            "valuation_policy_set_id": valuation_run.valuation_policy_set_id,
            "valuation_context_id": valuation_run.valuation_context_id,
            "scenario_set_id": valuation_run.scenario_set_id,
            "software_build_hash": valuation_run.software_build_hash,
            "run_timestamp": valuation_run.run_timestamp.isoformat(),
            "valuation_timestamp": valuation_run.valuation_timestamp.isoformat(),
            "run_purpose": valuation_run.run_purpose,
        }
        self._save_payload(
            session_id=_VALUATION_RUN_SESSION_ID,
            object_id=valuation_run.valuation_run_id,
            payload=payload,
        )


class SqliteModelRegistryRepository(_SqliteEventBackedRepository, ModelRegistryRepository):
    """SQLite-backed adapter for ModelRegistryRepository."""

    def get_by_model_id(self, model_id: str) -> Optional[ModelRegistryEntry]:
        _require_non_empty_id(model_id, "model_id")
        payload = self._get_payload(
            session_id=_MODEL_REGISTRY_SESSION_ID,
            object_id=model_id,
        )
        if payload is None:
            return None

        capabilities = tuple(
            ModelCapability(
                instrument_family=str(cap["instrument_family"]),
                exercise_style=str(cap["exercise_style"]),
                measure=str(cap["measure"]),
            )
            for cap in payload["supported_capabilities"]
        )

        return ModelRegistryEntry(
            model_id=str(payload["model_id"]),
            semantic_version=str(payload["semantic_version"]),
            implementation_version=str(payload["implementation_version"]),
            validation_status=str(payload["validation_status"]),
            owner=str(payload["owner"]),
            approval_date=datetime.date.fromisoformat(str(payload["approval_date"])),
            benchmark_pack_id=str(payload["benchmark_pack_id"]),
            known_limitations=tuple(str(item) for item in payload["known_limitations"]),
            numeric_policy_id=str(payload["numeric_policy_id"]),
            supported_capabilities=capabilities,
        )

    def save(self, model_entry: ModelRegistryEntry) -> None:
        payload: dict[str, object] = {
            "model_id": model_entry.model_id,
            "semantic_version": model_entry.semantic_version,
            "implementation_version": model_entry.implementation_version,
            "validation_status": model_entry.validation_status,
            "owner": model_entry.owner,
            "approval_date": model_entry.approval_date.isoformat(),
            "benchmark_pack_id": model_entry.benchmark_pack_id,
            "known_limitations": list(model_entry.known_limitations),
            "numeric_policy_id": model_entry.numeric_policy_id,
            "supported_capabilities": [
                {
                    "instrument_family": capability.instrument_family,
                    "exercise_style": capability.exercise_style,
                    "measure": capability.measure,
                }
                for capability in model_entry.supported_capabilities
            ],
        }
        self._save_payload(
            session_id=_MODEL_REGISTRY_SESSION_ID,
            object_id=model_entry.model_id,
            payload=payload,
        )


__all__ = [
    "SqliteModelRegistryRepository",
    "SqliteReferenceDataSetRepository",
    "SqliteValuationPolicySetRepository",
    "SqliteValuationRunRepository",
]
