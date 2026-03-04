from __future__ import annotations

import datetime
from decimal import Decimal

from core.services.advisory_input_contract_v1 import normalize_advisory_input_v1
from core.services.exposure_adapter_v1 import build_risk_request_from_advisory_v1


def _payload() -> dict:
    return {
        "contract_version": "v1",
        "company_id": "acme",
        "snapshot_id": "snap-001",
        "scenario_template_id": "scn-template-a",
        "exposures": [
            {
                "currency_pair": "USD/ILS",
                "direction": "receivable",
                "notional": "1000000",
                "maturity_date": "2026-12-31",
            },
            {
                "currency_pair": "EUR/USD",
                "direction": "payable",
                "notional": "500000",
                "maturity_date": "2026-06-30",
                "hedge_ratio": "0.4",
            },
        ],
    }


def _normalize(payload: dict):
    return normalize_advisory_input_v1(payload)


def test_mapping_correctness() -> None:
    contracts, _ = build_risk_request_from_advisory_v1(_normalize(_payload()))

    assert len(contracts) == 2
    contract_list = [contracts[k] for k in sorted(contracts)]
    eurusd = next(c for c in contract_list if c.base_currency == "EUR" and c.quote_currency == "USD")
    usdils = next(c for c in contract_list if c.base_currency == "USD" and c.quote_currency == "ILS")

    assert eurusd.forward_date == datetime.date(2026, 6, 30)
    assert eurusd.direction == "pay_foreign_receive_domestic"
    assert usdils.forward_date == datetime.date(2026, 12, 31)
    assert usdils.direction == "receive_foreign_pay_domestic"


def test_hedge_ratio_scales_notional() -> None:
    contracts, _ = build_risk_request_from_advisory_v1(_normalize(_payload()))
    eurusd = next(c for c in contracts.values() if c.base_currency == "EUR" and c.quote_currency == "USD")

    assert eurusd.notional == float(Decimal("500000") * Decimal("0.4"))


def test_deterministic_instrument_ids() -> None:
    normalized = _normalize(_payload())
    contracts_a, request_a = build_risk_request_from_advisory_v1(normalized)
    contracts_b, request_b = build_risk_request_from_advisory_v1(normalized)

    assert tuple(sorted(contracts_a.keys())) == tuple(sorted(contracts_b.keys()))
    assert request_a["instrument_ids"] == request_b["instrument_ids"]


def test_ordering_determinism() -> None:
    p1 = _payload()
    p2 = _payload()
    p2["exposures"] = list(reversed(p2["exposures"]))

    contracts_1, request_1 = build_risk_request_from_advisory_v1(_normalize(p1))
    contracts_2, request_2 = build_risk_request_from_advisory_v1(_normalize(p2))

    assert tuple(contracts_1.keys()) == tuple(contracts_2.keys())
    assert request_1 == request_2


def test_identical_input_identical_contracts() -> None:
    normalized = _normalize(_payload())
    contracts_1, request_1 = build_risk_request_from_advisory_v1(normalized)
    contracts_2, request_2 = build_risk_request_from_advisory_v1(normalized)

    assert contracts_1 == contracts_2
    assert request_1 == request_2


def test_integration_ready_risk_request_structure() -> None:
    _, risk_request = build_risk_request_from_advisory_v1(_normalize(_payload()))

    assert set(risk_request.keys()) == {
        "snapshot_id",
        "scenario_template_id",
        "instrument_ids",
        "valuation_context",
    }
    assert risk_request["snapshot_id"] == "snap-001"
    assert risk_request["scenario_template_id"] == "scn-template-a"
    assert isinstance(risk_request["instrument_ids"], tuple)
    assert risk_request["instrument_ids"] == tuple(sorted(risk_request["instrument_ids"]))
    assert risk_request["valuation_context"] == {"domestic_currency": "USD"}
