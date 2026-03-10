from __future__ import annotations

import datetime
import inspect
from decimal import Decimal

import pytest

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.option_valuation_result_v1 import OptionValuationResultV1
from core.contracts.resolved_option_valuation_inputs_v1 import NumericalPolicySnapshotV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedCurveInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxKernelScalarsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedRatePointV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedSpotInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityPointV1
from core.contracts.valuation_measure_result_v1 import ValuationMeasureResultV1
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
from core.pricing.black_scholes_european_fx_engine_v1 import BlackScholesEuropeanFxEngineV1
from core.pricing.black_scholes_european_fx_engine_v1 import ENGINE_NAME_V1
from core.pricing.black_scholes_european_fx_engine_v1 import ENGINE_VERSION_V1
from core.pricing.black_scholes_european_fx_engine_v1 import MODEL_NAME_V1
from core.pricing.black_scholes_european_fx_engine_v1 import MODEL_VERSION_V1
from core.pricing.black_scholes_european_fx_engine_v1 import RESOLVED_INPUT_CONTRACT_NAME_V1
from core.pricing.black_scholes_european_fx_engine_v1 import RESOLVED_INPUT_CONTRACT_VERSION_V1
from core.pricing.black_scholes_european_fx_engine_v1 import __name__ as engine_module_name


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
        resolved_basis_hash="sha256:def456",
    )


def test_accepts_resolved_fx_inputs_only() -> None:
    engine = BlackScholesEuropeanFxEngineV1()
    result = engine.value(_resolved_fx_inputs())

    assert isinstance(result, OptionValuationResultV1)


def test_rejects_wrong_input_contract_type() -> None:
    engine = BlackScholesEuropeanFxEngineV1()

    with pytest.raises(ValueError, match="ResolvedFxOptionValuationInputsV1"):
        engine.value(object())  # type: ignore[arg-type]


def test_repeated_calls_are_deterministic() -> None:
    engine = BlackScholesEuropeanFxEngineV1()
    resolved = _resolved_fx_inputs()

    first = engine.value(resolved)
    second = engine.value(resolved)

    assert first == second


def test_result_shape_identity_lineage_and_measure_order_are_governed() -> None:
    engine = BlackScholesEuropeanFxEngineV1()
    result = engine.value(_resolved_fx_inputs())

    assert result.engine_name == ENGINE_NAME_V1
    assert result.engine_version == ENGINE_VERSION_V1
    assert result.model_name == MODEL_NAME_V1
    assert result.model_version == MODEL_VERSION_V1
    assert result.resolved_input_contract_name == RESOLVED_INPUT_CONTRACT_NAME_V1
    assert result.resolved_input_contract_version == RESOLVED_INPUT_CONTRACT_VERSION_V1
    assert result.resolved_input_reference == "sha256:def456"

    names = tuple(item.measure_name for item in result.valuation_measures)
    assert names == PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
    assert len(set(names)) == len(PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1)


