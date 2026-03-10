from __future__ import annotations

import datetime
from dataclasses import fields
from decimal import Decimal

import pytest

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.option_valuation_dependency_bundle_v1 import OptionValuationDependencyBundleV1
from core.contracts.option_runtime_contract_v1 import OptionRuntimeContractV1
from core.contracts.reference_data_set import ReferenceDataSet
from core.contracts.resolved_option_valuation_inputs_v1 import NumericalPolicySnapshotV1
from core.contracts.valuation_context import ValuationContext
from core.contracts.valuation_policy_set import ValuationPolicySet
from core.market_data.market_snapshot_payload_v0 import Curve
from core.market_data.market_snapshot_payload_v0 import FxRates
from core.market_data.market_snapshot_payload_v0 import InterestRateCurves
from core.market_data.market_snapshot_payload_v0 import MarketConventions
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.market_snapshot_payload_v0 import SpotPrices
from core.market_data.market_snapshot_payload_v0 import VolSurface
from core.market_data.market_snapshot_payload_v0 import VolSurfaces
from core.services.option_valuation_input_resolver_v1 import OptionValuationInputResolutionError
from core.services.option_valuation_input_resolver_v1 import FX_KERNEL_SCALAR_SELECTION_POLICY_V1
from core.services.option_valuation_input_resolver_v1 import resolve_fx_option_inputs_v1
from core.services.option_valuation_input_resolver_v1 import resolve_option_inputs_v1


class _MarketSnapshotRepo:
    def __init__(self, snapshot: MarketSnapshotPayloadV0 | None) -> None:
        self._snapshot = snapshot

    def get_by_id(self, market_snapshot_id: str) -> MarketSnapshotPayloadV0 | None:
        return self._snapshot if market_snapshot_id == "mkt.snap.001" else None


class _ReferenceDataRepo:
    def __init__(self, reference_data_set: ReferenceDataSet | None) -> None:
        self._reference_data_set = reference_data_set

    def get_by_id(self, reference_data_set_id: str) -> ReferenceDataSet | None:
        return self._reference_data_set if reference_data_set_id == "reference.data.v1" else None


class _ValuationPolicyRepo:
    def __init__(self, valuation_policy_set: ValuationPolicySet | None) -> None:
        self._valuation_policy_set = valuation_policy_set

    def get_by_id(self, valuation_policy_set_id: str) -> ValuationPolicySet | None:
        return self._valuation_policy_set if valuation_policy_set_id == "valuation.policy.v1" else None


class _ValuationContextRepo:
    def __init__(self, valuation_context: ValuationContext | None) -> None:
        self._valuation_context = valuation_context

    def get_by_id(self, valuation_context_id: str) -> ValuationContext | None:
        return self._valuation_context if valuation_context_id == "valuation.context.001" else None


class _NumericalPolicyRepo:
    def __init__(self, snapshot: NumericalPolicySnapshotV1 | None) -> None:
        self._snapshot = snapshot

    def get_by_numeric_policy_id(self, numeric_policy_id: str) -> NumericalPolicySnapshotV1 | None:
        return self._snapshot if numeric_policy_id == "numeric.policy.v1" else None


class _MalformedNumericalPolicyRepo:
    def get_by_numeric_policy_id(self, numeric_policy_id: str) -> NumericalPolicySnapshotV1 | None:
        if numeric_policy_id != "numeric.policy.v1":
            return None

        malformed = object.__new__(NumericalPolicySnapshotV1)
        object.__setattr__(malformed, "numeric_policy_id", "numeric.policy.v1")
        object.__setattr__(malformed, "tolerance", "0")
        object.__setattr__(malformed, "max_iterations", 0)
        object.__setattr__(malformed, "rounding_decimals", -1)
        return malformed


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


def _bundle(contract: OptionRuntimeContractV1 | FxOptionRuntimeContractV1) -> OptionValuationDependencyBundleV1:
    return OptionValuationDependencyBundleV1(
        option_contract=contract,
        market_snapshot_id="mkt.snap.001",
        reference_data_set_id="reference.data.v1",
        valuation_policy_set_id="valuation.policy.v1",
        valuation_context_id="valuation.context.001",
    )


def _market_snapshot(include_vol: bool = True) -> MarketSnapshotPayloadV0:
    vols = (
        VolSurfaces(
            surfaces={
                "delta-neutral-vol": VolSurface(
                    type="quote_map",
                    data={
                        "quotes": {
                            "USD/ILS|1M|3.65|call": 0.12,
                            "USD/ILS|3M|3.65|call": 0.13,
                        }
                    },
                )
            }
        )
        if include_vol
        else None
    )

    return MarketSnapshotPayloadV0(
        fx_rates=FxRates(base_ccy="USD", quotes={"ILS": 3.70}),
        spots=SpotPrices(
            prices={"USD/ILS": 3.70},
            currency={"USD/ILS": "USD"},
        ),
        curves=InterestRateCurves(
            curves={
                "curve.ils.ois.v1": Curve(day_count="ACT/365F", compounding="continuous", zero_rates={"1M": 0.04, "6M": 0.041}),
                "curve.usd.ois.v1": Curve(day_count="ACT/365F", compounding="continuous", zero_rates={"1M": 0.05, "6M": 0.051}),
            }
        ),
        vols=vols,
        conventions=MarketConventions(calendar="IL-TASE", day_count_default="ACT/365F", spot_lag=2),
    )


