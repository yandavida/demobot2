from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError
from dataclasses import fields

import pytest

from core.contracts.valuation_run import ValuationRun


def _valuation_run(**overrides) -> ValuationRun:
    payload = {
        "valuation_run_id": "vr-2026-03-08-001",
        "portfolio_state_id": "ps-2026-03-08-001",
        "market_snapshot_id": "ms-2026-03-08-001",
        "reference_data_set_id": "rds-2026-03-08-001",
        "valuation_policy_set_id": "vps-2026-03-08-001",
        "valuation_context_id": "vc-2026-03-08-001",
        "scenario_set_id": "scn-2026-03-08-001",
        "software_build_hash": "build-abc123def",
        "run_timestamp": datetime.datetime(2026, 3, 8, 12, 0, 0, tzinfo=datetime.timezone.utc),
        "valuation_timestamp": datetime.datetime(
            2026,
            3,
            8,
            11,
            59,
            0,
            tzinfo=datetime.timezone.utc,
        ),
        "run_purpose": "risk_snapshot",
    }
    payload.update(overrides)
    return ValuationRun(**payload)


def test_valuation_run_construction() -> None:
    run = _valuation_run()

    assert run.valuation_run_id == "vr-2026-03-08-001"
    assert run.valuation_context_id == "vc-2026-03-08-001"
    assert run.scenario_set_id == "scn-2026-03-08-001"


def test_valuation_run_is_immutable() -> None:
    run = _valuation_run()

    with pytest.raises(FrozenInstanceError):
        run.run_purpose = "pricing"


def test_valuation_run_requires_all_fields() -> None:
    with pytest.raises(TypeError):
        ValuationRun(
            valuation_run_id="vr-2026-03-08-001",
            portfolio_state_id="ps-2026-03-08-001",
            market_snapshot_id="ms-2026-03-08-001",
            reference_data_set_id="rds-2026-03-08-001",
            valuation_policy_set_id="vps-2026-03-08-001",
            valuation_context_id="vc-2026-03-08-001",
            scenario_set_id="scn-2026-03-08-001",
            software_build_hash="build-abc123def",
            run_timestamp=datetime.datetime(
                2026,
                3,
                8,
                12,
                0,
                0,
                tzinfo=datetime.timezone.utc,
            ),
            valuation_timestamp=datetime.datetime(
                2026,
                3,
                8,
                11,
                59,
                0,
                tzinfo=datetime.timezone.utc,
            ),
        )


def test_valuation_run_lineage_fields_present() -> None:
    names = {f.name for f in fields(ValuationRun)}

    assert "portfolio_state_id" in names
    assert "market_snapshot_id" in names
    assert "reference_data_set_id" in names
    assert "valuation_policy_set_id" in names
    assert "valuation_context_id" in names
    assert "scenario_set_id" in names


def test_valuation_run_has_no_payload_fields() -> None:
    names = {f.name for f in fields(ValuationRun)}

    forbidden_substrings = ("payload", "result", "artifact")
    assert not any(any(token in name for token in forbidden_substrings) for name in names)
