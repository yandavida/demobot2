from __future__ import annotations

import datetime
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
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import theta_rolled_inputs_boundary_reference_v1
from core.services import theta_rolled_fx_inputs_boundary_preparer_v1
from core.services.theta_rolled_fx_inputs_boundary_preparer_v1 import prepare_theta_rolled_fx_inputs_boundary_v1


def _fx_contract() -> FxOptionRuntimeContractV1:
    return FxOptionRuntimeContractV1(
        contract_id="fx-opt-amer-d2-2-001",
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


def _resolved_fx_inputs(
    *,
    basis_hash: str,
    time_to_expiry_years: str,
    contract: FxOptionRuntimeContractV1 | None = None,
) -> ResolvedFxOptionValuationInputsV1:
    valuation_ts = datetime.datetime(2026, 12, 31, 10, 0, tzinfo=datetime.timezone.utc)
    return ResolvedFxOptionValuationInputsV1(
        fx_option_contract=_fx_contract() if contract is None else contract,
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


def test_successful_preparation_returns_governed_boundary() -> None:
    contract = _fx_contract()
    current = _resolved_fx_inputs(
        basis_hash="sha256:current",
        time_to_expiry_years="0.08333333333333333333333333333",
        contract=contract,
    )
    rolled = _resolved_fx_inputs(
        basis_hash="sha256:rolled",
        time_to_expiry_years="0.08059360730593607305936073059",
        contract=contract,
    )

    prepared = prepare_theta_rolled_fx_inputs_boundary_v1(
        current_resolved_inputs=current,
        theta_rolled_resolved_inputs=rolled,
    )

    assert isinstance(prepared, ThetaRolledFxInputsBoundaryV1)
    assert prepared.current_resolved_inputs == current
    assert prepared.theta_rolled_resolved_inputs == rolled


def test_policy_id_is_fixed_to_governed_constant() -> None:
    contract = _fx_contract()
    prepared = prepare_theta_rolled_fx_inputs_boundary_v1(
        current_resolved_inputs=_resolved_fx_inputs(
            basis_hash="sha256:current",
            time_to_expiry_years="0.08333333333333333333333333333",
            contract=contract,
        ),
        theta_rolled_resolved_inputs=_resolved_fx_inputs(
            basis_hash="sha256:rolled",
            time_to_expiry_years="0.08059360730593607305936073059",
            contract=contract,
        ),
    )

    assert prepared.theta_roll_policy_id == THETA_ROLLED_INPUT_POLICY_ID_V1


def test_deterministic_rerun_identity_for_equal_inputs() -> None:
    contract = _fx_contract()
    current = _resolved_fx_inputs(
        basis_hash="sha256:current",
        time_to_expiry_years="0.08333333333333333333333333333",
        contract=contract,
    )
    rolled = _resolved_fx_inputs(
        basis_hash="sha256:rolled",
        time_to_expiry_years="0.08059360730593607305936073059",
        contract=contract,
    )

    first = prepare_theta_rolled_fx_inputs_boundary_v1(
        current_resolved_inputs=current,
        theta_rolled_resolved_inputs=rolled,
    )
    second = prepare_theta_rolled_fx_inputs_boundary_v1(
        current_resolved_inputs=current,
        theta_rolled_resolved_inputs=rolled,
    )

    assert first == second


def test_rejects_wrong_input_types() -> None:
    with pytest.raises(ValueError, match="current_resolved_inputs"):
        prepare_theta_rolled_fx_inputs_boundary_v1(
            current_resolved_inputs=object(),  # type: ignore[arg-type]
            theta_rolled_resolved_inputs=_resolved_fx_inputs(
                basis_hash="sha256:rolled",
                time_to_expiry_years="0.08059360730593607305936073059",
            ),
        )

    with pytest.raises(ValueError, match="theta_rolled_resolved_inputs"):
        prepare_theta_rolled_fx_inputs_boundary_v1(
            current_resolved_inputs=_resolved_fx_inputs(
                basis_hash="sha256:current",
                time_to_expiry_years="0.08333333333333333333333333333",
            ),
            theta_rolled_resolved_inputs=object(),  # type: ignore[arg-type]
        )


def test_rejects_same_object_inputs() -> None:
    current = _resolved_fx_inputs(
        basis_hash="sha256:current",
        time_to_expiry_years="0.08333333333333333333333333333",
    )

    with pytest.raises(ValueError, match="distinct objects"):
        prepare_theta_rolled_fx_inputs_boundary_v1(
            current_resolved_inputs=current,
            theta_rolled_resolved_inputs=current,
        )


def test_rejects_fx_option_contract_mismatch() -> None:
    current_contract = _fx_contract()
    rolled_contract = _fx_contract()
    object.__setattr__(rolled_contract, "contract_id", "fx-opt-amer-d2-2-999")

    with pytest.raises(ValueError, match="same fx_option_contract"):
        prepare_theta_rolled_fx_inputs_boundary_v1(
            current_resolved_inputs=_resolved_fx_inputs(
                basis_hash="sha256:current",
                time_to_expiry_years="0.08333333333333333333333333333",
                contract=current_contract,
            ),
            theta_rolled_resolved_inputs=_resolved_fx_inputs(
                basis_hash="sha256:rolled",
                time_to_expiry_years="0.08059360730593607305936073059",
                contract=rolled_contract,
            ),
        )


def test_rejects_identical_resolved_basis_hash() -> None:
    contract = _fx_contract()

    with pytest.raises(ValueError, match="resolved_basis_hash must differ"):
        prepare_theta_rolled_fx_inputs_boundary_v1(
            current_resolved_inputs=_resolved_fx_inputs(
                basis_hash="sha256:same",
                time_to_expiry_years="0.08333333333333333333333333333",
                contract=contract,
            ),
            theta_rolled_resolved_inputs=_resolved_fx_inputs(
                basis_hash="sha256:same",
                time_to_expiry_years="0.08059360730593607305936073059",
                contract=contract,
            ),
        )


def test_rejects_rolled_time_not_strictly_less_than_current() -> None:
    contract = _fx_contract()

    with pytest.raises(ValueError, match="strictly less"):
        prepare_theta_rolled_fx_inputs_boundary_v1(
            current_resolved_inputs=_resolved_fx_inputs(
                basis_hash="sha256:current",
                time_to_expiry_years="0.08333333333333333333333333333",
                contract=contract,
            ),
            theta_rolled_resolved_inputs=_resolved_fx_inputs(
                basis_hash="sha256:rolled",
                time_to_expiry_years="0.08333333333333333333333333333",
                contract=contract,
            ),
        )


def test_boundary_reference_from_prepared_output_is_deterministic() -> None:
    contract = _fx_contract()
    current = _resolved_fx_inputs(
        basis_hash="sha256:current",
        time_to_expiry_years="0.08333333333333333333333333333",
        contract=contract,
    )
    rolled = _resolved_fx_inputs(
        basis_hash="sha256:rolled",
        time_to_expiry_years="0.08059360730593607305936073059",
        contract=contract,
    )

    first = prepare_theta_rolled_fx_inputs_boundary_v1(
        current_resolved_inputs=current,
        theta_rolled_resolved_inputs=rolled,
    )
    second = prepare_theta_rolled_fx_inputs_boundary_v1(
        current_resolved_inputs=current,
        theta_rolled_resolved_inputs=rolled,
    )

    first_reference = theta_rolled_inputs_boundary_reference_v1(first)
    second_reference = theta_rolled_inputs_boundary_reference_v1(second)

    assert first_reference == second_reference
    assert first_reference == (
        "ThetaRolledFxInputsBoundaryV1:"
        "current_resolved_input_reference=sha256:current;"
        "theta_rolled_resolved_input_reference=sha256:rolled;"
        "theta_roll_policy_id=theta_rolled_resolved_input_1d_calendar_upstream_v1"
    )


def test_preparation_module_has_no_hidden_calendar_pricing_or_resolver_imports() -> None:
    source = inspect.getsource(theta_rolled_fx_inputs_boundary_preparer_v1)

    assert "datetime" not in source
    assert "timedelta" not in source
    assert "calendar" not in source.lower()
    assert "crr_american_fx_kernel_v1" not in source
    assert "AmericanCrrFxEngineV1" not in source
    assert "option_valuation_input_resolver_v1" not in source
    assert "core.persistence" not in source
    assert "market_data" not in source
    assert "marketdata" not in source
