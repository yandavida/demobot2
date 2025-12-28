import pytest
from core.pricing.institutional_fx.models import InstitutionalFxMtmResult
from core.pricing.institutional_fx.swaps_models import FxSwapMtmResult
from core.validation.fx_recon.models import (
    BankMtmLegInput, BankFxForwardStatement, BankFxSwapStatement,
)
from core.validation.fx_recon.engine import (
    reconcile_fx_forward, reconcile_fx_swap
)
from core.contracts.money import Currency

ILS: Currency = "ILS"

# A) Forward exact match
def test_forward_exact_match():
    sys = InstitutionalFxMtmResult(
        mtm=100.0,
        currency=ILS,
        spot_component=60.0,
        forward_points_component=30.0,
        discounting_component=10.0,
    )
    bank_leg = BankMtmLegInput(
        mtm=100.0,
        currency=ILS,
        spot_component=60.0,
        forward_points_component=30.0,
        discounting_component=10.0,
    )
    bank = BankFxForwardStatement(
        pair="USD/ILS",
        notional_base=1_000_000,
        value_date=None,
        maturity_date=None,
        presentation_currency=ILS,
        mtm_total=100.0,
        leg=bank_leg,
    )
    result = reconcile_fx_forward(system=sys, bank=bank)
    assert result.delta.total_delta == 0.0
    assert all(v == 0.0 for v in result.delta.components_delta.values())
    assert "within_tolerance" in result.delta.notes

# B) Forward mismatch explanation
def test_forward_mismatch():
    sys = InstitutionalFxMtmResult(
        mtm=100.0,
        currency=ILS,
        spot_component=60.0,
        forward_points_component=30.0,
        discounting_component=10.0,
    )
    bank_leg = BankMtmLegInput(
        mtm=105.0,
        currency=ILS,
        spot_component=60.0,
        forward_points_component=30.0,
        discounting_component=15.0,
    )
    bank = BankFxForwardStatement(
        pair="USD/ILS",
        notional_base=1_000_000,
        value_date=None,
        maturity_date=None,
        presentation_currency=ILS,
        mtm_total=105.0,
        leg=bank_leg,
    )
    result = reconcile_fx_forward(system=sys, bank=bank, tol=0.01)
    assert result.delta.total_delta == -5.0
    assert result.delta.components_delta["discounting_component"] == -5.0
    assert "out_of_tolerance" in result.delta.notes

# C) Swap with legs provided
def test_swap_with_legs():
    from core.pricing.institutional_fx.models import InstitutionalFxMtmResult
    near = InstitutionalFxMtmResult(
        mtm=50.0,
        currency=ILS,
        spot_component=30.0,
        forward_points_component=15.0,
        discounting_component=5.0,
    )
    far = InstitutionalFxMtmResult(
        mtm=70.0,
        currency=ILS,
        spot_component=40.0,
        forward_points_component=20.0,
        discounting_component=10.0,
    )
    sys = FxSwapMtmResult(
        mtm=120.0,
        currency=ILS,
        near_leg=near,
        far_leg=far,
        notes=(),
    )
    bank_near = BankMtmLegInput(
        mtm=50.0,
        currency=ILS,
        spot_component=30.0,
        forward_points_component=15.0,
        discounting_component=5.0,
    )
    bank_far = BankMtmLegInput(
        mtm=70.0,
        currency=ILS,
        spot_component=40.0,
        forward_points_component=20.0,
        discounting_component=10.0,
    )
    bank = BankFxSwapStatement(
        pair="USD/ILS",
        base_notional=1_000_000,
        near_date=None,
        far_date=None,
        presentation_currency=ILS,
        mtm_total=120.0,
        near_leg=bank_near,
        far_leg=bank_far,
    )
    result = reconcile_fx_swap(system=sys, bank=bank)
    assert result.delta.total_delta == 0.0
    assert result.delta.near_delta == 0.0
    assert result.delta.far_delta == 0.0
    assert all(v == 0.0 for v in result.delta.components_delta.values())
    assert "within_tolerance" in result.delta.notes

# D) Swap where bank only has total
def test_swap_bank_total_only():
    near = InstitutionalFxMtmResult(
        mtm=50.0,
        currency=ILS,
        spot_component=30.0,
        forward_points_component=15.0,
        discounting_component=5.0,
    )
    far = InstitutionalFxMtmResult(
        mtm=70.0,
        currency=ILS,
        spot_component=40.0,
        forward_points_component=20.0,
        discounting_component=10.0,
    )
    sys = FxSwapMtmResult(
        mtm=120.0,
        currency=ILS,
        near_leg=near,
        far_leg=far,
        notes=(),
    )
    bank = BankFxSwapStatement(
        pair="USD/ILS",
        base_notional=1_000_000,
        near_date=None,
        far_date=None,
        presentation_currency=ILS,
        mtm_total=120.0,
        near_leg=None,
        far_leg=None,
    )
    result = reconcile_fx_swap(system=sys, bank=bank)
    assert result.delta.total_delta == 0.0
    assert result.delta.near_delta is None
    assert result.delta.far_delta is None
    assert "bank_legs_missing" in result.delta.notes
    assert "within_tolerance" in result.delta.notes

# E) Currency mismatch (strict)
def test_currency_mismatch():
    sys = InstitutionalFxMtmResult(
        mtm=100.0,
        currency=ILS,
        spot_component=60.0,
        forward_points_component=30.0,
        discounting_component=10.0,
    )
    bank = BankFxForwardStatement(
        pair="USD/ILS",
        notional_base=1_000_000,
        value_date=None,
        maturity_date=None,
        presentation_currency="USD",
        mtm_total=100.0,
        leg=None,
    )
    with pytest.raises(ValueError, match="Currency mismatch"):
        reconcile_fx_forward(system=sys, bank=bank)
