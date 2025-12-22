from __future__ import annotations

from core.market_data import PriceQuote, FxRateQuote, InMemoryMarketDataProvider, MissingQuoteError, MissingFxRateError


def test_get_price_and_missing():
    p = PriceQuote(asset="AAPL", price=150.0, currency="USD")
    prov = InMemoryMarketDataProvider(prices=[p])
    got = prov.get_price("AAPL")
    assert got.price == 150.0

    try:
        prov.get_price("MSFT")
        assert False, "expected MissingQuoteError"
    except MissingQuoteError:
        pass


def test_get_fx_and_missing():
    f = FxRateQuote(pair="USD/ILS", rate=3.5)
    prov = InMemoryMarketDataProvider(fx_rates=[f])
    got = prov.get_fx_rate("USD/ILS")
    assert got.rate == 3.5

    try:
        prov.get_fx_rate("EUR/USD")
        assert False, "expected MissingFxRateError"
    except MissingFxRateError:
        pass


def test_snapshot_deterministic_ordering():
    p1 = PriceQuote(asset="B", price=2.0, currency="USD")
    p2 = PriceQuote(asset="A", price=1.0, currency="USD")
    prov = InMemoryMarketDataProvider(prices=[p1, p2])
    snap = prov.snapshot()
    assets = tuple(q.asset for q in snap.quotes)
    assert assets == ("A", "B")


def test_with_updates_immutability():
    p = PriceQuote(asset="X", price=10.0, currency="USD")
    prov = InMemoryMarketDataProvider(prices=[p])
    new_p = PriceQuote(asset="Y", price=20.0, currency="USD")
    prov2 = prov.with_updates(prices=[new_p])
    assert prov.has_price("Y") is False
    assert prov2.has_price("Y") is True


def test_validation_rejects_non_positive():
    try:
        PriceQuote(asset="Z", price=0.0, currency="USD")
        assert False, "expected ValueError for price 0"
    except ValueError:
        pass

    try:
        FxRateQuote(pair="USD/ILS", rate=0.0)
        assert False, "expected ValueError for rate 0"
    except ValueError:
        pass
