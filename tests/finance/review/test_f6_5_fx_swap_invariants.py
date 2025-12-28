import math
import pytest
from core.pricing.institutional_fx.swaps_models import FxSwapTrade, SwapType
from core.pricing.institutional_fx.engine import InstitutionalFxPricingEngine
from core.pricing.institutional_fx.swaps_engine import InstitutionalFxSwapPricingEngine
from core.contracts.money import Currency

ILS: Currency = "ILS"

@pytest.fixture
def forward_engine():
    return InstitutionalFxPricingEngine()

@pytest.fixture
def swap_engine(forward_engine):
    return InstitutionalFxSwapPricingEngine(forward_engine)

# INV1 — Additivity (Exact)
def test_additivity_exact(swap_engine):
    trade = FxSwapTrade(
        pair="USD/ILS",
        base_notional=10_000_000,
        swap_type=SwapType.BUY_SELL,
        near_forward_rate=4.0,
        far_forward_rate=4.125,
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
    total = math.fsum([result.near_leg.mtm, result.far_leg.mtm])
    assert result.mtm == total

# INV2 — Zero-MTM at Par (Exact)
@pytest.mark.parametrize("swap_type", [SwapType.BUY_SELL, SwapType.SELL_BUY])
def test_zero_mtm_at_par(swap_engine, swap_type):
    trade = FxSwapTrade(
        pair="USD/ILS",
        base_notional=10_000_000,
        swap_type=swap_type,
        near_forward_rate=4.0,
        far_forward_rate=4.0,
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
    assert result.near_leg.mtm == 0.0
    assert result.far_leg.mtm == 0.0
    assert result.mtm == 0.0

# INV3 — SwapType symmetry (Exact when K equal to F_market)
def test_swaptype_symmetry(swap_engine):
    for swap_type in [SwapType.BUY_SELL, SwapType.SELL_BUY]:
        trade = FxSwapTrade(
            pair="USD/ILS",
            base_notional=10_000_000,
            swap_type=swap_type,
            near_forward_rate=4.0,
            far_forward_rate=4.0,
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
        assert result.mtm == 0.0
        assert result.near_leg.mtm == 0.0
        assert result.far_leg.mtm == 0.0

# INV4 — Notional linearity
def test_notional_linearity(swap_engine):
    base = 10_000_000
    trade1 = FxSwapTrade(
        pair="USD/ILS",
        base_notional=base,
        swap_type=SwapType.BUY_SELL,
        near_forward_rate=4.0,
        far_forward_rate=4.125,
        near_df_base=1.0,
        near_df_quote=1.0,
        near_df_mtm=1.0,
        far_df_base=1.0,
        far_df_quote=1.0,
        far_df_mtm=1.0,
        spot=4.0,
        presentation_currency=ILS,
    )
    trade2 = FxSwapTrade(
        pair="USD/ILS",
        base_notional=2*base,
        swap_type=SwapType.BUY_SELL,
        near_forward_rate=4.0,
        far_forward_rate=4.125,
        near_df_base=1.0,
        near_df_quote=1.0,
        near_df_mtm=1.0,
        far_df_base=1.0,
        far_df_quote=1.0,
        far_df_mtm=1.0,
        spot=4.0,
        presentation_currency=ILS,
    )
    result1 = swap_engine.price_swap(trade=trade1)
    result2 = swap_engine.price_swap(trade=trade2)
    assert result2.mtm == 2 * result1.mtm
    assert result2.near_leg.mtm == 2 * result1.near_leg.mtm
    assert result2.far_leg.mtm == 2 * result1.far_leg.mtm
