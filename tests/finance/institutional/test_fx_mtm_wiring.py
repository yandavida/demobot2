import pytest
from core.pricing.mtm_method import FxMtmMethod
from core.pricing.fx_mtm import compute_fx_forward_mtm
from core.pricing.institutional_fx.engine import InstitutionalFxPricingEngine
from core.contracts.money import Currency

ILS: Currency = "ILS"

@pytest.fixture
def engine():
    return InstitutionalFxPricingEngine()

# T1: default behavior (explicit): method=INSTITUTIONAL עם engine -> מחזיר בדיוק mtm של engine.
def test_institutional_explicit(engine):
    mtm = compute_fx_forward_mtm(
        method=FxMtmMethod.INSTITUTIONAL,
        notional=1_000_000,
        spot=3.5,
        contract_forward_rate=3.6,
        df_base=0.98,
        df_quote=0.97,
        df_mtm=0.99,
        presentation_currency=ILS,
        institutional_engine=engine,
    )
    expected = engine.price_forward(
        notional=1_000_000,
        spot=3.5,
        contract_forward_rate=3.6,
        df_base=0.98,
        df_quote=0.97,
        df_mtm=0.99,
        presentation_currency=ILS,
    ).mtm
    assert mtm == expected

# T2: INSTITUTIONAL בלי engine -> ValueError
def test_institutional_no_engine():
    with pytest.raises(ValueError, match="institutional_engine must be provided"):
        compute_fx_forward_mtm(
            method=FxMtmMethod.INSTITUTIONAL,
            notional=1_000_000,
            spot=3.5,
            contract_forward_rate=3.6,
            df_base=0.98,
            df_quote=0.97,
            df_mtm=0.99,
            presentation_currency=ILS,
        )

# T3: THEORETICAL path -> NotImplementedError
def test_theoretical_path():
    with pytest.raises(NotImplementedError, match="THEORETICAL forward MTM is computed in F6.2; wiring for forward MTM is INSTITUTIONAL-only for now."):
        compute_fx_forward_mtm(
            method=FxMtmMethod.THEORETICAL,
            notional=1_000_000,
            spot=3.5,
            contract_forward_rate=3.6,
            df_base=0.98,
            df_quote=0.97,
            df_mtm=0.99,
            presentation_currency=ILS,
        )
