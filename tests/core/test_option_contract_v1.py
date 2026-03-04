from __future__ import annotations

import datetime
import json

import pytest

from core.contracts.option_contract_v1 import OptionContractV1


def _contract(**overrides) -> OptionContractV1:
    payload = {
        "instrument_id": "opt-eur-usdils-001",
        "underlying": "USD/ILS",
        "option_type": "call",
        "strike": "3.6500",
        "expiry": datetime.datetime(2026, 12, 31, 10, 0, 0, tzinfo=datetime.timezone.utc),
        "notional": "1000000",
        "domestic_ccy": "ils",
        "foreign_ccy": "usd",
        "time_fraction_policy_id": "ACT_365F",
        "contract_version": "v1",
    }
    payload.update(overrides)
    return OptionContractV1(**payload)


def test_roundtrip_serialize_deserialize_preserves_equality() -> None:
    contract = _contract()

    encoded = contract.to_dict()
    decoded = OptionContractV1.from_dict(encoded)

    assert decoded == contract


def test_canonical_json_serialization_is_deterministic() -> None:
    contract_a = _contract()
    contract_b = _contract(domestic_ccy="ILS", foreign_ccy="USD")

    json_a = contract_a.to_canonical_json()
    json_b = contract_b.to_canonical_json()

    assert json_a == json_b
    assert json.loads(json_a)["strike"] == "3.6500"
    assert json.loads(json_a)["notional"] == "1000000"


def test_instrument_id_is_required_non_empty() -> None:
    with pytest.raises(ValueError, match="instrument_id"):
        _contract(instrument_id="")
