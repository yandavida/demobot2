from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Optional, Protocol

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.option_valuation_dependency_bundle_v1 import OptionValuationDependencyBundleV1
from core.contracts.resolved_option_valuation_inputs_v1 import NumericalPolicySnapshotV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedConventionBasisV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedCurveInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedOptionValuationInputsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedRatePointV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedSpotInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityPointV1
from core.contracts.reference_data_set import ReferenceDataSet
from core.contracts.valuation_context import ValuationContext
from core.contracts.valuation_policy_set import ValuationPolicySet
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.persistence.repositories import MarketSnapshotRepository
from core.persistence.repositories import ReferenceDataSetRepository
from core.persistence.repositories import ValuationPolicySetRepository


class OptionValuationInputResolutionError(ValueError):
    """Raised when dependency bundle cannot be resolved into engine-ready inputs."""


class ValuationContextRepository(Protocol):
    def get_by_id(self, valuation_context_id: str) -> Optional[ValuationContext]:
        ...


class NumericalPolicySnapshotRepository(Protocol):
    def get_by_numeric_policy_id(self, numeric_policy_id: str) -> Optional[NumericalPolicySnapshotV1]:
        ...


def _require_non_empty_tuple(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) == 0:
        raise OptionValuationInputResolutionError(f"{field_name} must be non-empty for resolved inputs")
    return values


def _canonical_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _load_dependencies(
    bundle: OptionValuationDependencyBundleV1,
    *,
    market_snapshot_repository: MarketSnapshotRepository,
    reference_data_set_repository: ReferenceDataSetRepository,
    valuation_policy_set_repository: ValuationPolicySetRepository,
    valuation_context_repository: ValuationContextRepository,
) -> tuple[MarketSnapshotPayloadV0, ReferenceDataSet, ValuationPolicySet, ValuationContext]:
    market_snapshot = market_snapshot_repository.get_by_id(bundle.market_snapshot_id)
    if market_snapshot is None:
        raise OptionValuationInputResolutionError("market_snapshot not found for market_snapshot_id")

    reference_data_set = reference_data_set_repository.get_by_id(bundle.reference_data_set_id)
    if reference_data_set is None:
        raise OptionValuationInputResolutionError("reference_data_set not found for reference_data_set_id")

    valuation_policy_set = valuation_policy_set_repository.get_by_id(bundle.valuation_policy_set_id)
    if valuation_policy_set is None:
        raise OptionValuationInputResolutionError("valuation_policy_set not found for valuation_policy_set_id")

    valuation_context = valuation_context_repository.get_by_id(bundle.valuation_context_id)
    if valuation_context is None:
        raise OptionValuationInputResolutionError("valuation_context not found for valuation_context_id")

    if valuation_context.market_snapshot_id != bundle.market_snapshot_id:
        raise OptionValuationInputResolutionError("valuation_context market_snapshot_id mismatch")
    if valuation_context.reference_data_set_id != bundle.reference_data_set_id:
        raise OptionValuationInputResolutionError("valuation_context reference_data_set_id mismatch")
    if valuation_context.valuation_policy_set_id != bundle.valuation_policy_set_id:
        raise OptionValuationInputResolutionError("valuation_context valuation_policy_set_id mismatch")

    return market_snapshot, reference_data_set, valuation_policy_set, valuation_context


def _resolve_numerical_policy_snapshot(
    valuation_policy_set: ValuationPolicySet,
    *,
    numerical_policy_snapshot_repository: NumericalPolicySnapshotRepository,
) -> NumericalPolicySnapshotV1:
    snapshot = numerical_policy_snapshot_repository.get_by_numeric_policy_id(
        valuation_policy_set.numeric_policy_id
    )
    if snapshot is None:
        raise OptionValuationInputResolutionError("numerical policy snapshot not found for numeric_policy_id")
    return snapshot


