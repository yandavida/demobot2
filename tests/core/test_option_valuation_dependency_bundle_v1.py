from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError

import pytest

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.option_runtime_contract_v1 import OptionRuntimeContractV1
from core.contracts.option_valuation_dependency_bundle_v1 import OptionValuationDependencyBundleV1


def _generic_contract() -> OptionRuntimeContractV1:
    return OptionRuntimeContractV1(
        contract_id="opt-rt-001",
        underlying_instrument_ref="USD/ILS",
        option_type="call",
        exercise_style="european",
        strike="3.65",
        expiry_date=datetime.date(2026, 12, 31),
        notional="1000000",
        notional_currency="usd",
    )


def _fx_contract() -> FxOptionRuntimeContractV1:
    return FxOptionRuntimeContractV1(
        contract_id="fx-opt-001",
        currency_pair_orientation="base_per_quote",
        base_currency="usd",
        quote_currency="ils",
        option_type="call",
        exercise_style="european",
        strike="3.65",
        expiry_date=datetime.date(2026, 12, 31),
        expiry_cutoff_time=datetime.time(10, 0, 0),
        expiry_cutoff_timezone="Asia/Jerusalem",
        notional="1000000",
        notional_currency_semantics="base_currency",
        premium_currency="usd",
        premium_payment_date=datetime.date(2026, 6, 1),
        settlement_style="deliverable",
        settlement_date=datetime.date(2027, 1, 4),
        settlement_calendar_refs=("IL-TASE", "US-NYFED"),
        fixing_source="WM/Reuters 4pm",
        fixing_date=datetime.date(2026, 12, 31),
        domestic_curve_id="curve.ils.ois.v1",
        foreign_curve_id="curve.usd.ois.v1",
        volatility_surface_quote_convention="delta-neutral-vol",
    )


def _bundle(contract: OptionRuntimeContractV1 | FxOptionRuntimeContractV1, **overrides: object) -> OptionValuationDependencyBundleV1:
    payload: dict[str, object] = {
        "option_contract": contract,
        "market_snapshot_id": "mkt.snap.2026-12-31t10:00:00z",
        "reference_data_set_id": "reference.data.v1",
        "valuation_policy_set_id": "valuation.policy.v1",
        "valuation_context_id": "valuation.context.2026-12-31-run-001",
    }
    payload.update(overrides)
    return OptionValuationDependencyBundleV1(**payload)


def test_constructs_with_generic_option_contract() -> None:
    bundle = _bundle(_generic_contract())

    assert bundle.market_snapshot_id == "mkt.snap.2026-12-31t10:00:00z"
    assert bundle.reference_data_set_id == "reference.data.v1"
    assert bundle.valuation_policy_set_id == "valuation.policy.v1"
    assert bundle.valuation_context_id == "valuation.context.2026-12-31-run-001"


def test_constructs_with_fx_option_contract() -> None:
    bundle = _bundle(_fx_contract())

    assert isinstance(bundle.option_contract, FxOptionRuntimeContractV1)


def test_bundle_is_immutable() -> None:
    bundle = _bundle(_generic_contract())

    with pytest.raises(FrozenInstanceError):
        bundle.market_snapshot_id = "mkt.snap.new"


def test_required_dependency_refs_are_explicit() -> None:
    with pytest.raises(ValueError, match="market_snapshot_id"):
        _bundle(_generic_contract(), market_snapshot_id="")

    with pytest.raises(ValueError, match="reference_data_set_id"):
        _bundle(_generic_contract(), reference_data_set_id="")

    with pytest.raises(ValueError, match="valuation_policy_set_id"):
        _bundle(_generic_contract(), valuation_policy_set_id="")

    with pytest.raises(ValueError, match="valuation_context_id"):
        _bundle(_generic_contract(), valuation_context_id="")


def test_rejects_invalid_contract_object_type() -> None:
    with pytest.raises(ValueError, match="option_contract"):
        _bundle(contract="not-a-contract")


def test_rejects_pricing_result_payload_fields() -> None:
    with pytest.raises(TypeError):
        _bundle(_generic_contract(), price_result="100.0")