def test_mapping_uses_kernel_outputs_without_reinterpretation(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = tuple(
        ValuationMeasureResultV1(measure_name=name, value=Decimal(index + 1))
        for index, name in enumerate(PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1)
    )

    call_count = {"count": 0}

    def _fake_kernel(**_kwargs: object) -> tuple[ValuationMeasureResultV1, ...]:
        call_count["count"] += 1
        return expected

    monkeypatch.setattr(
        "core.pricing.black_scholes_european_fx_engine_v1.black_scholes_fx_measures_v1",
        _fake_kernel,
    )

    engine = BlackScholesEuropeanFxEngineV1()
    result = engine.value(_resolved_fx_inputs())

    assert call_count["count"] == 1
    assert result.valuation_measures == expected


def test_mapping_uses_explicit_resolved_kernel_scalars_not_curve_point_heuristics(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Decimal] = {}

    def _fake_kernel(**kwargs: object) -> tuple[ValuationMeasureResultV1, ...]:
        captured["domestic_rate"] = kwargs["domestic_rate"]  # type: ignore[index]
        captured["foreign_rate"] = kwargs["foreign_rate"]  # type: ignore[index]
        captured["volatility"] = kwargs["volatility"]  # type: ignore[index]
        captured["time_to_expiry_years"] = kwargs["time_to_expiry_years"]  # type: ignore[index]
        return tuple(
            ValuationMeasureResultV1(measure_name=name, value=Decimal("1"))
            for name in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
        )

    monkeypatch.setattr(
        "core.pricing.black_scholes_european_fx_engine_v1.black_scholes_fx_measures_v1",
        _fake_kernel,
    )

    resolved = _resolved_fx_inputs()
    object.__setattr__(
        resolved,
        "resolved_kernel_scalars",
        ResolvedFxKernelScalarsV1(
            domestic_rate="0.031",
            foreign_rate="0.017",
            volatility="0.233",
            time_to_expiry_years="0.25",
        ),
    )
    object.__setattr__(
        resolved,
        "domestic_curve",
        ResolvedCurveInputV1(
            curve_id="curve.ils.ois.v1",
            quote_convention="zero_rate",
            interpolation_method="linear_zero_rate",
            extrapolation_policy="flat_forward",
            basis_timestamp=resolved.valuation_timestamp,
            source_lineage_ref="market_snapshot:mkt.snap.001:curve:curve.ils.ois.v1",
            points=(
                ResolvedRatePointV1(tenor_label="1M", zero_rate="0.99"),
                ResolvedRatePointV1(tenor_label="6M", zero_rate="0.98"),
            ),
        ),
    )
    object.__setattr__(
        resolved,
        "foreign_curve",
        ResolvedCurveInputV1(
            curve_id="curve.usd.ois.v1",
            quote_convention="zero_rate",
            interpolation_method="linear_zero_rate",
            extrapolation_policy="flat_forward",
            basis_timestamp=resolved.valuation_timestamp,
            source_lineage_ref="market_snapshot:mkt.snap.001:curve:curve.usd.ois.v1",
            points=(
                ResolvedRatePointV1(tenor_label="1M", zero_rate="0.88"),
                ResolvedRatePointV1(tenor_label="6M", zero_rate="0.77"),
            ),
        ),
    )
    object.__setattr__(
        resolved,
        "volatility_surface",
        ResolvedVolatilityInputV1(
            surface_id="surface.fx.usdils.v1",
            quote_convention="implied_vol",
            interpolation_method="surface_quote_map_lookup",
            extrapolation_policy="none",
            basis_timestamp=resolved.valuation_timestamp,
            source_lineage_ref="market_snapshot:mkt.snap.001:vol_surface:surface.fx.usdils.v1",
            points=(
                ResolvedVolatilityPointV1(tenor_label="1M", strike="3.65", implied_vol="0.66"),
            ),
        ),
    )

    BlackScholesEuropeanFxEngineV1().value(resolved)

    assert captured["domestic_rate"] == Decimal("0.031")
    assert captured["foreign_rate"] == Decimal("0.017")
    assert captured["volatility"] == Decimal("0.233")
    assert captured["time_to_expiry_years"] == Decimal("0.25")


def test_rejects_non_european_exercise_style() -> None:
    contract = _fx_contract()
    object.__setattr__(contract, "exercise_style", "american")
    resolved = _resolved_fx_inputs()
    object.__setattr__(resolved, "fx_option_contract", contract)

    with pytest.raises(ValueError, match="exercise_style"):
        BlackScholesEuropeanFxEngineV1().value(resolved)


def test_no_hidden_default_or_registry_driven_identity() -> None:
    assert ENGINE_NAME_V1 == "black_scholes_european_fx_engine"
    assert ENGINE_VERSION_V1 == "1.0.0"
    assert MODEL_NAME_V1 == "garman_kohlhagen"
    assert MODEL_VERSION_V1 == "1.0.0"
    assert RESOLVED_INPUT_CONTRACT_NAME_V1 == "ResolvedFxOptionValuationInputsV1"
    assert RESOLVED_INPUT_CONTRACT_VERSION_V1 == "1.0.0"


def test_engine_module_has_no_loader_or_repository_imports() -> None:
    module = __import__(engine_module_name, fromlist=["*"])
    source = inspect.getsource(module)

    assert "core.persistence" not in source
    assert "option_valuation_input_resolver_v1" not in source
    assert "OptionPricingArtifactV1" not in source
    assert "canonical_serialization_v1" not in source
    assert "canonical_hashing_v1" not in source
    assert "tenor_to_year" not in source
    assert "tenor_label" not in source
