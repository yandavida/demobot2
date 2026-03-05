from __future__ import annotations

import pytest

from core.portfolio.advisory_payload_artifact_store_v1 import put_advisory_payload_artifact_v1
from core.portfolio.portfolio_ref_resolver_v1 import PortfolioResolutionError
from core.portfolio.portfolio_ref_resolver_v1 import resolve_portfolio_ref_to_advisory_payload_v1
from core.services.advisory_input_contract_v1 import normalize_advisory_input_v1


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


def test_unsupported_format_raises() -> None:
    with pytest.raises(PortfolioResolutionError, match="unsupported_portfolio_ref_format"):
        resolve_portfolio_ref_to_advisory_payload_v1("foo")


def test_missing_artifact_raises() -> None:
    with pytest.raises(PortfolioResolutionError, match=r"portfolio_artifact_not_found:"):
        resolve_portfolio_ref_to_advisory_payload_v1("artifact:does-not-exist")


def test_success_path_uses_ssot_artifact_and_valid_payload() -> None:
    artifact_id = put_advisory_payload_artifact_v1(_payload())
    payload = resolve_portfolio_ref_to_advisory_payload_v1(f"artifact:{artifact_id}")

    assert payload is not None
    normalized = normalize_advisory_input_v1(payload)
    assert normalized.contract_version == "v1"