def resolve_option_inputs_v1(
    bundle: OptionValuationDependencyBundleV1,
    *,
    market_snapshot_repository: MarketSnapshotRepository,
    reference_data_set_repository: ReferenceDataSetRepository,
    valuation_policy_set_repository: ValuationPolicySetRepository,
    valuation_context_repository: ValuationContextRepository,
    numerical_policy_snapshot_repository: NumericalPolicySnapshotRepository,
) -> ResolvedOptionValuationInputsV1:
    """Resolve generic option dependencies into engine-facing, immutable inputs."""

    (
        market_snapshot,
        reference_data_set,
        valuation_policy_set,
        valuation_context,
    ) = _load_dependencies(
        bundle,
        market_snapshot_repository=market_snapshot_repository,
        reference_data_set_repository=reference_data_set_repository,
        valuation_policy_set_repository=valuation_policy_set_repository,
        valuation_context_repository=valuation_context_repository,
    )

    underlying = bundle.option_contract.underlying_instrument_ref
    spot_value = market_snapshot.spots.prices.get(underlying)
    if spot_value is None:
        raise OptionValuationInputResolutionError("spot missing for option underlying_instrument_ref")

    holiday_calendars = _require_non_empty_tuple(
        reference_data_set.holiday_calendar_refs,
        "reference_data_set.holiday_calendar_refs",
    )
    day_count_refs = _require_non_empty_tuple(
        reference_data_set.day_count_convention_refs,
        "reference_data_set.day_count_convention_refs",
    )
    settlement_refs = _require_non_empty_tuple(
        reference_data_set.settlement_convention_refs,
        "reference_data_set.settlement_convention_refs",
    )

    numerical_policy_snapshot = _resolve_numerical_policy_snapshot(
        valuation_policy_set,
        numerical_policy_snapshot_repository=numerical_policy_snapshot_repository,
    )

    resolved_inputs = ResolvedOptionValuationInputsV1(
        option_contract=bundle.option_contract,
        valuation_timestamp=valuation_context.valuation_timestamp,
        resolved_underlying_input=ResolvedSpotInputV1(
            underlying_instrument_ref=underlying,
            spot=spot_value,
        ),
        resolved_convention_basis=ResolvedConventionBasisV1(
            day_count_basis=day_count_refs[0],
            calendar_set=holiday_calendars,
            settlement_conventions=settlement_refs,
            premium_conventions=settlement_refs,
        ),
        numerical_policy_snapshot=numerical_policy_snapshot,
        resolved_basis_hash=_canonical_hash(
            {
                "contract_id": bundle.option_contract.contract_id,
                "valuation_context_id": bundle.valuation_context_id,
                "market_snapshot_id": bundle.market_snapshot_id,
                "reference_data_set_id": bundle.reference_data_set_id,
                "valuation_policy_set_id": bundle.valuation_policy_set_id,
                "spot": str(spot_value),
                "numeric_policy_id": numerical_policy_snapshot.numeric_policy_id,
            }
        ),
    )

    return resolved_inputs


def _resolve_curve_from_snapshot(
    market_snapshot: MarketSnapshotPayloadV0,
    *,
    curve_id: str,
) -> ResolvedCurveInputV1:
    curve = market_snapshot.curves.curves.get(curve_id)
    if curve is None:
        raise OptionValuationInputResolutionError(f"curve missing for curve_id '{curve_id}'")

    if len(curve.zero_rates) == 0:
        raise OptionValuationInputResolutionError(f"curve zero_rates must be non-empty for curve_id '{curve_id}'")

    points = tuple(
        ResolvedRatePointV1(tenor_label=tenor, zero_rate=curve.zero_rates[tenor])
        for tenor in sorted(curve.zero_rates.keys())
    )
    return ResolvedCurveInputV1(curve_id=curve_id, points=points)


def _resolve_vol_surface_from_snapshot(
    market_snapshot: MarketSnapshotPayloadV0,
    *,
    surface_id: str,
    fallback_strike: object,
) -> ResolvedVolatilityInputV1:
    if market_snapshot.vols is None:
        raise OptionValuationInputResolutionError("volatility surfaces missing in market snapshot")

    surface = market_snapshot.vols.surfaces.get(surface_id)
    if surface is None:
        raise OptionValuationInputResolutionError("volatility surface missing for contract convention")

    if not isinstance(surface.data, dict):
        raise OptionValuationInputResolutionError("volatility surface data must be a dict")

    quotes = surface.data.get("quotes")
    if isinstance(quotes, dict) and len(quotes) > 0:
        points: list[ResolvedVolatilityPointV1] = []
        for key in sorted(quotes.keys()):
            raw_value = quotes[key]
            parts = key.split("|")
            if len(parts) != 4:
                raise OptionValuationInputResolutionError("vol quote key must use canonical 4-part format")

            tenor_label = parts[1]
            strike_token = parts[2]
            strike_value = fallback_strike if strike_token == "*" else strike_token
            points.append(
                ResolvedVolatilityPointV1(
                    tenor_label=tenor_label,
                    strike=strike_value,
                    implied_vol=raw_value,
                )
            )

        return ResolvedVolatilityInputV1(surface_id=surface_id, points=tuple(points))

    if "vol" in surface.data:
        return ResolvedVolatilityInputV1(
            surface_id=surface_id,
            points=(
                ResolvedVolatilityPointV1(
                    tenor_label="atm",
                    strike=fallback_strike,
                    implied_vol=surface.data["vol"],
                ),
            ),
        )

    raise OptionValuationInputResolutionError("volatility surface data missing quotes/vol payload")


