import datetime
from dataclasses import FrozenInstanceError

import pytest

from core.pricing.fx.valuation_context import ValuationContext


def test_valuation_context_rejects_naive_datetime():
    with pytest.raises(ValueError, match="as_of_ts"):
        ValuationContext(
            as_of_ts=datetime.datetime(2026, 2, 22, 12, 0, 0),
            domestic_currency="ILS",
        )


def test_valuation_context_rejects_empty_currency():
    with pytest.raises(ValueError, match="domestic_currency"):
        ValuationContext(
            as_of_ts=datetime.datetime(2026, 2, 22, 12, 0, 0, tzinfo=datetime.timezone.utc),
            domestic_currency="   ",
        )


def test_valuation_context_is_frozen():
    ctx = ValuationContext(
        as_of_ts=datetime.datetime(2026, 2, 22, 12, 0, 0, tzinfo=datetime.timezone.utc),
        domestic_currency="ILS",
    )

    with pytest.raises(FrozenInstanceError):
        ctx.strict_mode = False


def test_valuation_context_equality_determinism():
    ts = datetime.datetime(2026, 2, 22, 12, 0, 0, tzinfo=datetime.timezone.utc)

    a = ValuationContext(as_of_ts=ts, domestic_currency="ILS", strict_mode=True)
    b = ValuationContext(as_of_ts=ts, domestic_currency="ILS", strict_mode=True)

    assert a == b
