from __future__ import annotations

import math

from core.pricing.bs import BlackScholesPricingEngine, bs_price
from core.pricing.option_types import EuropeanOption
from core.pricing.context import PricingContext
from core.market_data.types import MarketSnapshot, PriceQuote
from core.vol.inmemory import InMemoryVolProvider


def make_ctx(price: float, provider=None):
    snap = MarketSnapshot(quotes=(PriceQuote(asset="FOO", price=price, currency="USD"),))
    return PricingContext(market=snap, vol_provider=provider)


def test_bs_uses_provider_even_if_option_has_vol():
    opt = EuropeanOption(underlying="FOO", option_type="call", strike=100.0, expiry_t=0.5, vol=0.5, contract_multiplier=1.0)
    prov = InMemoryVolProvider({"FOO": 0.1})
    ctx = make_ctx(120.0, provider=prov)

    eng = BlackScholesPricingEngine()
    res = eng.price_execution(opt, ctx)

    # compute expected using vol from provider (0.1)
    expected = bs_price("call", 120.0, 100.0, 0.0, 0.0, 0.1, 0.5)
    assert math.isclose(res.pv, expected, rel_tol=1e-9)


def test_bs_falls_back_to_option_vol_when_no_provider():
    opt = EuropeanOption(underlying="FOO", option_type="put", strike=110.0, expiry_t=0.25, vol=0.2, contract_multiplier=1.0)
    ctx = make_ctx(100.0, provider=None)
    eng = BlackScholesPricingEngine()
    res = eng.price_execution(opt, ctx)
    expected = bs_price("put", 100.0, 110.0, 0.0, 0.0, 0.2, 0.25)
    assert math.isclose(res.pv, expected, rel_tol=1e-9)


def test_bs_missing_both_raises_pricing_error():
    opt = EuropeanOption(underlying="FOO", option_type="call", strike=100.0, expiry_t=1.0, vol=None)
    ctx = make_ctx(100.0, provider=None)
    eng = BlackScholesPricingEngine()
    try:
        eng.price_execution(opt, ctx)
        assert False, "expected PricingError"
    except Exception as e:
        from core.pricing.types import PricingError

        assert isinstance(e, PricingError)
