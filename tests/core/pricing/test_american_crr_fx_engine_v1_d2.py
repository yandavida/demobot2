from __future__ import annotations

import datetime
from decimal import Decimal

import pytest

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.resolved_american_lattice_policy_v1 import AMERICAN_MODEL_FAMILY_ID_V1
from core.contracts.resolved_american_lattice_policy_v1 import BUMP_POLICY_ID_V1
from core.contracts.resolved_american_lattice_policy_v1 import CONVERGENCE_POLICY_ID_V1
from core.contracts.resolved_american_lattice_policy_v1 import EARLY_EXERCISE_POLICY_ID_V1
from core.contracts.resolved_american_lattice_policy_v1 import EDGE_CASE_POLICY_ID_V1
from core.contracts.resolved_american_lattice_policy_v1 import ResolvedAmericanLatticePolicyV1
from core.contracts.resolved_american_lattice_policy_v1 import TOLERANCE_POLICY_ID_V1
from core.contracts.resolved_option_valuation_inputs_v1 import NumericalPolicySnapshotV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedCurveInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxKernelScalarsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedRatePointV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedSpotInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityPointV1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_POLICY_ID_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import ThetaRolledFxInputsBoundaryV1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
from core.numeric_policy import SPOT_BUMP_RELATIVE_V1
from core.pricing.american_crr_fx_engine_v1 import AmericanCrrFxEngineV1
from core.pricing.american_crr_fx_engine_v1 import DELTA_MEASURE_POLICY_ID_V1
from core.pricing.american_crr_fx_engine_v1 import GAMMA_MEASURE_POLICY_ID_V1
from core.pricing.american_crr_fx_engine_v1 import RHO_DOMESTIC_MEASURE_POLICY_ID_V1
from core.pricing.american_crr_fx_engine_v1 import RHO_FOREIGN_MEASURE_POLICY_ID_V1
from core.pricing.american_crr_fx_engine_v1 import THETA_MEASURE_POLICY_ID_V1
from core.pricing.american_crr_fx_engine_v1 import VEGA_MEASURE_POLICY_ID_V1
from core.pricing.black_scholes_fx_kernel_v1 import black_scholes_fx_measures_v1
from core.pricing.crr_american_fx_kernel_v1 import CrrAmericanKernelResultV1


def _fx_contract() -> FxOptionRuntimeContractV1:
    return FxOptionRuntimeContractV1(
        contract_id="fx-opt-amer-d2-001",
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


def _resolved_fx_inputs(*, basis_hash: str = "sha256:d2-current", time_to_expiry_years: str = "0.08333333333333333333333333333") -> ResolvedFxOptionValuationInputsV1:
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
                ResolvedVolatilityPointV1(tenor_label="1M", strike="3.65", implied_vol="0.11"),
            ),
        ),
        day_count_basis="ACT/365F",
        calendar_set=("IL-TASE", "US-NYFED"),
        settlement_conventions=("spot+2",),
        premium_conventions=("premium_currency:USD",),
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


def _policy(*, step_count: int = 250) -> ResolvedAmericanLatticePolicyV1:
    return ResolvedAmericanLatticePolicyV1(
        model_family_id=AMERICAN_MODEL_FAMILY_ID_V1,
        step_count=step_count,
        early_exercise_policy_id=EARLY_EXERCISE_POLICY_ID_V1,
        convergence_policy_id=CONVERGENCE_POLICY_ID_V1,
        edge_case_policy_id=EDGE_CASE_POLICY_ID_V1,
        bump_policy_id=BUMP_POLICY_ID_V1,
        tolerance_policy_id=TOLERANCE_POLICY_ID_V1,
    )


def _theta_boundary(current: ResolvedFxOptionValuationInputsV1) -> ThetaRolledFxInputsBoundaryV1:
    rolled = _resolved_fx_inputs(
        basis_hash="sha256:d2-rolled",
        time_to_expiry_years="0.08059360730593607305936073059",
    )
    return ThetaRolledFxInputsBoundaryV1(
        current_resolved_inputs=current,
        theta_rolled_resolved_inputs=rolled,
        theta_roll_policy_id=THETA_ROLLED_INPUT_POLICY_ID_V1,
    )


def _measure_map(result) -> dict[ValuationMeasureNameV1, object]:
    return {measure.measure_name: measure for measure in result.valuation_measures}


def test_emits_full_governed_measure_set_in_canonical_order() -> None:
    inputs = _resolved_fx_inputs()
    result = AmericanCrrFxEngineV1().value_with_theta_rolled_inputs_boundary(inputs, _policy(), _theta_boundary(inputs))

    names = tuple(item.measure_name for item in result.valuation_measures)
    assert names == PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1


