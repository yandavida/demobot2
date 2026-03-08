from __future__ import annotations

import pytest

from core.portfolio.advisory_payload_artifact_store_v1 import get_advisory_payload_artifact_lineage_v1
from core.portfolio.advisory_payload_artifact_store_v1 import get_advisory_payload_artifact_v1
from core.portfolio.advisory_payload_artifact_store_v1 import put_advisory_payload_artifact_v1


def _payload() -> dict:
    return {
        "contract_version": "v1",
        "company_id": "treasury-demo",
        "snapshot_id": "snap-usdils-20260304",
        "scenario_template_id": "usdils_spot_pm5",
        "exposures": [
            {
                "currency_pair": "USD/ILS",
                "direction": "receivable",
                "notional": "3000000",
                "maturity_date": "2026-06-02",
                "hedge_ratio": "0.60",
            }
        ],
    }


def test_lineage_round_trip_preserves_valuation_run_id() -> None:
    artifact_id = put_advisory_payload_artifact_v1(
        _payload(),
        valuation_run_id="vr-2026-03-08-001",
    )

    lineage = get_advisory_payload_artifact_lineage_v1(artifact_id)

    assert lineage is not None
    assert lineage["artifact_id"] == artifact_id
    assert lineage["valuation_run_id"] == "vr-2026-03-08-001"


def test_payload_remains_separate_from_lineage_metadata() -> None:
    artifact_id = put_advisory_payload_artifact_v1(
        _payload(),
        valuation_run_id="vr-2026-03-08-002",
    )

    payload = get_advisory_payload_artifact_v1(artifact_id)
    lineage = get_advisory_payload_artifact_lineage_v1(artifact_id)

    assert "valuation_run_id" not in payload
    assert lineage is not None
    assert payload["contract_version"] == "v1"


def test_repeated_save_with_same_payload_and_lineage_is_deterministic() -> None:
    payload = _payload()
    run_id = "vr-2026-03-08-003"

    artifact_id_1 = put_advisory_payload_artifact_v1(payload, valuation_run_id=run_id)
    artifact_id_2 = put_advisory_payload_artifact_v1(payload, valuation_run_id=run_id)

    lineage_1 = get_advisory_payload_artifact_lineage_v1(artifact_id_1)
    lineage_2 = get_advisory_payload_artifact_lineage_v1(artifact_id_2)

    assert artifact_id_1 == artifact_id_2
    assert lineage_1 == lineage_2


def test_rejects_invalid_valuation_run_id() -> None:
    with pytest.raises(ValueError, match="valuation_run_id"):
        put_advisory_payload_artifact_v1(_payload(), valuation_run_id="   ")
