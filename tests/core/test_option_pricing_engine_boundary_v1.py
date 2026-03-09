from __future__ import annotations

import datetime

import pytest

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.option_pricing_engine_boundary_v1 import ensure_pure_option_pricing_input_v1
from core.contracts.option_valuation_dependency_bundle_v1 import OptionValuationDependencyBundleV1
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


class FakeRepository:
    def get_by_id(self, _value: str) -> None:
        return None


class FakeLoader:
    def get_by_numeric_policy_id(self, _value: str) -> None:
        return None


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


def _resolved_generic_inputs() -> ResolvedOptionValuationInputsV1:
    return ResolvedOptionValuationInputsV1(
        option_contract=_generic_contract(),
        valuation_timestamp=datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
        resolved_underlying_input=ResolvedSpotInputV1(
            underlying_instrument_ref="USD/ILS",
            spot="3.70",
        ),
        resolved_convention_basis=ResolvedConventionBasisV1(
            day_count_basis="ACT/365F",
            calendar_set=("IL-TASE", "US-NYFED"),
            settlement_conventions=("spot+2",),
            premium_conventions=("premium-settle-t+2",),
        ),
        numerical_policy_snapshot=NumericalPolicySnapshotV1(
            numeric_policy_id="numeric.policy.v1",
            tolerance="0.000001",
            max_iterations=200,
            rounding_decimals=8,
        ),
        resolved_basis_hash="sha256:abc123",
    )


def _resolved_fx_inputs() -> ResolvedFxOptionValuationInputsV1:
    valuation_ts = datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc)
    return ResolvedFxOptionValuationInputsV1(
        fx_option_contract=_fx_contract(),
        valuation_timestamp=valuation_ts,
        spot=ResolvedSpotInputV1(underlying_instrument_ref="USD/ILS", spot="3.70"),
        domestic_curve=ResolvedCurveInputV1(
            curve_id="curve.ils.ois.v1",
            quote_convention="zero_rate",
            interpolation_method="linear_zero_rate",
            extrapolation_policy="flat_forward",
            basis_timestamp=valuation_ts,
            source_lineage_ref="market_snapshot:mkt.snap.001:curve:curve.ils.ois.v1",
            points=(
                ResolvedRatePointV1(tenor_label="1M", zero_rate="0.04"),
                ResolvedRatePointV1(tenor_label="6M", zero_rate="0.041"),
            ),
        ),
        foreign_curve=ResolvedCurveInputV1(
            curve_id="curve.usd.ois.v1",
            quote_convention="zero_rate",
            interpolation_method="linear_zero_rate",
            extrapolation_policy="flat_forward",
            basis_timestamp=valuation_ts,
            source_lineage_ref="market_snapshot:mkt.snap.001:curve:curve.usd.ois.v1",
            points=(
                ResolvedRatePointV1(tenor_label="1M", zero_rate="0.05"),
                ResolvedRatePointV1(tenor_label="6M", zero_rate="0.051"),
            ),
        ),
        volatility_surface=ResolvedVolatilityInputV1(
            surface_id="surface.fx.usdils.v1",
            quote_convention="implied_vol",
            interpolation_method="surface_quote_map_lookup",
            extrapolation_policy="none",
            basis_timestamp=valuation_ts,
            source_lineage_ref="market_snapshot:mkt.snap.001:vol_surface:surface.fx.usdils.v1",
            points=(
                ResolvedVolatilityPointV1(tenor_label="1M", strike="3.60", implied_vol="0.11"),
            ),
        ),
        day_count_basis="ACT/365F",
        calendar_set=("IL-TASE", "US-NYFED"),
        settlement_conventions=("spot+2",),
        premium_conventions=("premium-settle-t+2",),
        numerical_policy_snapshot=NumericalPolicySnapshotV1(
            numeric_policy_id="numeric.policy.v1",
            tolerance="0.000001",
            max_iterations=200,
            rounding_decimals=8,
        ),
        resolved_basis_hash="sha256:def456",
    )


def test_accepts_resolved_option_inputs() -> None:
    resolved = _resolved_generic_inputs()

    accepted = ensure_pure_option_pricing_input_v1(resolved)

    assert accepted == resolved


def test_accepts_resolved_fx_option_inputs() -> None:
    resolved = _resolved_fx_inputs()

    accepted = ensure_pure_option_pricing_input_v1(resolved)

    assert accepted == resolved


def test_rejects_dependency_bundle_for_engine_boundary() -> None:
    bundle = OptionValuationDependencyBundleV1(
        option_contract=_generic_contract(),
        market_snapshot_id="mkt.snap.001",
        reference_data_set_id="reference.data.v1",
        valuation_policy_set_id="valuation.policy.v1",
        valuation_context_id="valuation.context.001",
    )

    with pytest.raises(ValueError, match="OptionValuationDependencyBundleV1"):
        ensure_pure_option_pricing_input_v1(bundle)


def test_rejects_repository_and_loader_handles() -> None:
    with pytest.raises(ValueError, match="repository/provider/loader"):
        ensure_pure_option_pricing_input_v1(FakeRepository())

    with pytest.raises(ValueError, match="repository/provider/loader"):
        ensure_pure_option_pricing_input_v1(FakeLoader())
