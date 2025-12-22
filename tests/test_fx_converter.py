from __future__ import annotations

from core.fx.converter import FxConverter
from core.market_data.types import FxRateQuote
from core.fx.errors import MissingFxRateError


def test_direct_conversion():
    f = FxRateQuote(pair="USD/ILS", rate=3.5)
    c = FxConverter(fx_rates=[f])
    assert c.convert(2.0, "USD", "ILS") == 7.0


def test_inverse_conversion():
    f = FxRateQuote(pair="USD/ILS", rate=4.0)
    c = FxConverter(fx_rates=[f])
    # convert ILS->USD should use inverse
    assert abs(c.convert(8.0, "ILS", "USD") - 2.0) < 1e-12


def test_same_currency():
    c = FxConverter()
    assert c.convert(5.0, "USD", "USD") == 5.0


def test_missing_rate_strict_and_nonstrict():
    c = FxConverter()
    try:
        c.convert(1.0, "USD", "EUR", strict=True)
        assert False, "expected MissingFxRateError"
    except MissingFxRateError:
        pass

    # non-strict returns amount unchanged
    assert c.convert(1.0, "USD", "EUR", strict=False) == 1.0


def test_input_order_independent():
    f1 = FxRateQuote(pair="USD/ILS", rate=3.5)
    f2 = FxRateQuote(pair="EUR/USD", rate=1.2)
    c1 = FxConverter(fx_rates=[f1, f2])
    c2 = FxConverter(fx_rates=[f2, f1])
    assert c1.convert(2.0, "USD", "ILS") == c2.convert(2.0, "USD", "ILS")
