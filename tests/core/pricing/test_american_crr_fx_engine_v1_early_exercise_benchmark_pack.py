from __future__ import annotations

import datetime
import inspect
from dataclasses import dataclass
from decimal import Decimal

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
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_set_v1 import PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
from core.numeric_policy import EXERCISE_EPSILON_ABS_V1
from core.pricing.american_crr_fx_engine_v1 import AmericanCrrFxEngineV1
from core.pricing.american_crr_fx_engine_v1 import ENGINE_NAME_V1
from core.pricing.american_crr_fx_engine_v1 import ENGINE_VERSION_V1
from core.pricing.american_crr_fx_engine_v1 import MODEL_NAME_V1
from core.pricing.american_crr_fx_engine_v1 import MODEL_VERSION_V1
from core.pricing.american_crr_fx_engine_v1 import RESOLVED_INPUT_CONTRACT_NAME_V1
from core.pricing.american_crr_fx_engine_v1 import RESOLVED_INPUT_CONTRACT_VERSION_V1
from core.pricing.american_crr_fx_engine_v1 import RESOLVED_LATTICE_POLICY_CONTRACT_NAME_V1
from core.pricing.american_crr_fx_engine_v1 import RESOLVED_LATTICE_POLICY_CONTRACT_VERSION_V1
from core.pricing.american_crr_fx_engine_v1 import __name__ as american_engine_module_name
from core.pricing.crr_american_fx_kernel_v1 import apply_american_exercise_decision_v1


FIXED_VALUATION_TIMESTAMP = datetime.datetime(2026, 7, 1, 12, 0, tzinfo=datetime.timezone.utc)


@dataclass(frozen=True)
class EarlyExerciseBenchmarkCaseV1:
    case_id: str
    option_type: str
    spot: Decimal
    strike: Decimal
    domestic_rate: Decimal
    foreign_rate: Decimal
    volatility: Decimal
    time_to_expiry_years: Decimal
    step_count: int
    expected_present_value: Decimal
    expected_intrinsic_value: Decimal
    expected_time_value: Decimal
    expect_root_exercise: bool


EARLY_EXERCISE_BENCHMARK_CASES_V1: tuple[EarlyExerciseBenchmarkCaseV1, ...] = (
    EarlyExerciseBenchmarkCaseV1(
        case_id="exercise_favored_put_itm_high_carry",
        option_type="put",
        spot=Decimal("0.80"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.20"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.05"),
        time_to_expiry_years=Decimal("1.0"),
        step_count=400,
        expected_present_value=Decimal("0.20"),
        expected_intrinsic_value=Decimal("0.20"),
        expected_time_value=Decimal("0.00"),
        expect_root_exercise=True,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="continuation_favored_put_with_material_time_value",
        option_type="put",
        spot=Decimal("0.95"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.00"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.35"),
        time_to_expiry_years=Decimal("1.0"),
        step_count=400,
        expected_present_value=Decimal("0.16196475847505254"),
        expected_intrinsic_value=Decimal("0.05"),
        expected_time_value=Decimal("0.11196475847505254"),
        expect_root_exercise=False,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="boundary_sensitive_put_near_threshold_positive_time_value",
        option_type="put",
        spot=Decimal("0.96"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.00"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.03"),
        time_to_expiry_years=Decimal("0.10"),
        step_count=400,
        expected_present_value=Decimal("0.04000001512114745"),
        expected_intrinsic_value=Decimal("0.04"),
        expected_time_value=Decimal("1.512114745E-8"),
        expect_root_exercise=False,
    ),
)


def _fx_contract(case: EarlyExerciseBenchmarkCaseV1) -> FxOptionRuntimeContractV1:
    return FxOptionRuntimeContractV1(
        contract_id=f"fx-opt-amer-d4-1-{case.case_id}",
        currency_pair_orientation="base_per_quote",
        base_currency="usd",
        quote_currency="ils",
        option_type=case.option_type,
        exercise_style="american",
        strike=case.strike,
        expiry_date=datetime.date(2027, 1, 1),
        expiry_cutoff_time=datetime.time(10, 0, 0),
        expiry_cutoff_timezone="UTC",
        notional=Decimal("1000000"),
        notional_currency_semantics="base_currency",
        premium_currency="usd",
        premium_payment_date=datetime.date(2026, 7, 2),
        settlement_style="deliverable",
        settlement_date=datetime.date(2027, 1, 4),
        settlement_calendar_refs=("IL-TASE", "US-NYFED"),
        fixing_source="WM/Reuters 4pm",
        fixing_date=datetime.date(2027, 1, 1),
        domestic_curve_id="curve.ils.ois.v1",
        foreign_curve_id="curve.usd.ois.v1",
        volatility_surface_quote_convention="delta-neutral-vol",
    )


