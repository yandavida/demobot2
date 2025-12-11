from __future__ import annotations

import pytest

from core.services.portfolio_valuation import (
    PublicPosition,
    PublicValuationRequest,
    valuate_portfolio,
)


def test_public_valuation_defaults_to_ils() -> None:
    request = PublicValuationRequest(
        positions=[
            PublicPosition(symbol="AAA", quantity=2, price=10.0, currency="USD"),
            PublicPosition(symbol="BBB", quantity=1, price=50.0, currency="ILS"),
        ],
        fx_rates={"USD/ILS": 3.5, "ILS/USD": 1 / 3.5},
    )

    response = valuate_portfolio(request)

    assert response.currency == "ILS"
    assert response.total_value == pytest.approx(120.0)


def test_public_valuation_respects_usd_base_currency() -> None:
    request = PublicValuationRequest(
        positions=[
            PublicPosition(symbol="CCC", quantity=1, price=100.0, currency="ILS"),
            PublicPosition(symbol="DDD", quantity=2, price=5.0, currency="USD"),
        ],
        fx_rates={"USD/ILS": 3.5, "ILS/USD": 1 / 3.5},
        base_currency="USD",
    )

    response = valuate_portfolio(request)

    assert response.currency == "USD"
    assert response.total_value == pytest.approx(38.5714286)