def _reference_data_set() -> ReferenceDataSet:
    return ReferenceDataSet(
        calendar_version="2026.01",
        holiday_calendar_refs=("IL-TASE", "US-NYFED"),
        day_count_convention_refs=("ACT/365F",),
        business_day_adjustment_refs=("following",),
        settlement_convention_refs=("spot+2",),
        fixing_source_refs=("WM/Reuters 4pm",),
        exercise_convention_refs=("european-expiry",),
        taxonomy_mapping_refs=("fx-option-vanilla",),
        reference_data_version_id="reference.data.v1",
    )


def _valuation_policy_set() -> ValuationPolicySet:
    return ValuationPolicySet(
        valuation_policy_id="valuation.policy.v1",
        model_family="black_scholes",
        pricing_engine_policy="governed",
        numeric_policy_id="numeric.policy.v1",
        tolerance_policy_id="tol.v1",
        calibration_recipe_id="cal.v1",
        approval_status="approved",
        policy_version="1.0",
        policy_owner="risk",
        created_timestamp=datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
    )


def _valuation_context() -> ValuationContext:
    return ValuationContext(
        valuation_context_id="valuation.context.001",
        valuation_timestamp=datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
        market_snapshot_id="mkt.snap.001",
        reference_data_set_id="reference.data.v1",
        valuation_policy_set_id="valuation.policy.v1",
        pricing_currency="USD",
        reporting_currency="USD",
        run_purpose="valuation",
    )


def _numeric_policy_snapshot() -> NumericalPolicySnapshotV1:
    return NumericalPolicySnapshotV1(
        numeric_policy_id="numeric.policy.v1",
        tolerance="0.000001",
        max_iterations=200,
        rounding_decimals=8,
    )


def _resolver_dependencies(*, include_market_snapshot: bool = True, include_reference_data: bool = True, include_vol: bool = True) -> tuple[_MarketSnapshotRepo, _ReferenceDataRepo, _ValuationPolicyRepo, _ValuationContextRepo, _NumericalPolicyRepo]:
    return (
        _MarketSnapshotRepo(_market_snapshot(include_vol=include_vol) if include_market_snapshot else None),
        _ReferenceDataRepo(_reference_data_set() if include_reference_data else None),
        _ValuationPolicyRepo(_valuation_policy_set()),
        _ValuationContextRepo(_valuation_context()),
        _NumericalPolicyRepo(_numeric_policy_snapshot()),
    )


def test_dependency_bundle_resolves_successfully() -> None:
    market_repo, ref_repo, policy_repo, context_repo, numeric_repo = _resolver_dependencies()

    resolved = resolve_option_inputs_v1(
        _bundle(_generic_contract()),
        market_snapshot_repository=market_repo,
        reference_data_set_repository=ref_repo,
        valuation_policy_set_repository=policy_repo,
        valuation_context_repository=context_repo,
        numerical_policy_snapshot_repository=numeric_repo,
    )

    assert resolved.option_contract.contract_id == "opt-rt-001"
    assert resolved.resolved_underlying_input.underlying_instrument_ref == "USD/ILS"


def test_missing_market_snapshot_fails() -> None:
    market_repo, ref_repo, policy_repo, context_repo, numeric_repo = _resolver_dependencies(include_market_snapshot=False)

    with pytest.raises(OptionValuationInputResolutionError, match="market_snapshot"):
        resolve_option_inputs_v1(
            _bundle(_generic_contract()),
            market_snapshot_repository=market_repo,
            reference_data_set_repository=ref_repo,
            valuation_policy_set_repository=policy_repo,
            valuation_context_repository=context_repo,
            numerical_policy_snapshot_repository=numeric_repo,
        )


def test_missing_reference_data_fails() -> None:
    market_repo, ref_repo, policy_repo, context_repo, numeric_repo = _resolver_dependencies(include_reference_data=False)

    with pytest.raises(OptionValuationInputResolutionError, match="reference_data_set"):
        resolve_option_inputs_v1(
            _bundle(_generic_contract()),
            market_snapshot_repository=market_repo,
            reference_data_set_repository=ref_repo,
            valuation_policy_set_repository=policy_repo,
            valuation_context_repository=context_repo,
            numerical_policy_snapshot_repository=numeric_repo,
        )


def test_missing_volatility_surface_fails() -> None:
    market_repo, ref_repo, policy_repo, context_repo, numeric_repo = _resolver_dependencies(include_vol=False)

    with pytest.raises(OptionValuationInputResolutionError, match="volatility"):
        resolve_fx_option_inputs_v1(
            _bundle(_fx_contract()),
            market_snapshot_repository=market_repo,
            reference_data_set_repository=ref_repo,
            valuation_policy_set_repository=policy_repo,
            valuation_context_repository=context_repo,
            numerical_policy_snapshot_repository=numeric_repo,
        )


