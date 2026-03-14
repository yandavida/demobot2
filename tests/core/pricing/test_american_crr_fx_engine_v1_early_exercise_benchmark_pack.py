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
from core.numeric_policy import TIME_EPSILON_YEARS_V1
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
from core.pricing.crr_american_fx_kernel_v1 import CrrAmericanKernelResultV1
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


@dataclass(frozen=True)
class ConvergenceRegressionCaseV1:
    case_id: str
    option_type: str
    spot: Decimal
    strike: Decimal
    domestic_rate: Decimal
    foreign_rate: Decimal
    volatility: Decimal
    time_to_expiry_years: Decimal
    base_step_count: int
    expected_present_value_n: Decimal
    expected_present_value_2n: Decimal
    expected_present_value_4n: Decimal


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


DEEP_ITM_OTM_BENCHMARK_CASES_V1: tuple[EarlyExerciseBenchmarkCaseV1, ...] = (
    EarlyExerciseBenchmarkCaseV1(
        case_id="deep_itm_call_low_vol_short",
        option_type="call",
        spot=Decimal("1.80"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.01"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.05"),
        time_to_expiry_years=Decimal("0.25"),
        step_count=500,
        expected_present_value=Decimal("0.8024968776025472"),
        expected_intrinsic_value=Decimal("0.80"),
        expected_time_value=Decimal("0.0024968776025472"),
        expect_root_exercise=False,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="deep_otm_call_low_vol_short",
        option_type="call",
        spot=Decimal("0.60"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.01"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.05"),
        time_to_expiry_years=Decimal("0.25"),
        step_count=500,
        expected_present_value=Decimal("1.5543627998435793E-116"),
        expected_intrinsic_value=Decimal("0"),
        expected_time_value=Decimal("1.5543627998435793E-116"),
        expect_root_exercise=False,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="deep_itm_put_high_carry",
        option_type="put",
        spot=Decimal("0.40"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.12"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.08"),
        time_to_expiry_years=Decimal("0.75"),
        step_count=500,
        expected_present_value=Decimal("0.60"),
        expected_intrinsic_value=Decimal("0.60"),
        expected_time_value=Decimal("0.00"),
        expect_root_exercise=True,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="deep_otm_put_low_vol_short",
        option_type="put",
        spot=Decimal("1.60"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.01"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.05"),
        time_to_expiry_years=Decimal("0.25"),
        step_count=500,
        expected_present_value=Decimal("2.484905515637785E-96"),
        expected_intrinsic_value=Decimal("0"),
        expected_time_value=Decimal("2.484905515637785E-96"),
        expect_root_exercise=False,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="deep_itm_call_negative_carry",
        option_type="call",
        spot=Decimal("1.80"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.01"),
        foreign_rate=Decimal("0.10"),
        volatility=Decimal("0.08"),
        time_to_expiry_years=Decimal("0.75"),
        step_count=500,
        expected_present_value=Decimal("0.80"),
        expected_intrinsic_value=Decimal("0.80"),
        expected_time_value=Decimal("0.00"),
        expect_root_exercise=True,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="deep_otm_put_carry_sensitive",
        option_type="put",
        spot=Decimal("1.60"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.10"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.20"),
        time_to_expiry_years=Decimal("0.75"),
        step_count=500,
        expected_present_value=Decimal("0.00004991666317075974"),
        expected_intrinsic_value=Decimal("0"),
        expected_time_value=Decimal("0.00004991666317075974"),
        expect_root_exercise=False,
    ),
)


SHORT_DATED_NEAR_EXPIRY_BENCHMARK_CASES_V1: tuple[EarlyExerciseBenchmarkCaseV1, ...] = (
    EarlyExerciseBenchmarkCaseV1(
        case_id="short_tree_call_tiny_positive_time",
        option_type="call",
        spot=Decimal("1.02"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.01"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.20"),
        time_to_expiry_years=Decimal("1e-6"),
        step_count=400,
        expected_present_value=Decimal("0.02000001000000102"),
        expected_intrinsic_value=Decimal("0.02"),
        expected_time_value=Decimal("1.000000102E-8"),
        expect_root_exercise=False,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="short_tree_call_very_short_positive_time",
        option_type="call",
        spot=Decimal("1.02"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.01"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.20"),
        time_to_expiry_years=Decimal("1e-8"),
        step_count=400,
        expected_present_value=Decimal("0.020000000100008665"),
        expected_intrinsic_value=Decimal("0.02"),
        expected_time_value=Decimal("1.00008665E-10"),
        expect_root_exercise=False,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="short_tree_put_tiny_positive_time_exercise_favored",
        option_type="put",
        spot=Decimal("0.98"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.01"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.20"),
        time_to_expiry_years=Decimal("1e-6"),
        step_count=400,
        expected_present_value=Decimal("0.02"),
        expected_intrinsic_value=Decimal("0.02"),
        expected_time_value=Decimal("0.00"),
        expect_root_exercise=True,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="near_zero_boundary_equals_eps_call",
        option_type="call",
        spot=Decimal("1.02"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.01"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.20"),
        time_to_expiry_years=Decimal("1e-12"),
        step_count=400,
        expected_present_value=Decimal("0.02"),
        expected_intrinsic_value=Decimal("0.02"),
        expected_time_value=Decimal("0"),
        expect_root_exercise=True,
    ),
    EarlyExerciseBenchmarkCaseV1(
        case_id="near_zero_below_eps_put",
        option_type="put",
        spot=Decimal("0.98"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.01"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.20"),
        time_to_expiry_years=Decimal("5e-13"),
        step_count=400,
        expected_present_value=Decimal("0.02"),
        expected_intrinsic_value=Decimal("0.02"),
        expected_time_value=Decimal("0"),
        expect_root_exercise=True,
    ),
)


CONVERGENCE_STEP_LADDER_MULTIPLIERS_V1: tuple[int, ...] = (1, 2, 4)


CONVERGENCE_REGRESSION_CASES_V1: tuple[ConvergenceRegressionCaseV1, ...] = (
    ConvergenceRegressionCaseV1(
        case_id="convergence_continuation_favored_put",
        option_type="put",
        spot=Decimal("0.95"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.00"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.35"),
        time_to_expiry_years=Decimal("1.0"),
        base_step_count=125,
        expected_present_value_n=Decimal("0.1620741150593523"),
        expected_present_value_2n=Decimal("0.16189020444280056"),
        expected_present_value_4n=Decimal("0.16193927565943644"),
    ),
    ConvergenceRegressionCaseV1(
        case_id="convergence_near_zero_boundary_call",
        option_type="call",
        spot=Decimal("1.02"),
        strike=Decimal("1.00"),
        domestic_rate=Decimal("0.01"),
        foreign_rate=Decimal("0.00"),
        volatility=Decimal("0.20"),
        time_to_expiry_years=TIME_EPSILON_YEARS_V1,
        base_step_count=125,
        expected_present_value_n=Decimal("0.02"),
        expected_present_value_2n=Decimal("0.02"),
        expected_present_value_4n=Decimal("0.02"),
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


def test_d42_case_pack_structure_is_explicit_and_deterministic() -> None:
    case_ids = tuple(case.case_id for case in DEEP_ITM_OTM_BENCHMARK_CASES_V1)
    assert case_ids == (
        "deep_itm_call_low_vol_short",
        "deep_otm_call_low_vol_short",
        "deep_itm_put_high_carry",
        "deep_otm_put_low_vol_short",
        "deep_itm_call_negative_carry",
        "deep_otm_put_carry_sensitive",
    )
    assert len(case_ids) == len(set(case_ids))


def test_d42_extreme_regime_result_benchmarks_are_regression_locked() -> None:
    engine = AmericanCrrFxEngineV1()

    for case in DEEP_ITM_OTM_BENCHMARK_CASES_V1:
        first = engine.value(_resolved_inputs(case), _policy(step_count=case.step_count))
        second = engine.value(_resolved_inputs(case), _policy(step_count=case.step_count))
        assert first == second

        values = _measure_values(first)
        pv = values[ValuationMeasureNameV1.PRESENT_VALUE]
        intrinsic = values[ValuationMeasureNameV1.INTRINSIC_VALUE]
        time_value = values[ValuationMeasureNameV1.TIME_VALUE]

        assert tuple(item.measure_name for item in first.valuation_measures) == PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
        assert first.resolved_input_reference == f"sha256:d4-1:{case.case_id}"
        assert f"step_count={case.step_count}" in first.resolved_lattice_policy_reference

        assert pv == case.expected_present_value
        assert intrinsic == case.expected_intrinsic_value
        assert time_value == case.expected_time_value

        assert pv >= intrinsic
        assert pv >= Decimal("0")
        assert intrinsic >= Decimal("0")
        assert time_value == pv - intrinsic

        if case.case_id.startswith("deep_itm"):
            assert intrinsic > Decimal("0")
            assert pv >= intrinsic
            if case.expect_root_exercise:
                assert time_value == Decimal("0")
        if case.case_id.startswith("deep_otm"):
            assert intrinsic == Decimal("0")
            assert pv < Decimal("0.001")


def test_d42_carry_sensitive_extreme_regimes_are_explicitly_visible() -> None:
    case_by_id = {case.case_id: case for case in DEEP_ITM_OTM_BENCHMARK_CASES_V1}
    engine = AmericanCrrFxEngineV1()

    low_carry_call = engine.value(
        _resolved_inputs(case_by_id["deep_itm_call_low_vol_short"]),
        _policy(step_count=case_by_id["deep_itm_call_low_vol_short"].step_count),
    )
    negative_carry_call = engine.value(
        _resolved_inputs(case_by_id["deep_itm_call_negative_carry"]),
        _policy(step_count=case_by_id["deep_itm_call_negative_carry"].step_count),
    )
    low_vol_otm_put = engine.value(
        _resolved_inputs(case_by_id["deep_otm_put_low_vol_short"]),
        _policy(step_count=case_by_id["deep_otm_put_low_vol_short"].step_count),
    )
    carry_sensitive_otm_put = engine.value(
        _resolved_inputs(case_by_id["deep_otm_put_carry_sensitive"]),
        _policy(step_count=case_by_id["deep_otm_put_carry_sensitive"].step_count),
    )

    low_carry_call_pv = _measure_values(low_carry_call)[ValuationMeasureNameV1.PRESENT_VALUE]
    negative_carry_call_pv = _measure_values(negative_carry_call)[ValuationMeasureNameV1.PRESENT_VALUE]
    low_vol_otm_put_pv = _measure_values(low_vol_otm_put)[ValuationMeasureNameV1.PRESENT_VALUE]
    carry_sensitive_otm_put_pv = _measure_values(carry_sensitive_otm_put)[ValuationMeasureNameV1.PRESENT_VALUE]

    assert low_carry_call_pv > negative_carry_call_pv
    assert carry_sensitive_otm_put_pv > low_vol_otm_put_pv


def test_d43_case_pack_structure_is_explicit_and_deterministic() -> None:
    case_ids = tuple(case.case_id for case in SHORT_DATED_NEAR_EXPIRY_BENCHMARK_CASES_V1)
    assert case_ids == (
        "short_tree_call_tiny_positive_time",
        "short_tree_call_very_short_positive_time",
        "short_tree_put_tiny_positive_time_exercise_favored",
        "near_zero_boundary_equals_eps_call",
        "near_zero_below_eps_put",
    )
    assert len(case_ids) == len(set(case_ids))


def test_d43_short_dated_and_near_expiry_result_benchmarks_are_regression_locked() -> None:
    engine = AmericanCrrFxEngineV1()

    for case in SHORT_DATED_NEAR_EXPIRY_BENCHMARK_CASES_V1:
        first = engine.value(_resolved_inputs(case), _policy(step_count=case.step_count))
        second = engine.value(_resolved_inputs(case), _policy(step_count=case.step_count))
        assert first == second

        values = _measure_values(first)
        pv = values[ValuationMeasureNameV1.PRESENT_VALUE]
        intrinsic = values[ValuationMeasureNameV1.INTRINSIC_VALUE]
        time_value = values[ValuationMeasureNameV1.TIME_VALUE]

        assert tuple(item.measure_name for item in first.valuation_measures) == PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
        assert first.resolved_input_reference == f"sha256:d4-1:{case.case_id}"
        assert f"step_count={case.step_count}" in first.resolved_lattice_policy_reference

        assert pv == case.expected_present_value
        assert intrinsic == case.expected_intrinsic_value
        assert time_value == case.expected_time_value

        assert pv >= intrinsic
        assert pv >= Decimal("0")
        assert time_value == pv - intrinsic

        if case.case_id.startswith("short_tree_call"):
            assert case.time_to_expiry_years > TIME_EPSILON_YEARS_V1
            assert time_value > Decimal("0")

        if case.case_id.startswith("near_zero"):
            assert case.time_to_expiry_years <= TIME_EPSILON_YEARS_V1
            assert pv == intrinsic
            assert time_value == Decimal("0")


def test_d43_tree_path_and_near_zero_boundary_distinction_is_explicit() -> None:
    case_by_id = {case.case_id: case for case in SHORT_DATED_NEAR_EXPIRY_BENCHMARK_CASES_V1}
    engine = AmericanCrrFxEngineV1()

    short_tree_case = case_by_id["short_tree_call_tiny_positive_time"]
    near_zero_case = case_by_id["near_zero_boundary_equals_eps_call"]
    below_eps_case = case_by_id["near_zero_below_eps_put"]

    short_tree_values = _measure_values(
        engine.value(_resolved_inputs(short_tree_case), _policy(step_count=short_tree_case.step_count))
    )
    near_zero_values = _measure_values(
        engine.value(_resolved_inputs(near_zero_case), _policy(step_count=near_zero_case.step_count))
    )
    below_eps_values = _measure_values(
        engine.value(_resolved_inputs(below_eps_case), _policy(step_count=below_eps_case.step_count))
    )

    assert short_tree_case.time_to_expiry_years > TIME_EPSILON_YEARS_V1
    assert near_zero_case.time_to_expiry_years == TIME_EPSILON_YEARS_V1
    assert below_eps_case.time_to_expiry_years < TIME_EPSILON_YEARS_V1

    assert short_tree_values[ValuationMeasureNameV1.TIME_VALUE] > Decimal("0")
    assert near_zero_values[ValuationMeasureNameV1.TIME_VALUE] == Decimal("0")
    assert below_eps_values[ValuationMeasureNameV1.TIME_VALUE] == Decimal("0")

    assert short_tree_values[ValuationMeasureNameV1.PRESENT_VALUE] > near_zero_values[ValuationMeasureNameV1.PRESENT_VALUE]


def test_d44_convergence_pack_structure_is_explicit_and_deterministic() -> None:
    case_ids = tuple(case.case_id for case in CONVERGENCE_REGRESSION_CASES_V1)
    assert case_ids == (
        "convergence_continuation_favored_put",
        "convergence_near_zero_boundary_call",
    )
    assert CONVERGENCE_STEP_LADDER_MULTIPLIERS_V1 == (1, 2, 4)
    assert len(case_ids) == len(set(case_ids))


def test_d44_fixed_step_ladder_outputs_are_regression_locked() -> None:
    engine = AmericanCrrFxEngineV1()

    for case in CONVERGENCE_REGRESSION_CASES_V1:
        ladder_steps = tuple(case.base_step_count * multiplier for multiplier in CONVERGENCE_STEP_LADDER_MULTIPLIERS_V1)
        expected_pv_by_step = {
            ladder_steps[0]: case.expected_present_value_n,
            ladder_steps[1]: case.expected_present_value_2n,
            ladder_steps[2]: case.expected_present_value_4n,
        }

        observed_pv_by_step: dict[int, Decimal] = {}

        for step_count in ladder_steps:
            fixture_case = EarlyExerciseBenchmarkCaseV1(
                case_id=case.case_id,
                option_type=case.option_type,
                spot=case.spot,
                strike=case.strike,
                domestic_rate=case.domestic_rate,
                foreign_rate=case.foreign_rate,
                volatility=case.volatility,
                time_to_expiry_years=case.time_to_expiry_years,
                step_count=step_count,
                expected_present_value=expected_pv_by_step[step_count],
                expected_intrinsic_value=Decimal("0"),
                expected_time_value=Decimal("0"),
                expect_root_exercise=False,
            )

            first = engine.value(_resolved_inputs(fixture_case), _policy(step_count=step_count))
            second = engine.value(_resolved_inputs(fixture_case), _policy(step_count=step_count))
            assert first == second

            first_values = _measure_values(first)
            pv = first_values[ValuationMeasureNameV1.PRESENT_VALUE]
            intrinsic = first_values[ValuationMeasureNameV1.INTRINSIC_VALUE]
            time_value = first_values[ValuationMeasureNameV1.TIME_VALUE]

            assert tuple(item.measure_name for item in first.valuation_measures) == PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
            assert first.resolved_input_reference == f"sha256:d4-1:{case.case_id}"
            assert f"step_count={step_count}" in first.resolved_lattice_policy_reference
            assert pv == expected_pv_by_step[step_count]
            assert pv >= intrinsic
            assert pv >= Decimal("0")
            assert time_value == pv - intrinsic

            observed_pv_by_step[step_count] = pv

        delta_n_to_2n = abs(observed_pv_by_step[ladder_steps[1]] - observed_pv_by_step[ladder_steps[0]])
        delta_2n_to_4n = abs(observed_pv_by_step[ladder_steps[2]] - observed_pv_by_step[ladder_steps[1]])

        assert delta_2n_to_4n <= delta_n_to_2n

        if case.case_id == "convergence_near_zero_boundary_call":
            assert case.time_to_expiry_years <= TIME_EPSILON_YEARS_V1
            assert delta_n_to_2n == Decimal("0")
            assert delta_2n_to_4n == Decimal("0")


def test_d44_convergence_is_validation_only_not_runtime_step_escalation(monkeypatch) -> None:
    observed_step_counts: list[int] = []

    def _recording_kernel(**kwargs: object):
        step_count_obj = kwargs["step_count"]
        assert isinstance(step_count_obj, int)
        step_count = step_count_obj
        observed_step_counts.append(step_count)
        return_value = Decimal("1") + (Decimal(step_count) / Decimal("1000000"))
        intrinsic = Decimal("1")
        return CrrAmericanKernelResultV1(
            present_value=return_value,
            intrinsic_value=intrinsic,
            time_value=return_value - intrinsic,
        )

    monkeypatch.setattr("core.pricing.american_crr_fx_engine_v1.crr_american_fx_kernel_v1", _recording_kernel)

    engine = AmericanCrrFxEngineV1()
    case = CONVERGENCE_REGRESSION_CASES_V1[0]
    ladder_steps = tuple(case.base_step_count * multiplier for multiplier in CONVERGENCE_STEP_LADDER_MULTIPLIERS_V1)

    fixture_case = EarlyExerciseBenchmarkCaseV1(
        case_id=case.case_id,
        option_type=case.option_type,
        spot=case.spot,
        strike=case.strike,
        domestic_rate=case.domestic_rate,
        foreign_rate=case.foreign_rate,
        volatility=case.volatility,
        time_to_expiry_years=case.time_to_expiry_years,
        step_count=case.base_step_count,
        expected_present_value=Decimal("0"),
        expected_intrinsic_value=Decimal("0"),
        expected_time_value=Decimal("0"),
        expect_root_exercise=False,
    )

    for step_count in ladder_steps:
        engine.value(_resolved_inputs(fixture_case), _policy(step_count=step_count))

    assert observed_step_counts == list(ladder_steps)
