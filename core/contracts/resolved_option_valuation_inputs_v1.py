from __future__ import annotations

from dataclasses import dataclass
import datetime
from decimal import Decimal
from decimal import InvalidOperation

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.option_runtime_contract_v1 import OptionRuntimeContractV1


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _require_positive_decimal(value: Decimal | str | int | float, field_name: str) -> Decimal:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid decimal") from exc

    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value <= 0:
        raise ValueError(f"{field_name} must be > 0")

    return decimal_value


def _require_finite_decimal(value: Decimal | str | int | float, field_name: str) -> Decimal:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid decimal") from exc

    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")

    return decimal_value


def _require_datetime(value: datetime.datetime, field_name: str) -> datetime.datetime:
    if not isinstance(value, datetime.datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _normalize_non_empty_string_tuple(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple) or len(values) == 0:
        raise ValueError(f"{field_name} must be a non-empty tuple")

    normalized: list[str] = []
    for value in values:
        normalized.append(_require_non_empty_string(value, f"{field_name} entry"))
    return tuple(normalized)


@dataclass(frozen=True)
class ResolvedSpotInputV1:
    """Resolved underlying spot input for deterministic engine invocation."""

    underlying_instrument_ref: str
    spot: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "underlying_instrument_ref",
            _require_non_empty_string(self.underlying_instrument_ref, "underlying_instrument_ref"),
        )
        object.__setattr__(self, "spot", _require_positive_decimal(self.spot, "spot"))


@dataclass(frozen=True)
class ResolvedRatePointV1:
    """Single resolved curve point used by a resolved curve input."""

    tenor_label: str
    zero_rate: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "tenor_label", _require_non_empty_string(self.tenor_label, "tenor_label"))
        object.__setattr__(self, "zero_rate", _require_finite_decimal(self.zero_rate, "zero_rate"))


@dataclass(frozen=True)
class ResolvedCurveInputV1:
    """Resolved curve input for engine-facing valuation calls."""

    curve_id: str
    quote_convention: str
    interpolation_method: str
    extrapolation_policy: str
    basis_timestamp: datetime.datetime
    source_lineage_ref: str
    points: tuple[ResolvedRatePointV1, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "curve_id", _require_non_empty_string(self.curve_id, "curve_id"))
        object.__setattr__(
            self,
            "quote_convention",
            _require_non_empty_string(self.quote_convention, "quote_convention"),
        )
        object.__setattr__(
            self,
            "interpolation_method",
            _require_non_empty_string(self.interpolation_method, "interpolation_method"),
        )
        object.__setattr__(
            self,
            "extrapolation_policy",
            _require_non_empty_string(self.extrapolation_policy, "extrapolation_policy"),
        )
        object.__setattr__(
            self,
            "basis_timestamp",
            _require_datetime(self.basis_timestamp, "basis_timestamp"),
        )
        object.__setattr__(
            self,
            "source_lineage_ref",
            _require_non_empty_string(self.source_lineage_ref, "source_lineage_ref"),
        )
        if not isinstance(self.points, tuple) or len(self.points) == 0:
            raise ValueError("points must be a non-empty tuple")
        seen_tenors: set[str] = set()
        for point in self.points:
            if not isinstance(point, ResolvedRatePointV1):
                raise ValueError("points entries must be ResolvedRatePointV1")
            if point.tenor_label in seen_tenors:
                raise ValueError("points tenor_label values must be unique")
            seen_tenors.add(point.tenor_label)


@dataclass(frozen=True)
class ResolvedVolatilityPointV1:
    """Single resolved volatility node for deterministic surface input."""

    tenor_label: str
    strike: Decimal
    implied_vol: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "tenor_label", _require_non_empty_string(self.tenor_label, "tenor_label"))
        object.__setattr__(self, "strike", _require_positive_decimal(self.strike, "strike"))
        object.__setattr__(self, "implied_vol", _require_positive_decimal(self.implied_vol, "implied_vol"))


