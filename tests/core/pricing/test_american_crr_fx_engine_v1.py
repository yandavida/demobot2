from __future__ import annotations

import datetime
import inspect
from decimal import Decimal

import pytest

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
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
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2
from core.contracts.valuation_measure_set_v1 import PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
from core.pricing.american_crr_fx_engine_v1 import AmericanCrrFxEngineV1
from core.pricing.american_crr_fx_engine_v1 import ENGINE_NAME_V1
from core.pricing.american_crr_fx_engine_v1 import ENGINE_VERSION_V1
from core.pricing.american_crr_fx_engine_v1 import INTRINSIC_VALUE_MEASURE_POLICY_ID_V1
from core.pricing.american_crr_fx_engine_v1 import MODEL_NAME_V1
from core.pricing.american_crr_fx_engine_v1 import MODEL_VERSION_V1
from core.pricing.american_crr_fx_engine_v1 import PRESENT_VALUE_MEASURE_POLICY_ID_V1
from core.pricing.american_crr_fx_engine_v1 import RESOLVED_INPUT_CONTRACT_NAME_V1
from core.pricing.american_crr_fx_engine_v1 import RESOLVED_INPUT_CONTRACT_VERSION_V1
from core.pricing.american_crr_fx_engine_v1 import RESOLVED_LATTICE_POLICY_CONTRACT_NAME_V1
from core.pricing.american_crr_fx_engine_v1 import RESOLVED_LATTICE_POLICY_CONTRACT_VERSION_V1
from core.pricing.american_crr_fx_engine_v1 import TIME_VALUE_MEASURE_POLICY_ID_V1
from core.pricing.american_crr_fx_engine_v1 import __name__ as engine_module_name
from core.pricing.crr_american_fx_kernel_v1 import CrrAmericanKernelResultV1


def _fx_contract() -> FxOptionRuntimeContractV1:
    return FxOptionRuntimeContractV1(
        contract_id="fx-opt-amer-001",
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
            time_to_expiry_years="0.08333333333333333333333333333",
        ),
        resolved_basis_hash="sha256:american-input-ref-001",
    )


def _policy(*, step_count: int = 200) -> ResolvedAmericanLatticePolicyV1:
    return ResolvedAmericanLatticePolicyV1(
        model_family_id=AMERICAN_MODEL_FAMILY_ID_V1,
        step_count=step_count,
        early_exercise_policy_id=EARLY_EXERCISE_POLICY_ID_V1,
        convergence_policy_id=CONVERGENCE_POLICY_ID_V1,
        edge_case_policy_id=EDGE_CASE_POLICY_ID_V1,
        bump_policy_id=BUMP_POLICY_ID_V1,
        tolerance_policy_id=TOLERANCE_POLICY_ID_V1,
    )


def _expected_lattice_policy_reference(policy: ResolvedAmericanLatticePolicyV1) -> str:
    return (
        "ResolvedAmericanLatticePolicyV1:"
        f"model_family_id={policy.model_family_id};"
        f"step_count={policy.step_count};"
        f"early_exercise_policy_id={policy.early_exercise_policy_id};"
        f"convergence_policy_id={policy.convergence_policy_id};"
        f"edge_case_policy_id={policy.edge_case_policy_id};"
        f"bump_policy_id={policy.bump_policy_id};"
        f"tolerance_policy_id={policy.tolerance_policy_id}"
    )


def test_accepts_exact_two_input_boundary() -> None:
    engine = AmericanCrrFxEngineV1()
    result = engine.value(_resolved_fx_inputs(), _policy())

    assert isinstance(result, OptionValuationResultV2)


def test_rejects_wrong_boundary_input_types() -> None:
    engine = AmericanCrrFxEngineV1()

    with pytest.raises(ValueError, match="ResolvedFxOptionValuationInputsV1"):
        engine.value(object(), _policy())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="ResolvedAmericanLatticePolicyV1"):
        engine.value(_resolved_fx_inputs(), object())  # type: ignore[arg-type]


def test_repeated_calls_are_deterministic() -> None:
    engine = AmericanCrrFxEngineV1()
    resolved_inputs = _resolved_fx_inputs()
    resolved_policy = _policy(step_count=250)

    first = engine.value(resolved_inputs, resolved_policy)
    second = engine.value(resolved_inputs, resolved_policy)

    assert first == second


def test_identity_and_lineage_fields_are_explicit_and_preserved() -> None:
    engine = AmericanCrrFxEngineV1()
    resolved_inputs = _resolved_fx_inputs()
    resolved_policy = _policy(step_count=300)

    result = engine.value(resolved_inputs, resolved_policy)

    assert result.engine_name == ENGINE_NAME_V1
    assert result.engine_version == ENGINE_VERSION_V1
    assert result.model_name == MODEL_NAME_V1
    assert result.model_version == MODEL_VERSION_V1
    assert result.resolved_input_contract_name == RESOLVED_INPUT_CONTRACT_NAME_V1
    assert result.resolved_input_contract_version == RESOLVED_INPUT_CONTRACT_VERSION_V1
    assert result.resolved_input_reference == resolved_inputs.resolved_basis_hash
    assert result.resolved_lattice_policy_contract_name == RESOLVED_LATTICE_POLICY_CONTRACT_NAME_V1
    assert result.resolved_lattice_policy_contract_version == RESOLVED_LATTICE_POLICY_CONTRACT_VERSION_V1
    assert result.resolved_lattice_policy_reference == _expected_lattice_policy_reference(resolved_policy)