def resolve_fx_option_inputs_v1(
    bundle: OptionValuationDependencyBundleV1,
    *,
    market_snapshot_repository: MarketSnapshotRepository,
    reference_data_set_repository: ReferenceDataSetRepository,
    valuation_policy_set_repository: ValuationPolicySetRepository,
    valuation_context_repository: ValuationContextRepository,
    numerical_policy_snapshot_repository: NumericalPolicySnapshotRepository,
) -> ResolvedFxOptionValuationInputsV1:
    """Resolve FX option dependencies into engine-facing, immutable inputs."""

    if not isinstance(bundle.option_contract, FxOptionRuntimeContractV1):
        raise OptionValuationInputResolutionError("bundle.option_contract must be FxOptionRuntimeContractV1")

    (
        market_snapshot,
        reference_data_set,
        valuation_policy_set,
        valuation_context,
    ) = _load_dependencies(
        bundle,
        market_snapshot_repository=market_snapshot_repository,
        reference_data_set_repository=reference_data_set_repository,
        valuation_policy_set_repository=valuation_policy_set_repository,
        valuation_context_repository=valuation_context_repository,
    )

    fx_contract = bundle.option_contract
    spot_key = f"{fx_contract.base_currency}/{fx_contract.quote_currency}"
    spot_value = market_snapshot.spots.prices.get(spot_key)
    if spot_value is None:
        raise OptionValuationInputResolutionError("spot missing for fx option base/quote pair")

    holiday_calendars = _require_non_empty_tuple(
        reference_data_set.holiday_calendar_refs,
        "reference_data_set.holiday_calendar_refs",
    )
    settlement_refs = _require_non_empty_tuple(
        reference_data_set.settlement_convention_refs,
        "reference_data_set.settlement_convention_refs",
    )
    day_count_refs = _require_non_empty_tuple(
        reference_data_set.day_count_convention_refs,
        "reference_data_set.day_count_convention_refs",
    )

    if market_snapshot.conventions.day_count_default not in day_count_refs:
        raise OptionValuationInputResolutionError(
            "market snapshot day_count_default not present in reference_data_set day count refs"
        )

    domestic_curve = _resolve_curve_from_snapshot(
        market_snapshot,
        curve_id=fx_contract.domestic_curve_id,
    )
    foreign_curve = _resolve_curve_from_snapshot(
        market_snapshot,
        curve_id=fx_contract.foreign_curve_id,
    )

    volatility_surface = _resolve_vol_surface_from_snapshot(
        market_snapshot,
        surface_id=fx_contract.volatility_surface_quote_convention,
        fallback_strike=fx_contract.strike,
    )

    numerical_policy_snapshot = _resolve_numerical_policy_snapshot(
        valuation_policy_set,
        numerical_policy_snapshot_repository=numerical_policy_snapshot_repository,
    )

    resolved_inputs = ResolvedFxOptionValuationInputsV1(
        fx_option_contract=fx_contract,
        valuation_timestamp=valuation_context.valuation_timestamp,
        spot=ResolvedSpotInputV1(underlying_instrument_ref=spot_key, spot=spot_value),
        domestic_curve=domestic_curve,
        foreign_curve=foreign_curve,
        volatility_surface=volatility_surface,
        day_count_basis=market_snapshot.conventions.day_count_default,
        calendar_set=holiday_calendars,
        settlement_conventions=settlement_refs,
        premium_conventions=(f"premium_currency:{fx_contract.premium_currency}",),
        numerical_policy_snapshot=numerical_policy_snapshot,
        resolved_basis_hash=_canonical_hash(
            {
                "contract_id": fx_contract.contract_id,
                "valuation_context_id": bundle.valuation_context_id,
                "market_snapshot_id": bundle.market_snapshot_id,
                "reference_data_set_id": bundle.reference_data_set_id,
                "valuation_policy_set_id": bundle.valuation_policy_set_id,
                "spot": str(spot_value),
                "domestic_curve": asdict(domestic_curve),
                "foreign_curve": asdict(foreign_curve),
                "volatility_surface": asdict(volatility_surface),
                "numeric_policy_id": numerical_policy_snapshot.numeric_policy_id,
            }
        ),
    )

    return resolved_inputs


__all__ = [
    "NumericalPolicySnapshotRepository",
    "OptionValuationInputResolutionError",
    "ValuationContextRepository",
    "resolve_fx_option_inputs_v1",
    "resolve_option_inputs_v1",
]