def test_provenance_and_policy_traceability_are_explicit() -> None:
    inputs = _resolved_fx_inputs()
    result = AmericanCrrFxEngineV1().value_with_theta_rolled_inputs_boundary(inputs, _policy(), _theta_boundary(inputs))
    measures = _measure_map(result)

    for model_direct_measure in (
        ValuationMeasureNameV1.PRESENT_VALUE,
        ValuationMeasureNameV1.INTRINSIC_VALUE,
        ValuationMeasureNameV1.TIME_VALUE,
    ):
        entry = measures[model_direct_measure]
        assert entry.method_kind == ValuationMeasureMethodKindV2.MODEL_DIRECT
        assert entry.bump_policy_id is None
        assert entry.tolerance_policy_id is None

    numerical_policy_by_measure = {
        ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED: DELTA_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.GAMMA_SPOT: GAMMA_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.VEGA_1VOL_ABS: VEGA_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.THETA_1D_CALENDAR: THETA_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.RHO_DOMESTIC_1PCT: RHO_DOMESTIC_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.RHO_FOREIGN_1PCT: RHO_FOREIGN_MEASURE_POLICY_ID_V1,
    }

    for measure_name, policy_id in numerical_policy_by_measure.items():
        entry = measures[measure_name]
        assert entry.method_kind == ValuationMeasureMethodKindV2.NUMERICAL_BUMP_REPRICE
        assert entry.measure_policy_id == policy_id
        assert entry.bump_policy_id == BUMP_POLICY_ID_V1
        assert entry.tolerance_policy_id == TOLERANCE_POLICY_ID_V1


def test_repeated_calls_are_deterministic() -> None:
    engine = AmericanCrrFxEngineV1()
    inputs = _resolved_fx_inputs()
    policy = _policy()
    boundary = _theta_boundary(inputs)

    first = engine.value_with_theta_rolled_inputs_boundary(inputs, policy, boundary)
    second = engine.value_with_theta_rolled_inputs_boundary(inputs, policy, boundary)

    assert first == second


