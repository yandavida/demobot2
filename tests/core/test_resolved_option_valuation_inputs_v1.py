from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.option_runtime_contract_v1 import OptionRuntimeContractV1
from core.contracts.resolved_option_valuation_inputs_v1 import NumericalPolicySnapshotV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedConventionBasisV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedCurveInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedOptionValuationInputsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedRatePointV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedSpotInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityPointV1


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


def _spot() -> ResolvedSpotInputV1:
    return ResolvedSpotInputV1(
        underlying_instrument_ref="USD/ILS",
        spot="3.70",
    )


def _convention_basis() -> ResolvedConventionBasisV1:
    return ResolvedConventionBasisV1(
        day_count_basis="ACT/365F",
        calendar_set=("IL-TASE", "US-NYFED"),
        settlement_conventions=("spot+2",),
        premium_conventions=("premium-settle-t+2",),
    )


def _numeric_policy() -> NumericalPolicySnapshotV1:
    return NumericalPolicySnapshotV1(
        numeric_policy_id="numeric.policy.v1",
        tolerance="0.000001",
        max_iterations=200,
        rounding_decimals=8,
    )


def _domestic_curve() -> ResolvedCurveInputV1:
    return ResolvedCurveInputV1(
        curve_id="curve.ils.ois.v1",
        points=(
            ResolvedRatePointV1(tenor_label="1M", zero_rate="0.04"),
            ResolvedRatePointV1(tenor_label="6M", zero_rate="0.041"),
        ),
    )


def _foreign_curve() -> ResolvedCurveInputV1:
    return ResolvedCurveInputV1(
        curve_id="curve.usd.ois.v1",
        points=(
            ResolvedRatePointV1(tenor_label="1M", zero_rate="0.05"),
            ResolvedRatePointV1(tenor_label="6M", zero_rate="0.051"),
        ),
    )


def _vol_surface() -> ResolvedVolatilityInputV1:
    return ResolvedVolatilityInputV1(
        surface_id="surface.fx.usdils.v1",
        points=(
            ResolvedVolatilityPointV1(tenor_label="1M", strike="3.60", implied_vol="0.11"),
            ResolvedVolatilityPointV1(tenor_label="3M", strike="3.70", implied_vol="0.12"),
        ),
    )


def test_constructs_generic_resolved_inputs() -> None:
    resolved = ResolvedOptionValuationInputsV1(
        option_contract=_generic_contract(),
        valuation_timestamp=datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
        resolved_underlying_input=_spot(),
        resolved_convention_basis=_convention_basis(),
        numerical_policy_snapshot=_numeric_policy(),
        resolved_basis_hash="sha256:abc123",
    )

    assert resolved.option_contract.contract_id == "opt-rt-001"
    assert resolved.resolved_underlying_input.spot == Decimal("3.70")
    assert resolved.resolved_convention_basis.day_count_basis == "ACT/365F"


def test_constructs_fx_resolved_inputs() -> None:
    resolved = ResolvedFxOptionValuationInputsV1(
        fx_option_contract=_fx_contract(),
        valuation_timestamp=datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
        spot=_spot(),
        domestic_curve=_domestic_curve(),
        foreign_curve=_foreign_curve(),
        volatility_surface=_vol_surface(),
        day_count_basis="ACT/365F",
        calendar_set=("IL-TASE", "US-NYFED"),
        settlement_conventions=("spot+2",),
        premium_conventions=("premium-settle-t+2",),
        numerical_policy_snapshot=_numeric_policy(),
        resolved_basis_hash="sha256:def456",
    )

    assert resolved.fx_option_contract.contract_id == "fx-opt-001"
    assert resolved.domestic_curve.curve_id == "curve.ils.ois.v1"
    assert resolved.foreign_curve.curve_id == "curve.usd.ois.v1"
    assert resolved.volatility_surface.surface_id == "surface.fx.usdils.v1"


def test_resolved_inputs_are_immutable() -> None:
    resolved = ResolvedOptionValuationInputsV1(
        option_contract=_generic_contract(),
        valuation_timestamp=datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
        resolved_underlying_input=_spot(),
        resolved_convention_basis=_convention_basis(),
        numerical_policy_snapshot=_numeric_policy(),
        resolved_basis_hash="sha256:abc123",
    )

    with pytest.raises(FrozenInstanceError):
        resolved.resolved_basis_hash = "sha256:other"


def test_rejects_ids_only_fallback_shape_and_loader_handles() -> None:
    with pytest.raises(TypeError):
        ResolvedOptionValuationInputsV1(
            option_contract=_generic_contract(),
            valuation_timestamp=datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
            resolved_underlying_input=_spot(),
            resolved_convention_basis=_convention_basis(),
            numerical_policy_snapshot=_numeric_policy(),
            resolved_basis_hash="sha256:abc123",
            market_snapshot_id="mkt.snap.id.only",
        )

    with pytest.raises(ValueError, match="spot"):
        ResolvedFxOptionValuationInputsV1(
            fx_option_contract=_fx_contract(),
            valuation_timestamp=datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
            spot=lambda: _spot(),
            domestic_curve=_domestic_curve(),
            foreign_curve=_foreign_curve(),
            volatility_surface=_vol_surface(),
            day_count_basis="ACT/365F",
            calendar_set=("IL-TASE",),
            settlement_conventions=("spot+2",),
            premium_conventions=("premium-settle-t+2",),
            numerical_policy_snapshot=_numeric_policy(),
            resolved_basis_hash="sha256:def456",
        )


def test_rejects_pricing_result_payload_fields() -> None:
    with pytest.raises(TypeError):
        ResolvedFxOptionValuationInputsV1(
            fx_option_contract=_fx_contract(),
            valuation_timestamp=datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
            spot=_spot(),
            domestic_curve=_domestic_curve(),
            foreign_curve=_foreign_curve(),
            volatility_surface=_vol_surface(),
            day_count_basis="ACT/365F",
            calendar_set=("IL-TASE",),
            settlement_conventions=("spot+2",),
            premium_conventions=("premium-settle-t+2",),
            numerical_policy_snapshot=_numeric_policy(),
            resolved_basis_hash="sha256:def456",
            price_result="100.0",
        )


def test_rejects_invalid_structural_values() -> None:
    with pytest.raises(ValueError, match="valuation_timestamp"):
        ResolvedOptionValuationInputsV1(
            option_contract=_generic_contract(),
            valuation_timestamp="2026-12-31T10:00:00Z",
            resolved_underlying_input=_spot(),
            resolved_convention_basis=_convention_basis(),
            numerical_policy_snapshot=_numeric_policy(),
            resolved_basis_hash="sha256:abc123",
        )

    with pytest.raises(ValueError, match="points"):
        ResolvedCurveInputV1(curve_id="curve.ils.ois.v1", points=())

    with pytest.raises(ValueError, match="implied_vol"):
        ResolvedVolatilityPointV1(tenor_label="1M", strike="3.65", implied_vol="0")
