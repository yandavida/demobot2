import math
import pytest
from core.pricing.institutional_fx.swaps_models import FxSwapTrade, SwapType
from core.pricing.institutional_fx.engine import InstitutionalFxPricingEngine
from core.pricing.institutional_fx.swaps_engine import InstitutionalFxSwapPricingEngine
from core.contracts.money import Currency

ILS: Currency = "ILS"
USD: Currency = "USD"

@pytest.fixture
def swap_engine():
    return InstitutionalFxSwapPricingEngine(InstitutionalFxPricingEngine())

@pytest.fixture
def forward_engine():
    return InstitutionalFxPricingEngine()

# T1: BUY_SELL sign semantics (USD/ILS, presentation="ILS")
def test_buy_sell_signs(forward_engine):
    swap_engine = InstitutionalFxSwapPricingEngine(forward_engine)
    trade = FxSwapTrade(
        pair="USD/ILS",
        base_notional=10_000_000,
        swap_type=SwapType.BUY_SELL,
        near_forward_rate=4.0,
        far_forward_rate=4.1,
        near_df_base=1.0,
        near_df_quote=1.0,
        near_df_mtm=1.0,
        far_df_base=1.0,
        far_df_quote=1.0,
        far_df_mtm=1.0,
        spot=4.0,
        presentation_currency=ILS,
    )
    result = swap_engine.price_swap(trade=trade)
    # חישוב ערכים צפויים
    F_near = trade.spot * (trade.near_df_base / trade.near_df_quote)
    F_far  = trade.spot * (trade.far_df_base  / trade.far_df_quote)
    expected_near_signed = -trade.base_notional
    expected_far_signed  = +trade.base_notional
    expected_near_mtm = expected_near_signed * (F_near - trade.near_forward_rate) * trade.near_df_mtm
    expected_far_mtm  = expected_far_signed  * (F_far  - trade.far_forward_rate)  * trade.far_df_mtm
    expected_total    = math.fsum([expected_near_mtm, expected_far_mtm])
    assert result.near_leg.mtm == expected_near_mtm
    assert result.far_leg.mtm  == expected_far_mtm
    assert result.mtm == expected_total

# T2: SELL_BUY sign semantics (USD/ILS, presentation="ILS")
def test_sell_buy_signs(forward_engine):
    swap_engine = InstitutionalFxSwapPricingEngine(forward_engine)
    trade = FxSwapTrade(
        pair="USD/ILS",
        base_notional=10_000_000,
        swap_type=SwapType.SELL_BUY,
        near_forward_rate=4.0,
        far_forward_rate=3.9,
        near_df_base=1.0,
        near_df_quote=1.0,
        near_df_mtm=1.0,
        far_df_base=1.0,
        far_df_quote=1.0,
        far_df_mtm=1.0,
        spot=4.0,
        presentation_currency=ILS,
    )
    result = swap_engine.price_swap(trade=trade)
    # חישוב ערכים צפויים
    F_near = trade.spot * (trade.near_df_base / trade.near_df_quote)
    F_far  = trade.spot * (trade.far_df_base  / trade.far_df_quote)
    expected_near_signed = +trade.base_notional
    expected_far_signed  = -trade.base_notional
    expected_near_mtm = expected_near_signed * (F_near - trade.near_forward_rate) * trade.near_df_mtm
    expected_far_mtm  = expected_far_signed  * (F_far  - trade.far_forward_rate)  * trade.far_df_mtm
    expected_total    = math.fsum([expected_near_mtm, expected_far_mtm])
    assert result.near_leg.mtm == expected_near_mtm
    assert result.far_leg.mtm  == expected_far_mtm
    assert result.mtm == expected_total

# T3: Additivity exact
def test_additivity(forward_engine):
    swap_engine = InstitutionalFxSwapPricingEngine(forward_engine)
    trade = FxSwapTrade(
        pair="USD/ILS",
        base_notional=10_000_000,
        swap_type=SwapType.BUY_SELL,
        near_forward_rate=4.0,
        far_forward_rate=4.1,
        near_df_base=0.95,
        near_df_quote=1.0,
        near_df_mtm=1.0,
        far_df_base=0.95,
        far_df_quote=1.0,
        far_df_mtm=1.0,
        spot=4.0,
        presentation_currency=ILS,
    )
    result = swap_engine.price_swap(trade=trade)
    total = math.fsum([result.near_leg.mtm, result.far_leg.mtm])
    assert total == result.mtm

# T4: Inception sanity
def test_inception_sanity(forward_engine):
    swap_engine = InstitutionalFxSwapPricingEngine(forward_engine)
    # F_market for near = spot * (df_base / df_quote) = 4.0 * (0.95/1.0) = 3.8
    # F_market for far = spot * (df_base / df_quote) = 4.0 * (0.95/1.0) = 3.8
    trade = FxSwapTrade(
        pair="USD/ILS",
        base_notional=10_000_000,
        swap_type=SwapType.BUY_SELL,
        near_forward_rate=3.8,
        far_forward_rate=3.8,
        near_df_base=0.95,
        near_df_quote=1.0,
        near_df_mtm=1.0,
        far_df_base=0.95,
        far_df_quote=1.0,
        far_df_mtm=1.0,
        spot=4.0,
        presentation_currency=ILS,
    )
    result = swap_engine.price_swap(trade=trade)
    assert result.near_leg.mtm == 0
    assert result.far_leg.mtm == 0
    assert result.mtm == 0

# T5: Component consistency per leg
def test_component_consistency(forward_engine):
    swap_engine = InstitutionalFxSwapPricingEngine(forward_engine)
    trade = FxSwapTrade(
        pair="USD/ILS",
        base_notional=10_000_000,
        swap_type=SwapType.BUY_SELL,
        near_forward_rate=4.0,
        far_forward_rate=4.1,
        near_df_base=0.95,
        near_df_quote=1.0,
        near_df_mtm=1.0,
        far_df_base=0.95,
        far_df_quote=1.0,
        far_df_mtm=1.0,
        spot=4.0,
        presentation_currency=ILS,
    )
    result = swap_engine.price_swap(trade=trade)
    for leg in [result.near_leg, result.far_leg]:
        total = math.fsum([
            leg.spot_component,
            leg.forward_points_component,
            leg.discounting_component,
        ])
        assert total == leg.mtm