def _resolved_inputs(case: EarlyExerciseBenchmarkCaseV1) -> ResolvedFxOptionValuationInputsV1:
    return ResolvedFxOptionValuationInputsV1(
        fx_option_contract=_fx_contract(case),
        valuation_timestamp=FIXED_VALUATION_TIMESTAMP,
        spot=ResolvedSpotInputV1(underlying_instrument_ref="USD/ILS", spot=case.spot),
        domestic_curve=ResolvedCurveInputV1(
            curve_id="curve.ils.ois.v1",
            quote_convention="zero_rate",
            interpolation_method="linear_zero_rate",
            extrapolation_policy="flat_forward",
            basis_timestamp=FIXED_VALUATION_TIMESTAMP,
            source_lineage_ref="market_snapshot:d4_1:curve:ils",
            points=(
                ResolvedRatePointV1(tenor_label="1M", zero_rate=case.domestic_rate),
                ResolvedRatePointV1(tenor_label="6M", zero_rate=case.domestic_rate),
            ),
        ),
        foreign_curve=ResolvedCurveInputV1(
            curve_id="curve.usd.ois.v1",
            quote_convention="zero_rate",
            interpolation_method="linear_zero_rate",
            extrapolation_policy="flat_forward",
            basis_timestamp=FIXED_VALUATION_TIMESTAMP,
            source_lineage_ref="market_snapshot:d4_1:curve:usd",
            points=(
                ResolvedRatePointV1(tenor_label="1M", zero_rate=case.foreign_rate),
                ResolvedRatePointV1(tenor_label="6M", zero_rate=case.foreign_rate),
            ),
        ),
        volatility_surface=ResolvedVolatilityInputV1(
            surface_id="surface.fx.usdils.v1",
            quote_convention="implied_vol",
            interpolation_method="surface_quote_map_lookup",
            extrapolation_policy="none",
            basis_timestamp=FIXED_VALUATION_TIMESTAMP,
            source_lineage_ref="market_snapshot:d4_1:vol:usdils",
            points=(
                ResolvedVolatilityPointV1(
                    tenor_label="1M",
                    strike=case.strike,
                    implied_vol=case.volatility,
                ),
            ),
        ),
        day_count_basis="ACT/365F",
        calendar_set=("IL-TASE", "US-NYFED"),
        settlement_conventions=("spot+2",),
        premium_conventions=("premium_currency:USD",),
        numerical_policy_snapshot=NumericalPolicySnapshotV1(
            numeric_policy_id="numeric.policy.v1",
            tolerance=Decimal("0.000001"),
            max_iterations=200,
            rounding_decimals=8,
        ),
        resolved_kernel_scalars=ResolvedFxKernelScalarsV1(
            domestic_rate=case.domestic_rate,
            foreign_rate=case.foreign_rate,
            volatility=case.volatility,
            time_to_expiry_years=case.time_to_expiry_years,
        ),
        resolved_basis_hash=f"sha256:d4-1:{case.case_id}",
    )


def _policy(step_count: int) -> ResolvedAmericanLatticePolicyV1:
    return ResolvedAmericanLatticePolicyV1(
        model_family_id=AMERICAN_MODEL_FAMILY_ID_V1,
        step_count=step_count,
        early_exercise_policy_id=EARLY_EXERCISE_POLICY_ID_V1,
        convergence_policy_id=CONVERGENCE_POLICY_ID_V1,
        edge_case_policy_id=EDGE_CASE_POLICY_ID_V1,
        bump_policy_id=BUMP_POLICY_ID_V1,
        tolerance_policy_id=TOLERANCE_POLICY_ID_V1,
    )


def _measure_values(result) -> dict[ValuationMeasureNameV1, Decimal]:
    return {measure.measure_name: measure.value for measure in result.valuation_measures}


def test_d41_case_pack_structure_is_explicit_and_deterministic() -> None:
    case_ids = tuple(case.case_id for case in EARLY_EXERCISE_BENCHMARK_CASES_V1)
    assert case_ids == (
        "exercise_favored_put_itm_high_carry",
        "continuation_favored_put_with_material_time_value",
        "boundary_sensitive_put_near_threshold_positive_time_value",
    )
    assert len(case_ids) == len(set(case_ids))


