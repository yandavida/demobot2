from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError

import pytest

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.option_lifecycle_domain_v1 import OptionLifecycleEventRefV1
from core.contracts.option_lifecycle_domain_v1 import OptionLifecycleOutcomeV1
from core.contracts.option_lifecycle_domain_v1 import OptionPostEventRecomputeRefV1
from core.contracts.option_lifecycle_domain_v1 import OptionPremiumCashflowRefV1
from core.contracts.option_lifecycle_domain_v1 import OptionSettlementOutcomeV1
from core.contracts.option_runtime_contract_v1 import OptionRuntimeContractV1


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


def _event() -> OptionLifecycleEventRefV1:
    return OptionLifecycleEventRefV1(
        event_id="evt-001",
        contract_id="opt-rt-001",
        event_type="exercise",
        event_timestamp=datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
        valuation_context_id="valuation.context.2026-12-31-run-001",
    )


def _premium() -> OptionPremiumCashflowRefV1:
    return OptionPremiumCashflowRefV1(
        premium_cashflow_id="prem-001",
        contract_id="opt-rt-001",
        premium_currency="usd",
        premium_payment_date=datetime.date(2026, 6, 1),
        premium_amount="10000.25",
    )


def _settlement() -> OptionSettlementOutcomeV1:
    return OptionSettlementOutcomeV1(
        settlement_outcome_id="settle-001",
        contract_id="opt-rt-001",
        settlement_style="deliverable",
        settlement_date=datetime.date(2027, 1, 4),
        settlement_currency="usd",
        settlement_amount="15000",
    )


def _recompute() -> OptionPostEventRecomputeRefV1:
    return OptionPostEventRecomputeRefV1(
        recompute_ref_id="recomp-001",
        source_event_id="evt-001",
        valuation_context_id="valuation.context.2026-12-31-run-001",
        valuation_dependency_bundle_id="valdep-001",
    )


def test_constructs_lifecycle_outcome_with_generic_contract() -> None:
    outcome = OptionLifecycleOutcomeV1(
        option_contract=_generic_contract(),
        lifecycle_event=_event(),
        outcome_state="exercised",
        premium_cashflow_ref=_premium(),
        settlement_outcome=_settlement(),
        post_event_recompute_ref=_recompute(),
    )

    assert outcome.outcome_state == "exercised"
    assert outcome.lifecycle_event.event_type == "exercise"


def test_constructs_lifecycle_outcome_with_fx_contract() -> None:
    outcome = OptionLifecycleOutcomeV1(
        option_contract=_fx_contract(),
        lifecycle_event=_event(),
        outcome_state="settled",
        premium_cashflow_ref=_premium(),
        settlement_outcome=_settlement(),
        post_event_recompute_ref=_recompute(),
    )

    assert isinstance(outcome.option_contract, FxOptionRuntimeContractV1)


def test_lifecycle_contracts_are_immutable() -> None:
    event = _event()

    with pytest.raises(FrozenInstanceError):
        event.event_type = "expiry"


def test_explicit_lifecycle_vocabulary_is_enforced() -> None:
    with pytest.raises(ValueError, match="event_type"):
        OptionLifecycleEventRefV1(
            event_id="evt-001",
            contract_id="opt-rt-001",
            event_type="roll",
            event_timestamp=datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
            valuation_context_id="valuation.context.2026-12-31-run-001",
        )

    with pytest.raises(ValueError, match="outcome_state"):
        OptionLifecycleOutcomeV1(
            option_contract=_generic_contract(),
            lifecycle_event=_event(),
            outcome_state="pending",
            premium_cashflow_ref=_premium(),
            settlement_outcome=_settlement(),
            post_event_recompute_ref=_recompute(),
        )


def test_premium_cashflow_semantics_are_explicit() -> None:
    premium = _premium()

    assert premium.premium_currency == "USD"
    assert premium.premium_amount == 10000.25

    with pytest.raises(ValueError, match="premium_amount"):
        OptionPremiumCashflowRefV1(
            premium_cashflow_id="prem-001",
            contract_id="opt-rt-001",
            premium_currency="usd",
            premium_payment_date=datetime.date(2026, 6, 1),
            premium_amount="0",
        )


def test_settlement_outcome_semantics_are_explicit() -> None:
    with pytest.raises(ValueError, match="settlement_style"):
        OptionSettlementOutcomeV1(
            settlement_outcome_id="settle-001",
            contract_id="opt-rt-001",
            settlement_style="cash",
            settlement_date=datetime.date(2027, 1, 4),
            settlement_currency="usd",
            settlement_amount="15000",
        )


def test_post_event_recompute_reference_semantics_are_explicit() -> None:
    with pytest.raises(ValueError, match="valuation_dependency_bundle_id"):
        OptionPostEventRecomputeRefV1(
            recompute_ref_id="recomp-001",
            source_event_id="evt-001",
            valuation_context_id="valuation.context.2026-12-31-run-001",
            valuation_dependency_bundle_id="",
        )


def test_rejects_invalid_structural_values_and_arbitrary_payloads() -> None:
    with pytest.raises(ValueError, match="event_timestamp"):
        OptionLifecycleEventRefV1(
            event_id="evt-001",
            contract_id="opt-rt-001",
            event_type="expiry",
            event_timestamp="2026-12-31T10:00:00Z",
            valuation_context_id="valuation.context.2026-12-31-run-001",
        )

    with pytest.raises(TypeError):
        OptionLifecycleOutcomeV1(
            option_contract=_generic_contract(),
            lifecycle_event=_event(),
            outcome_state="exercised",
            premium_cashflow_ref=_premium(),
            settlement_outcome=_settlement(),
            post_event_recompute_ref=_recompute(),
            price_result="10.5",
        )