def test_model_direct_measure_mapping_uses_explicit_policy_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"count": 0}

    def _fake_kernel(**_kwargs: object) -> CrrAmericanKernelResultV1:
        call_count["count"] += 1
        return CrrAmericanKernelResultV1(
            present_value=Decimal("12.34"),
            intrinsic_value=Decimal("10.00"),
            time_value=Decimal("2.34"),
        )

    monkeypatch.setattr("core.pricing.american_crr_fx_engine_v1.crr_american_fx_kernel_v1", _fake_kernel)

    result = AmericanCrrFxEngineV1().value(_resolved_fx_inputs(), _policy())
    measures = result.valuation_measures

    assert call_count["count"] == 1
    assert tuple(item.measure_name for item in measures) == PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
    assert measures[0].value == Decimal("12.34")
    assert measures[1].value == Decimal("10.00")
    assert measures[2].value == Decimal("2.34")

    assert measures[0].method_kind == ValuationMeasureMethodKindV2.MODEL_DIRECT
    assert measures[0].measure_policy_id == PRESENT_VALUE_MEASURE_POLICY_ID_V1

    assert measures[1].method_kind == ValuationMeasureMethodKindV2.MODEL_DIRECT
    assert measures[1].measure_policy_id == INTRINSIC_VALUE_MEASURE_POLICY_ID_V1

    assert measures[2].method_kind == ValuationMeasureMethodKindV2.MODEL_DIRECT
    assert measures[2].measure_policy_id == TIME_VALUE_MEASURE_POLICY_ID_V1


def test_emits_only_model_direct_slice_and_no_fake_greeks() -> None:
    result = AmericanCrrFxEngineV1().value(_resolved_fx_inputs(), _policy())
    measure_names = tuple(item.measure_name for item in result.valuation_measures)

    assert measure_names == PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
    assert len(measure_names) == 3

    forbidden = {
        ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED,
        ValuationMeasureNameV1.GAMMA_SPOT,
        ValuationMeasureNameV1.VEGA_1VOL_ABS,
        ValuationMeasureNameV1.THETA_1D_CALENDAR,
        ValuationMeasureNameV1.RHO_DOMESTIC_1PCT,
        ValuationMeasureNameV1.RHO_FOREIGN_1PCT,
    }
    assert forbidden.isdisjoint(set(measure_names))


def test_engine_calls_kernel_once_with_resolved_scalars(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _fake_kernel(**kwargs: object) -> CrrAmericanKernelResultV1:
        captured.update(kwargs)
        return CrrAmericanKernelResultV1(
            present_value=Decimal("1"),
            intrinsic_value=Decimal("1"),
            time_value=Decimal("0"),
        )

    monkeypatch.setattr("core.pricing.american_crr_fx_engine_v1.crr_american_fx_kernel_v1", _fake_kernel)

    inputs = _resolved_fx_inputs()
    policy = _policy(step_count=111)
    AmericanCrrFxEngineV1().value(inputs, policy)

    assert captured["option_type"] == inputs.fx_option_contract.option_type
    assert captured["spot"] == inputs.spot.spot
    assert captured["strike"] == inputs.fx_option_contract.strike
    assert captured["domestic_rate"] == inputs.resolved_kernel_scalars.domestic_rate
    assert captured["foreign_rate"] == inputs.resolved_kernel_scalars.foreign_rate
    assert captured["volatility"] == inputs.resolved_kernel_scalars.volatility
    assert captured["time_to_expiry_years"] == inputs.resolved_kernel_scalars.time_to_expiry_years
    assert captured["step_count"] == policy.step_count


def test_rejects_non_american_exercise_style() -> None:
    contract = _fx_contract()
    object.__setattr__(contract, "exercise_style", "european")

    resolved = _resolved_fx_inputs()
    object.__setattr__(resolved, "fx_option_contract", contract)

    with pytest.raises(ValueError, match="exercise_style"):
        AmericanCrrFxEngineV1().value(resolved, _policy())


def test_no_engine_creep_imports() -> None:
    module = __import__(engine_module_name, fromlist=["*"])
    source = inspect.getsource(module)

    assert "core.persistence" not in source
    assert "option_valuation_input_resolver_v1" not in source
    assert "OptionPricingArtifactV2" not in source
    assert "canonical_serialization" not in source
    assert "canonical_hashing" not in source
    assert "tenor_to_year" not in source
    assert "tenor_label" not in source
