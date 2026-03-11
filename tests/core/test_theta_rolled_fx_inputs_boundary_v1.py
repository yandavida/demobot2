from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError
from dataclasses import fields
import inspect

import pytest

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.resolved_option_valuation_inputs_v1 import NumericalPolicySnapshotV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedCurveInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxKernelScalarsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedRatePointV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedSpotInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityPointV1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_POLICY_ID_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import ThetaRolledFxInputsBoundaryV1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import __name__ as boundary_module_name


def _fx_contract() -> FxOptionRuntimeContractV1:
    return FxOptionRuntimeContractV1(
        contract_id="fx-opt-001",
        currency_pair_orientation="base_per_quote",
        base_currency="usd",
        quote_currency="ils",
        option_type="call",
        exercise_style="american",
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


def _resolved_fx_inputs(*, basis_hash: str, time_to_expiry_years: str) -> ResolvedFxOptionValuationInputsV1:
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
        resolved_kernel_scalars=ResolvedFxKernelScalarsV1(
            domestic_rate="0.04",
            foreign_rate="0.05",
            volatility="0.11",
            time_to_expiry_years=time_to_expiry_years,
        ),
        resolved_basis_hash=basis_hash,
    )


def test_boundary_shape_is_explicit_and_stable() -> None:
    field_names = tuple(field.name for field in fields(ThetaRolledFxInputsBoundaryV1))

    assert field_names == (
        "current_resolved_inputs",
        "theta_rolled_resolved_inputs",
        "theta_roll_policy_id",
    )


def test_boundary_is_immutable() -> None:
    boundary = ThetaRolledFxInputsBoundaryV1(
        current_resolved_inputs=_resolved_fx_inputs(
            basis_hash="sha256:current",
            time_to_expiry_years="0.08333333333333333333333333333",
        ),
        theta_rolled_resolved_inputs=_resolved_fx_inputs(
            basis_hash="sha256:rolled",
            time_to_expiry_years="0.08059360730593607305936073059",
        ),
        theta_roll_policy_id=THETA_ROLLED_INPUT_POLICY_ID_V1,
    )

    with pytest.raises(FrozenInstanceError):
        boundary.theta_roll_policy_id = "other"  # type: ignore[misc]


def test_boundary_requires_explicit_current_and_rolled_resolved_inputs() -> None:
    current_inputs = _resolved_fx_inputs(
        basis_hash="sha256:current",
        time_to_expiry_years="0.08333333333333333333333333333",
    )
    rolled_inputs = _resolved_fx_inputs(
        basis_hash="sha256:rolled",
        time_to_expiry_years="0.08059360730593607305936073059",
    )

    boundary = ThetaRolledFxInputsBoundaryV1(
        current_resolved_inputs=current_inputs,
        theta_rolled_resolved_inputs=rolled_inputs,
        theta_roll_policy_id=THETA_ROLLED_INPUT_POLICY_ID_V1,
    )

    assert boundary.current_resolved_inputs.resolved_basis_hash == "sha256:current"
    assert boundary.theta_rolled_resolved_inputs.resolved_basis_hash == "sha256:rolled"
    assert boundary.current_resolved_inputs.fx_option_contract == boundary.theta_rolled_resolved_inputs.fx_option_contract


def test_boundary_rejects_wrong_input_types() -> None:
    current_inputs = _resolved_fx_inputs(
        basis_hash="sha256:current",
        time_to_expiry_years="0.08333333333333333333333333333",
    )

    with pytest.raises(ValueError, match="current_resolved_inputs"):
        ThetaRolledFxInputsBoundaryV1(
            current_resolved_inputs=object(),  # type: ignore[arg-type]
            theta_rolled_resolved_inputs=current_inputs,
            theta_roll_policy_id=THETA_ROLLED_INPUT_POLICY_ID_V1,
        )

    with pytest.raises(ValueError, match="theta_rolled_resolved_inputs"):
        ThetaRolledFxInputsBoundaryV1(
            current_resolved_inputs=current_inputs,
            theta_rolled_resolved_inputs=object(),  # type: ignore[arg-type]
            theta_roll_policy_id=THETA_ROLLED_INPUT_POLICY_ID_V1,
        )


