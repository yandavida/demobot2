from __future__ import annotations

import datetime
from decimal import Decimal

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.resolved_input_canonicalization_v1 import canonical_decimal_str_v1
from core.contracts.resolved_input_canonicalization_v1 import canonical_resolved_input_hash_v1
from core.contracts.resolved_input_canonicalization_v1 import canonical_timestamp_str_v1
from core.contracts.resolved_option_valuation_inputs_v1 import NumericalPolicySnapshotV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedCurveInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedRatePointV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedSpotInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityPointV1


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
            surface_id="delta-neutral-vol",
            quote_convention="implied_vol",
            interpolation_method="surface_quote_map_lookup",
            extrapolation_policy="none",
            basis_timestamp=valuation_ts,
            source_lineage_ref="market_snapshot:mkt.snap.001:vol_surface:delta-neutral-vol",
            points=(
                ResolvedVolatilityPointV1(tenor_label="1M", strike="3.65", implied_vol="0.12"),
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
        resolved_basis_hash="sha256:placeholder",
    )


def test_canonical_decimal_str_is_deterministic() -> None:
    assert canonical_decimal_str_v1("3.7000") == "3.7"
    assert canonical_decimal_str_v1(3.7) == "3.7"
    assert canonical_decimal_str_v1("0.000") == "0"


def test_canonical_timestamp_str_is_utc_normalized() -> None:
    value = datetime.datetime(2026, 12, 31, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
    assert canonical_timestamp_str_v1(value) == "2026-12-31T10:00:00.000000Z"


def test_canonical_hash_is_deterministic_for_equivalent_nested_payloads() -> None:
    payload_a = {
        "valuation_timestamp": datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
        "spot": Decimal("3.7000"),
        "null_example": None,
        "nested": {"b": "2", "a": "1"},
    }
    payload_b = {
        "nested": {"a": "1", "b": "2"},
        "spot": 3.7,
        "valuation_timestamp": datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc),
        "null_example": None,
    }

    assert canonical_resolved_input_hash_v1(payload_a) == canonical_resolved_input_hash_v1(payload_b)


def test_canonical_hash_handles_resolved_fx_input_objects() -> None:
    resolved = _resolved_fx_inputs()
    hash_1 = canonical_resolved_input_hash_v1({"resolved": resolved})
    hash_2 = canonical_resolved_input_hash_v1({"resolved": resolved})

    assert hash_1 == hash_2