@dataclass(frozen=True)
class ResolvedVolatilityInputV1:
    """Resolved volatility surface input for engine-facing valuation calls."""

    surface_id: str
    quote_convention: str
    interpolation_method: str
    extrapolation_policy: str
    basis_timestamp: datetime.datetime
    source_lineage_ref: str
    points: tuple[ResolvedVolatilityPointV1, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "surface_id", _require_non_empty_string(self.surface_id, "surface_id"))
        object.__setattr__(
            self,
            "quote_convention",
            _require_non_empty_string(self.quote_convention, "quote_convention"),
        )
        object.__setattr__(
            self,
            "interpolation_method",
            _require_non_empty_string(self.interpolation_method, "interpolation_method"),
        )
        object.__setattr__(
            self,
            "extrapolation_policy",
            _require_non_empty_string(self.extrapolation_policy, "extrapolation_policy"),
        )
        object.__setattr__(
            self,
            "basis_timestamp",
            _require_datetime(self.basis_timestamp, "basis_timestamp"),
        )
        object.__setattr__(
            self,
            "source_lineage_ref",
            _require_non_empty_string(self.source_lineage_ref, "source_lineage_ref"),
        )
        if not isinstance(self.points, tuple) or len(self.points) == 0:
            raise ValueError("points must be a non-empty tuple")
        seen_nodes: set[tuple[str, str]] = set()
        for point in self.points:
            if not isinstance(point, ResolvedVolatilityPointV1):
                raise ValueError("points entries must be ResolvedVolatilityPointV1")
            node_key = (point.tenor_label, str(point.strike))
            if node_key in seen_nodes:
                raise ValueError("points tenor/strike nodes must be unique")
            seen_nodes.add(node_key)


@dataclass(frozen=True)
class ResolvedConventionBasisV1:
    """Resolved convention basis used by valuation engines without lookups."""

    day_count_basis: str
    calendar_set: tuple[str, ...]
    settlement_conventions: tuple[str, ...]
    premium_conventions: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "day_count_basis", _require_non_empty_string(self.day_count_basis, "day_count_basis"))
        object.__setattr__(
            self,
            "calendar_set",
            _normalize_non_empty_string_tuple(self.calendar_set, "calendar_set"),
        )
        object.__setattr__(
            self,
            "settlement_conventions",
            _normalize_non_empty_string_tuple(self.settlement_conventions, "settlement_conventions"),
        )
        object.__setattr__(
            self,
            "premium_conventions",
            _normalize_non_empty_string_tuple(self.premium_conventions, "premium_conventions"),
        )


@dataclass(frozen=True)
class NumericalPolicySnapshotV1:
    """Resolved numerical policy snapshot consumed directly by valuation engines."""

    numeric_policy_id: str
    tolerance: Decimal
    max_iterations: int
    rounding_decimals: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "numeric_policy_id", _require_non_empty_string(self.numeric_policy_id, "numeric_policy_id"))
        object.__setattr__(self, "tolerance", _require_positive_decimal(self.tolerance, "tolerance"))

        if not isinstance(self.max_iterations, int) or self.max_iterations <= 0:
            raise ValueError("max_iterations must be a positive integer")
        if not isinstance(self.rounding_decimals, int) or self.rounding_decimals < 0:
            raise ValueError("rounding_decimals must be a non-negative integer")


@dataclass(frozen=True)
class ResolvedFxKernelScalarsV1:
    """Resolved scalar kernel inputs for deterministic FX option valuation."""

    domestic_rate: Decimal
    foreign_rate: Decimal
    volatility: Decimal
    time_to_expiry_years: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "domestic_rate", _require_finite_decimal(self.domestic_rate, "domestic_rate"))
        object.__setattr__(self, "foreign_rate", _require_finite_decimal(self.foreign_rate, "foreign_rate"))
        object.__setattr__(self, "volatility", _require_finite_decimal(self.volatility, "volatility"))
        object.__setattr__(
            self,
            "time_to_expiry_years",
            _require_finite_decimal(self.time_to_expiry_years, "time_to_expiry_years"),
        )

        if self.volatility < 0:
            raise ValueError("volatility must be >= 0")
        if self.time_to_expiry_years < 0:
            raise ValueError("time_to_expiry_years must be >= 0")