def test_boundary_requires_explicit_distinction_between_current_and_rolled_inputs() -> None:
    current_inputs = _resolved_fx_inputs(
        basis_hash="sha256:current",
        time_to_expiry_years="0.08333333333333333333333333333",
    )

    with pytest.raises(ValueError, match="explicitly distinct"):
        ThetaRolledFxInputsBoundaryV1(
            current_resolved_inputs=current_inputs,
            theta_rolled_resolved_inputs=current_inputs,
            theta_roll_policy_id=THETA_ROLLED_INPUT_POLICY_ID_V1,
        )


def test_boundary_rejects_ungoverned_theta_roll_policy_id() -> None:
    with pytest.raises(ValueError, match="theta_roll_policy_id"):
        ThetaRolledFxInputsBoundaryV1(
            current_resolved_inputs=_resolved_fx_inputs(
                basis_hash="sha256:current",
                time_to_expiry_years="0.08333333333333333333333333333",
            ),
            theta_rolled_resolved_inputs=_resolved_fx_inputs(
                basis_hash="sha256:rolled",
                time_to_expiry_years="0.08059360730593607305936073059",
            ),
            theta_roll_policy_id="theta_roll_uncontrolled_v1",
        )


def test_boundary_rejects_mismatched_fx_option_contract_between_current_and_rolled() -> None:
    current_inputs = _resolved_fx_inputs(
        basis_hash="sha256:current",
        time_to_expiry_years="0.08333333333333333333333333333",
    )
    rolled_inputs = _resolved_fx_inputs(
        basis_hash="sha256:rolled",
        time_to_expiry_years="0.08059360730593607305936073059",
    )

    different_contract = _fx_contract()
    object.__setattr__(different_contract, "contract_id", "fx-opt-002")
    object.__setattr__(rolled_inputs, "fx_option_contract", different_contract)

    with pytest.raises(ValueError, match="same fx_option_contract"):
        ThetaRolledFxInputsBoundaryV1(
            current_resolved_inputs=current_inputs,
            theta_rolled_resolved_inputs=rolled_inputs,
            theta_roll_policy_id=THETA_ROLLED_INPUT_POLICY_ID_V1,
        )


def test_boundary_rejects_rolled_time_to_expiry_greater_than_current() -> None:
    current_inputs = _resolved_fx_inputs(
        basis_hash="sha256:current",
        time_to_expiry_years="0.08333333333333333333333333333",
    )
    rolled_inputs = _resolved_fx_inputs(
        basis_hash="sha256:rolled",
        time_to_expiry_years="0.08607305936073059360730593607",
    )

    with pytest.raises(ValueError, match="must be <="):
        ThetaRolledFxInputsBoundaryV1(
            current_resolved_inputs=current_inputs,
            theta_rolled_resolved_inputs=rolled_inputs,
            theta_roll_policy_id=THETA_ROLLED_INPUT_POLICY_ID_V1,
        )


def test_boundary_contract_has_no_hidden_calendaring_or_pricing_logic() -> None:
    module = __import__(boundary_module_name, fromlist=["*"])
    source = inspect.getsource(module)

    assert "timedelta" not in source
    assert "calendar" not in source.lower() or "theta_roll_policy_id" in source
    assert "crr_american_fx_kernel_v1" not in source
    assert "black_scholes_fx_measures_v1" not in source


def test_boundary_shape_has_no_portfolio_or_scenario_semantics() -> None:
    forbidden = {
        "portfolio",
        "scenario",
        "basket",
        "lifecycle",
        "advisory",
        "aggregation",
        "risk",
    }

    field_names = {field.name for field in fields(ThetaRolledFxInputsBoundaryV1)}
    assert field_names.isdisjoint(forbidden)
