from core.finance.market import MarketSnapshot as Shim, PriceQuote as ShimPQ, FxRateQuote as ShimFx
from core.market_data.types import MarketSnapshot as Canon, PriceQuote as CanonPQ, FxRateQuote as CanonFx

def test_market_snapshot_shim_is_canonical():
    assert Shim is Canon
    assert ShimPQ is CanonPQ
    assert ShimFx is CanonFx
