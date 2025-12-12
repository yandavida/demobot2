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
    assert response.portfolio_risk is not None
    assert response.portfolio_risk.pv == pytest.approx(120.0)
    assert response.portfolio_risk.currency == "ILS"
    assert response.portfolio_risk.greeks.delta == 0.0
    assert response.portfolio_risk.margin is not None
    assert response.portfolio_risk.margin.required == pytest.approx(18.0)
    assert response.portfolio_risk.margin.currency == "ILS"
    assert response.portfolio_risk.var is not None
    assert response.portfolio_risk.var.amount == pytest.approx(5.592)
    assert response.portfolio_risk.var.currency == "ILS"


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
    assert response.portfolio_risk is not None
    assert response.portfolio_risk.pv == pytest.approx(38.5714286)
    assert response.portfolio_risk.currency == "USD"
    assert response.portfolio_risk.margin is not None
    assert response.portfolio_risk.margin.required == pytest.approx(5.78571429)
    assert response.portfolio_risk.margin.currency == "USD"
    assert response.portfolio_risk.var is not None
    assert response.portfolio_risk.var is not None
    expected_var_usd = 38.5714286 * 0.0466
    assert response.portfolio_risk.var.amount == pytest.approx(expected_var_usd)

