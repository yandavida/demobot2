
import math
from core.pricing.institutional_fx.engine import InstitutionalFxPricingEngine
from core.contracts.money import Currency

engine = InstitutionalFxPricingEngine()


ILS: Currency = "ILS"
USD: Currency = "USD"

# T1: Zero MTM at inception
def test_zero_mtm_at_inception():
    notional = 1_000_000
    spot = 3.5
    df_base = 0.98
    df_quote = 0.97
    F_market = spot * (df_base / df_quote)
    contract_forward_rate = F_market
    df_mtm = 0.99
    res = engine.price_forward(
        notional=notional,
        spot=spot,
        contract_forward_rate=contract_forward_rate,
        df_base=df_base,
        df_quote=df_quote,
        df_mtm=df_mtm,
        presentation_currency=ILS,
    )
    assert res.mtm == 0.0
    assert res.currency == ILS

# T2: Directionality
def test_directionality_long_short():
    notional = 1_000_000
    spot = 3.5
    df_base = 0.98
    df_quote = 0.97
    df_mtm = 0.99
    # Long forward
    F_market = spot * (df_base / df_quote)
    contract_forward_rate = F_market - 0.05
    res_long = engine.price_forward(
        notional=notional,
        spot=spot,
        contract_forward_rate=contract_forward_rate,
        df_base=df_base,
        df_quote=df_quote,
        df_mtm=df_mtm,
        presentation_currency=ILS,
    )
    # Short forward
    res_short = engine.price_forward(
        notional=-notional,
        spot=spot,
        contract_forward_rate=contract_forward_rate,
        df_base=df_base,
        df_quote=df_quote,
        df_mtm=df_mtm,
        presentation_currency=ILS,
    )
    assert res_long.mtm > 0
    assert res_short.mtm < 0
    assert math.isclose(res_long.mtm, -res_short.mtm, rel_tol=1e-12)

# T3: Discounting sanity
def test_discounting_sanity():
    notional = 1_000_000
    spot = 3.5
    df_base = 0.98
    df_quote = 0.97
    contract_forward_rate = 3.6
    df_mtm_high = 0.99
    df_mtm_low = 0.95
    res_high = engine.price_forward(
        notional=notional,
        spot=spot,
        contract_forward_rate=contract_forward_rate,
        df_base=df_base,
        df_quote=df_quote,
        df_mtm=df_mtm_high,
        presentation_currency=ILS,
    )
    res_low = engine.price_forward(
        notional=notional,
        spot=spot,
        contract_forward_rate=contract_forward_rate,
        df_base=df_base,
        df_quote=df_quote,
        df_mtm=df_mtm_low,
        presentation_currency=ILS,
    )
    assert abs(res_high.mtm) > abs(res_low.mtm)

# T4: Exact reconciliation
def test_exact_reconciliation():
    notional = 1_000_000
    spot = 3.5
    df_base = 0.98
    df_quote = 0.97
    contract_forward_rate = 3.6
    df_mtm = 0.99
    F_market = spot * (df_base / df_quote)
    diff = F_market - contract_forward_rate
    mtm_expected = notional * diff * df_mtm
    res = engine.price_forward(
        notional=notional,
        spot=spot,
        contract_forward_rate=contract_forward_rate,
        df_base=df_base,
        df_quote=df_quote,
        df_mtm=df_mtm,
        presentation_currency=ILS,
    )
    assert res.mtm == mtm_expected

# T5: Component consistency
def test_component_consistency():
    notional = 1_000_000
    spot = 3.5
    df_base = 0.98
    df_quote = 0.97
    contract_forward_rate = 3.6
    df_mtm = 0.99
    res = engine.price_forward(
        notional=notional,
        spot=spot,
        contract_forward_rate=contract_forward_rate,
        df_base=df_base,
        df_quote=df_quote,
        df_mtm=df_mtm,
        presentation_currency=ILS,
    )
    total = math.fsum([
        res.spot_component,
        res.forward_points_component,
        res.discounting_component,
    ])
    assert math.isclose(total, res.mtm, rel_tol=1e-12)
