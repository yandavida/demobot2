from __future__ import annotations

from decimal import Decimal

import pytest

from core.services.advisory_input_contract_v1 import AdvisoryInputValidationError
from core.services.advisory_input_contract_v1 import normalize_advisory_input_v1


def _payload() -> dict:
    return {
        "contract_version": "v1",
        "company_id": "acme-co",
        "snapshot_id": "snap-001",
        "scenario_template_id": "scn-fx-base",
        "exposures": [
            {
                "currency_pair": "usd/ils",
                "direction": "receivable",
                "notional": "1000000.00",
                "maturity_date": "2026-12-31",
                "hedge_ratio": "0.5",
            },
            {
                "currency_pair": "EUR/USD",
                "direction": "payable",
                "notional": 250000,
                "maturity_date": "2026-06-30",
            },
        ],
    }


def test_valid_payload_normalizes_correctly() -> None:
    normalized = normalize_advisory_input_v1(_payload())

    assert normalized.contract_version == "v1"
    assert normalized.company_id == "acme-co"
    assert normalized.snapshot_id == "snap-001"
    assert normalized.scenario_template_id == "scn-fx-base"
    assert len(normalized.exposures) == 2
    assert normalized.exposures[0].currency_pair == "EUR/USD"
    assert normalized.exposures[1].currency_pair == "USD/ILS"


def test_row_ordering_determinism() -> None:
    p1 = _payload()
    p2 = _payload()
    p2["exposures"] = list(reversed(p2["exposures"]))

    n1 = normalize_advisory_input_v1(p1)
    n2 = normalize_advisory_input_v1(p2)

    assert n1 == n2


@pytest.mark.parametrize(
    "path, value",
    [
        ("currency_pair", ""),
        ("direction", "invalid"),
        ("notional", 0),
        ("maturity_date", ""),
    ],
)
def test_schema_validation_errors(path: str, value) -> None:
    payload = _payload()
    payload["exposures"][0][path] = value

    with pytest.raises(AdvisoryInputValidationError):
        normalize_advisory_input_v1(payload)


def test_numeric_normalization() -> None:
    normalized = normalize_advisory_input_v1(_payload())
    row = next(r for r in normalized.exposures if r.currency_pair == "USD/ILS")

    assert isinstance(row.notional, Decimal)
    assert row.notional == Decimal("1000000.00")
    assert isinstance(row.hedge_ratio, Decimal)
    assert row.hedge_ratio == Decimal("0.5")


def test_identical_payload_same_output() -> None:
    payload = _payload()
    out1 = normalize_advisory_input_v1(payload)
    out2 = normalize_advisory_input_v1(payload)

    assert out1 == out2