@dataclass(frozen=True)
class ResolvedOptionValuationInputsV1:
    """Engine-facing resolved valuation inputs for generic options."""

    option_contract: OptionRuntimeContractV1
    valuation_timestamp: datetime.datetime
    resolved_underlying_input: ResolvedSpotInputV1
    resolved_convention_basis: ResolvedConventionBasisV1
    numerical_policy_snapshot: NumericalPolicySnapshotV1
    resolved_basis_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.option_contract, OptionRuntimeContractV1):
            raise ValueError("option_contract must be OptionRuntimeContractV1")
        object.__setattr__(
            self,
            "valuation_timestamp",
            _require_datetime(self.valuation_timestamp, "valuation_timestamp"),
        )
        if not isinstance(self.resolved_underlying_input, ResolvedSpotInputV1):
            raise ValueError("resolved_underlying_input must be ResolvedSpotInputV1")
        if not isinstance(self.resolved_convention_basis, ResolvedConventionBasisV1):
            raise ValueError("resolved_convention_basis must be ResolvedConventionBasisV1")
        if not isinstance(self.numerical_policy_snapshot, NumericalPolicySnapshotV1):
            raise ValueError("numerical_policy_snapshot must be NumericalPolicySnapshotV1")
        object.__setattr__(
            self,
            "resolved_basis_hash",
            _require_non_empty_string(self.resolved_basis_hash, "resolved_basis_hash"),
        )


@dataclass(frozen=True)
class ResolvedFxOptionValuationInputsV1:
    """Engine-facing resolved valuation inputs for FX options."""

    fx_option_contract: FxOptionRuntimeContractV1
    valuation_timestamp: datetime.datetime
    spot: ResolvedSpotInputV1
    domestic_curve: ResolvedCurveInputV1
    foreign_curve: ResolvedCurveInputV1
    volatility_surface: ResolvedVolatilityInputV1
    day_count_basis: str
    calendar_set: tuple[str, ...]
    settlement_conventions: tuple[str, ...]
    premium_conventions: tuple[str, ...]
    numerical_policy_snapshot: NumericalPolicySnapshotV1
    resolved_kernel_scalars: ResolvedFxKernelScalarsV1
    resolved_basis_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.fx_option_contract, FxOptionRuntimeContractV1):
            raise ValueError("fx_option_contract must be FxOptionRuntimeContractV1")
        object.__setattr__(
            self,
            "valuation_timestamp",
            _require_datetime(self.valuation_timestamp, "valuation_timestamp"),
        )

        if not isinstance(self.spot, ResolvedSpotInputV1):
            raise ValueError("spot must be ResolvedSpotInputV1")
        if not isinstance(self.domestic_curve, ResolvedCurveInputV1):
            raise ValueError("domestic_curve must be ResolvedCurveInputV1")
        if not isinstance(self.foreign_curve, ResolvedCurveInputV1):
            raise ValueError("foreign_curve must be ResolvedCurveInputV1")
        if not isinstance(self.volatility_surface, ResolvedVolatilityInputV1):
            raise ValueError("volatility_surface must be ResolvedVolatilityInputV1")

        object.__setattr__(self, "day_count_basis", _require_non_empty_string(self.day_count_basis, "day_count_basis"))
        object.__setattr__(
            self,
            "calendar_set",
            _normalize_non_empty_string_tuple(self.calendar_set, "calendar_set"),
        )
        object.__setattr__(
            self,
            "settlement_conventions",
            _normalize_non_empty_string_tuple(self.settlement_conventions, "settlement_conventions"),
        )
        object.__setattr__(
            self,
            "premium_conventions",
            _normalize_non_empty_string_tuple(self.premium_conventions, "premium_conventions"),
        )

        if not isinstance(self.numerical_policy_snapshot, NumericalPolicySnapshotV1):
            raise ValueError("numerical_policy_snapshot must be NumericalPolicySnapshotV1")
        if not isinstance(self.resolved_kernel_scalars, ResolvedFxKernelScalarsV1):
            raise ValueError("resolved_kernel_scalars must be ResolvedFxKernelScalarsV1")

        object.__setattr__(
            self,
            "resolved_basis_hash",
            _require_non_empty_string(self.resolved_basis_hash, "resolved_basis_hash"),
        )


__all__ = [
    "NumericalPolicySnapshotV1",
    "ResolvedConventionBasisV1",
    "ResolvedCurveInputV1",
    "ResolvedFxOptionValuationInputsV1",
    "ResolvedFxKernelScalarsV1",
    "ResolvedOptionValuationInputsV1",
    "ResolvedRatePointV1",
    "ResolvedSpotInputV1",
    "ResolvedVolatilityInputV1",
    "ResolvedVolatilityPointV1",
]