def test_theta_uses_governed_boundary_only(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _fake_present_value(rolled_inputs, lattice_policy):
        captured["rolled_basis_hash"] = rolled_inputs.resolved_basis_hash
        captured["policy_step_count"] = lattice_policy.step_count
        return Decimal("11.5")

    monkeypatch.setattr("core.pricing.american_crr_fx_engine_v1._present_value_from_inputs_v1", _fake_present_value)

    inputs = _resolved_fx_inputs()
    policy = _policy(step_count=300)
    boundary = _theta_boundary(inputs)

    result = AmericanCrrFxEngineV1().value_with_theta_rolled_inputs_boundary(inputs, policy, boundary)
    measures = _measure_map(result)

    assert captured["rolled_basis_hash"] == boundary.theta_rolled_resolved_inputs.resolved_basis_hash
    assert captured["policy_step_count"] == policy.step_count
    assert measures[ValuationMeasureNameV1.THETA_1D_CALENDAR].method_kind == ValuationMeasureMethodKindV2.NUMERICAL_BUMP_REPRICE


def test_rejects_mismatched_theta_boundary_current_inputs() -> None:
    inputs = _resolved_fx_inputs()
    mismatched_current = _resolved_fx_inputs(basis_hash="sha256:other-current")
    boundary = ThetaRolledFxInputsBoundaryV1(
        current_resolved_inputs=mismatched_current,
        theta_rolled_resolved_inputs=_resolved_fx_inputs(
            basis_hash="sha256:d2-rolled",
            time_to_expiry_years="0.08059360730593607305936073059",
        ),
        theta_roll_policy_id=THETA_ROLLED_INPUT_POLICY_ID_V1,
    )

    with pytest.raises(ValueError, match="must equal resolved_inputs"):
        AmericanCrrFxEngineV1().value_with_theta_rolled_inputs_boundary(inputs, _policy(), boundary)


def test_numerical_sanity_in_standard_case() -> None:
    inputs = _resolved_fx_inputs()
    result = AmericanCrrFxEngineV1().value_with_theta_rolled_inputs_boundary(inputs, _policy(), _theta_boundary(inputs))
    measures = _measure_map(result)

    assert measures[ValuationMeasureNameV1.GAMMA_SPOT].value >= Decimal("0")
    assert measures[ValuationMeasureNameV1.VEGA_1VOL_ABS].value >= Decimal("0")

    bs_measure_map = {
        item.measure_name: item.value
        for item in black_scholes_fx_measures_v1(
            option_type=inputs.fx_option_contract.option_type,
            spot=inputs.spot.spot,
            strike=inputs.fx_option_contract.strike,
            domestic_rate=inputs.resolved_kernel_scalars.domestic_rate,
            foreign_rate=inputs.resolved_kernel_scalars.foreign_rate,
            volatility=inputs.resolved_kernel_scalars.volatility,
            time_to_expiry_years=inputs.resolved_kernel_scalars.time_to_expiry_years,
        )
    }
    assert measures[ValuationMeasureNameV1.PRESENT_VALUE].value >= bs_measure_map[ValuationMeasureNameV1.PRESENT_VALUE]


def test_numerical_outputs_are_not_placeholders(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_kernel(**kwargs: object) -> CrrAmericanKernelResultV1:
        spot = kwargs["spot"]
        domestic_rate = kwargs["domestic_rate"]
        foreign_rate = kwargs["foreign_rate"]
        volatility = kwargs["volatility"]
        time_to_expiry_years = kwargs["time_to_expiry_years"]
        pv = spot + domestic_rate - foreign_rate + (Decimal("2") * volatility) + time_to_expiry_years
        intrinsic = max(spot - kwargs["strike"], Decimal("0"))
        return CrrAmericanKernelResultV1(
            present_value=pv,
            intrinsic_value=intrinsic,
            time_value=pv - intrinsic,
        )

    monkeypatch.setattr("core.pricing.american_crr_fx_engine_v1.crr_american_fx_kernel_v1", _fake_kernel)

    inputs = _resolved_fx_inputs()
    result = AmericanCrrFxEngineV1().value_with_theta_rolled_inputs_boundary(inputs, _policy(), _theta_boundary(inputs))
    measures = _measure_map(result)

    assert measures[ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED].value != Decimal("0")
    assert measures[ValuationMeasureNameV1.VEGA_1VOL_ABS].value != Decimal("0")
    assert measures[ValuationMeasureNameV1.RHO_DOMESTIC_1PCT].value != Decimal("0")
    assert measures[ValuationMeasureNameV1.RHO_FOREIGN_1PCT].value != Decimal("0")


def test_spot_bump_policy_is_relative_to_current_spot(monkeypatch: pytest.MonkeyPatch) -> None:
    observed_spot_values: list[Decimal] = []

    def _recording_kernel(**kwargs: object) -> CrrAmericanKernelResultV1:
        observed_spot_values.append(kwargs["spot"])
        spot = kwargs["spot"]
        intrinsic = max(spot - kwargs["strike"], Decimal("0"))
        return CrrAmericanKernelResultV1(
            present_value=spot,
            intrinsic_value=intrinsic,
            time_value=spot - intrinsic,
        )

    monkeypatch.setattr("core.pricing.american_crr_fx_engine_v1.crr_american_fx_kernel_v1", _recording_kernel)

    inputs = _resolved_fx_inputs()
    AmericanCrrFxEngineV1().value_with_theta_rolled_inputs_boundary(inputs, _policy(), _theta_boundary(inputs))

    spot = inputs.spot.spot
    expected_bump_abs = spot * SPOT_BUMP_RELATIVE_V1

    assert (spot + expected_bump_abs) in observed_spot_values
    assert (spot - expected_bump_abs) in observed_spot_values


def test_identity_and_lineage_are_preserved_in_full_output() -> None:
    inputs = _resolved_fx_inputs()
    policy = _policy(step_count=220)
    boundary = _theta_boundary(inputs)
    result = AmericanCrrFxEngineV1().value_with_theta_rolled_inputs_boundary(inputs, policy, boundary)

    assert result.engine_name == "american_crr_fx_engine"
    assert result.engine_version == "1.0.0"
    assert result.model_name == "crr_recombining_binomial"
    assert result.model_version == "1.0.0"
    assert result.resolved_input_contract_name == "ResolvedFxOptionValuationInputsV1"
    assert result.resolved_input_reference == inputs.resolved_basis_hash
    assert result.resolved_lattice_policy_contract_name == "ResolvedAmericanLatticePolicyV1"
    assert "step_count=220" in result.resolved_lattice_policy_reference
    assert result.theta_roll_boundary_contract_name == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
    assert result.theta_roll_boundary_contract_version == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
    assert result.theta_roll_boundary_reference == (
        "ThetaRolledFxInputsBoundaryV1:"
        f"current_resolved_input_reference={boundary.current_resolved_inputs.resolved_basis_hash};"
        f"theta_rolled_resolved_input_reference={boundary.theta_rolled_resolved_inputs.resolved_basis_hash};"
        f"theta_roll_policy_id={boundary.theta_roll_policy_id}"
    )