def test_d41_result_level_benchmark_assertions_are_traceable() -> None:
    engine = AmericanCrrFxEngineV1()

    for case in EARLY_EXERCISE_BENCHMARK_CASES_V1:
        result = engine.value(_resolved_inputs(case), _policy(step_count=case.step_count))
        values = _measure_values(result)

        assert tuple(item.measure_name for item in result.valuation_measures) == PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
        assert result.engine_name == ENGINE_NAME_V1
        assert result.engine_version == ENGINE_VERSION_V1
        assert result.model_name == MODEL_NAME_V1
        assert result.model_version == MODEL_VERSION_V1
        assert result.resolved_input_contract_name == RESOLVED_INPUT_CONTRACT_NAME_V1
        assert result.resolved_input_contract_version == RESOLVED_INPUT_CONTRACT_VERSION_V1
        assert result.resolved_input_reference == f"sha256:d4-1:{case.case_id}"
        assert result.resolved_lattice_policy_contract_name == RESOLVED_LATTICE_POLICY_CONTRACT_NAME_V1
        assert result.resolved_lattice_policy_contract_version == RESOLVED_LATTICE_POLICY_CONTRACT_VERSION_V1
        assert f"step_count={case.step_count}" in result.resolved_lattice_policy_reference
        assert f"early_exercise_policy_id={EARLY_EXERCISE_POLICY_ID_V1}" in result.resolved_lattice_policy_reference

        assert values[ValuationMeasureNameV1.PRESENT_VALUE] == case.expected_present_value
        assert values[ValuationMeasureNameV1.INTRINSIC_VALUE] == case.expected_intrinsic_value
        assert values[ValuationMeasureNameV1.TIME_VALUE] == case.expected_time_value

        if case.expect_root_exercise:
            assert values[ValuationMeasureNameV1.PRESENT_VALUE] == values[ValuationMeasureNameV1.INTRINSIC_VALUE]
            assert values[ValuationMeasureNameV1.TIME_VALUE] == Decimal("0")
        else:
            assert values[ValuationMeasureNameV1.PRESENT_VALUE] > values[ValuationMeasureNameV1.INTRINSIC_VALUE]
            assert values[ValuationMeasureNameV1.TIME_VALUE] > Decimal("0")


def test_d41_tie_to_continuation_rule_enforcement_at_boundary() -> None:
    continuation = Decimal("10.0")
    eps = EXERCISE_EPSILON_ABS_V1

    cases = (
        ("continuation_strictly_better", Decimal("9.9"), continuation, continuation),
        ("exact_tie", continuation, continuation, continuation),
        ("exact_eps_boundary_still_continuation", continuation + eps, continuation, continuation),
        (
            "strictly_above_eps_switches_to_exercise",
            continuation + eps + Decimal("1e-18"),
            continuation,
            continuation + eps + Decimal("1e-18"),
        ),
    )

    for _label, exercise_value, continuation_value, expected in cases:
        actual = apply_american_exercise_decision_v1(
            exercise_value=exercise_value,
            continuation_value=continuation_value,
        )
        assert actual == expected


def test_d41_strict_decision_invariant_for_fixed_grid() -> None:
    continuation = Decimal("2.5")
    eps = EXERCISE_EPSILON_ABS_V1
    offsets = (
        -Decimal("2e-12"),
        -Decimal("1e-12"),
        Decimal("0"),
        Decimal("5e-13"),
        Decimal("1e-12"),
        Decimal("2e-12"),
    )

    for offset in offsets:
        exercise = continuation + eps + offset
        actual = apply_american_exercise_decision_v1(
            exercise_value=exercise,
            continuation_value=continuation,
        )
        if exercise > continuation + eps:
            assert actual == exercise
        else:
            assert actual == continuation


def test_d41_engine_module_has_no_hidden_io_or_wall_clock_dependencies() -> None:
    source = inspect.getsource(__import__(american_engine_module_name, fromlist=["*"]))

    forbidden_markers = (
        "datetime.now",
        "time.time(",
        "open(",
        "pathlib",
        "requests",
        "urllib",
        "socket",
        "subprocess",
    )
    for marker in forbidden_markers:
        assert marker not in source
