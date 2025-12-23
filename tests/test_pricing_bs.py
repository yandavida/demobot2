from __future__ import annotations

import math

from core.pricing.bs import bs_price, bs_greeks, BlackScholesPricingEngine
from core.pricing.option_types import EuropeanOption
from core.market_data.types import MarketSnapshot, PriceQuote
from core.pricing.context import PricingContext
from core.pricing.types import PricingError


def test_call_put_parity_and_monotonicity():
    S = 100.0
    K = 95.0
    r = 0.01
    q = 0.0
    vol = 0.2
    t = 0.5

    C = bs_price("call", S, K, r, q, vol, t)
    P = bs_price("put", S, K, r, q, vol, t)
    lhs = C - P
    rhs = S * math.exp(-q * t) - K * math.exp(-r * t)
    assert abs(lhs - rhs) < 1e-8

    # monotonicity: call increases with spot
    C_low = bs_price("call", S - 1.0, K, r, q, vol, t)
    C_high = bs_price("call", S + 1.0, K, r, q, vol, t)
    assert C_high > C_low

    # put increases with strike
    P_low = bs_price("put", S, K - 1.0, r, q, vol, t)
    P_high = bs_price("put", S, K + 1.0, r, q, vol, t)
    assert P_high > P_low


def test_boundary_conditions_t0_and_vol0():
    S = 50.0
    K = 40.0
    # t=0 intrinsic
    c0 = bs_price("call", S, K, 0.01, 0.0, 0.2, 0.0)
    assert c0 == max(S - K, 0.0)

    # vol = 0 deterministic forward
    t = 1.0
    vol0 = 0.0
    c_det = bs_price("call", S, K, 0.01, 0.0, vol0, t)
    expected = max(S * math.exp(-0.0 * t) - K * math.exp(-0.01 * t), 0.0)
    assert abs(c_det - expected) < 1e-12


def test_greeks_sanity():
    S = 120.0
    K = 100.0
    r = 0.02
    q = 0.0
    vol = 0.25
    t = 0.75

    greeks = bs_greeks("call", S, K, r, q, vol, t)
    assert greeks["gamma"] >= 0.0
    assert greeks["vega"] >= 0.0
    assert -1.0 <= greeks["delta"] <= 1.0


def test_engine_prices_european_option():
    opt = EuropeanOption(underlying="ABC", option_type="call", strike=10.0, expiry_t=0.5, currency="USD", contract_multiplier=1.0, vol=0.3)

    snap = MarketSnapshot(quotes=(PriceQuote(asset="ABC", price=12.0, currency="USD"),), fx_rates=(), as_of="t")
    engine = BlackScholesPricingEngine()
    # Use real PricingContext (tests should use the contract)
    ctx = PricingContext(market=snap, vol_provider=None, fx_converter=None, base_currency="USD")
    res = engine.price_execution(opt, ctx)
    assert res.pv > 0.0


def test_engine_missing_spot_or_vol_raises():
    opt = EuropeanOption(underlying="NOPE", option_type="call", strike=10.0, expiry_t=0.5, currency="USD")
    engine = BlackScholesPricingEngine()
    ctx = PricingContext(market=MarketSnapshot(quotes=(), fx_rates=(), as_of=None), vol_provider=None, fx_converter=None, base_currency="USD")
    try:
        engine.price_execution(opt, ctx)
        assert False, "expected PricingError for missing vol or spot"
    except PricingError:
        pass