def test_resolver_outputs_are_identical_for_identical_inputs() -> None:
    market_repo, ref_repo, policy_repo, context_repo, numeric_repo = _resolver_dependencies()

    result_1 = resolve_fx_option_inputs_v1(
        _bundle(_fx_contract()),
        market_snapshot_repository=market_repo,
        reference_data_set_repository=ref_repo,
        valuation_policy_set_repository=policy_repo,
        valuation_context_repository=context_repo,
        numerical_policy_snapshot_repository=numeric_repo,
    )
    result_2 = resolve_fx_option_inputs_v1(
        _bundle(_fx_contract()),
        market_snapshot_repository=market_repo,
        reference_data_set_repository=ref_repo,
        valuation_policy_set_repository=policy_repo,
        valuation_context_repository=context_repo,
        numerical_policy_snapshot_repository=numeric_repo,
    )

    assert result_1 == result_2
    assert result_1.resolved_kernel_scalars.domestic_rate == result_1.domestic_curve.points[0].zero_rate
    assert result_1.resolved_kernel_scalars.foreign_rate == result_1.foreign_curve.points[0].zero_rate
    assert result_1.resolved_kernel_scalars.volatility == result_1.volatility_surface.points[0].implied_vol


def test_resolved_inputs_contain_no_repository_handles() -> None:
    market_repo, ref_repo, policy_repo, context_repo, numeric_repo = _resolver_dependencies()

    resolved = resolve_fx_option_inputs_v1(
        _bundle(_fx_contract()),
        market_snapshot_repository=market_repo,
        reference_data_set_repository=ref_repo,
        valuation_policy_set_repository=policy_repo,
        valuation_context_repository=context_repo,
        numerical_policy_snapshot_repository=numeric_repo,
    )

    field_names = {field.name for field in fields(resolved)}

    assert "market_snapshot_repository" not in field_names
    assert "reference_data_set_repository" not in field_names
    assert "valuation_policy_set_repository" not in field_names
    assert "valuation_context_repository" not in field_names
    assert "loader" not in " ".join(sorted(field_names)).lower()
    assert "resolved_kernel_scalars" in field_names


def test_missing_numerical_policy_snapshot_fails() -> None:
    market_repo, ref_repo, policy_repo, context_repo, _numeric_repo = _resolver_dependencies()
    missing_numeric_repo = _NumericalPolicyRepo(None)

    with pytest.raises(OptionValuationInputResolutionError, match="numerical policy snapshot"):
        resolve_fx_option_inputs_v1(
            _bundle(_fx_contract()),
            market_snapshot_repository=market_repo,
            reference_data_set_repository=ref_repo,
            valuation_policy_set_repository=policy_repo,
            valuation_context_repository=context_repo,
            numerical_policy_snapshot_repository=missing_numeric_repo,
        )


def test_invalid_numerical_policy_snapshot_fails_without_fallback() -> None:
    market_repo, ref_repo, policy_repo, context_repo, _numeric_repo = _resolver_dependencies()

    with pytest.raises(OptionValuationInputResolutionError, match="numerical policy snapshot"):
        resolve_fx_option_inputs_v1(
            _bundle(_fx_contract()),
            market_snapshot_repository=market_repo,
            reference_data_set_repository=ref_repo,
            valuation_policy_set_repository=policy_repo,
            valuation_context_repository=context_repo,
            numerical_policy_snapshot_repository=_MalformedNumericalPolicyRepo(),
        )


def test_fx_kernel_scalar_selection_policy_uses_primary_vol_tenor_after_canonical_sort() -> None:
    assert FX_KERNEL_SCALAR_SELECTION_POLICY_V1 == "primary_vol_tenor_after_canonical_sort"

    market_repo, ref_repo, policy_repo, context_repo, numeric_repo = _resolver_dependencies()
    snapshot = market_repo.get_by_id("mkt.snap.001")
    assert snapshot is not None

    # Intentionally provide unsorted quote keys to prove resolver uses canonical sort before choosing primary tenor.
    snapshot.vols.surfaces["delta-neutral-vol"].data["quotes"] = {
        "USD/ILS|3M|3.65|call": 0.33,
        "USD/ILS|1M|3.65|call": 0.12,
    }

    resolved = resolve_fx_option_inputs_v1(
        _bundle(_fx_contract()),
        market_snapshot_repository=market_repo,
        reference_data_set_repository=ref_repo,
        valuation_policy_set_repository=policy_repo,
        valuation_context_repository=context_repo,
        numerical_policy_snapshot_repository=numeric_repo,
    )

    # Canonical sort picks 1M first, so primary tenor is 1M and all kernel scalars align to 1M.
    assert resolved.resolved_kernel_scalars.time_to_expiry_years == Decimal("1") / Decimal("12")
    assert resolved.resolved_kernel_scalars.volatility == Decimal("0.12")
    assert resolved.resolved_kernel_scalars.domestic_rate == resolved.domestic_curve.points[0].zero_rate
    assert resolved.resolved_kernel_scalars.foreign_rate == resolved.foreign_curve.points[0].zero_rate
