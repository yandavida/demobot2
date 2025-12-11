from __future__ import annotations

from typing import Mapping

from pydantic import BaseModel, Field

from core.adapters.contracts import PricingAdapter
from core.adapters.market_data import InMemoryMarketDataAdapter
from core.adapters.pricing import PricingRouter
from core.fx.converter import FxConverter
from core.fx.provider import FxRateProvider
from core.portfolio.engine import PortfolioEngine
from core.portfolio.models import Currency, Money, Portfolio, Position


class PublicPosition(BaseModel):
    symbol: str
    quantity: float
    price: float
    currency: Currency = Field(default="USD", description="Currency of the quoted price")
    instrument_type: str = Field(default="equity", description="Instrument type for routing")


class PublicValuationRequest(BaseModel):
    positions: list[PublicPosition]
    fx_rates: Mapping[str, float]
    base_currency: Currency = Field(
        default="ILS",
        description="Base currency for aggregation; defaults to ILS for backward compatibility",
    )


class PublicValuationResponse(BaseModel):
    total_value: float
    currency: Currency


class _StaticPricingAdapter(PricingAdapter):
    """Pricing adapter that multiplies market price by quantity and respects position currency."""

    def price(self, position: Position, market, fx_converter: FxConverter | None = None) -> Money:
        price = market.get_price(position.symbol)
        if price is None:
            raise ValueError(f"Missing market price for {position.symbol}")

        currency = position.metadata.get("currency")
        if currency is None:
            raise ValueError(f"Missing currency metadata for {position.symbol}")

        return Money(amount=price * position.quantity, ccy=currency)


def valuate_portfolio(request: PublicValuationRequest) -> PublicValuationResponse:
    """Evaluate a public-facing portfolio valuation request."""

    portfolio_positions = [
        Position(
            symbol=p.symbol,
            quantity=p.quantity,
            instrument_type=p.instrument_type,
            metadata={"currency": p.currency},
        )
        for p in request.positions
    ]

    market_adapter = InMemoryMarketDataAdapter(
        prices={p.symbol: p.price for p in request.positions}
    )

    pricing_router = PricingRouter(default_adapter=_StaticPricingAdapter())

    fx_provider = FxRateProvider(rates=request.fx_rates)
    fx_converter = FxConverter(provider=fx_provider, base_ccy=request.base_currency)

    engine = PortfolioEngine(
        market_data=market_adapter,
        pricing_router=pricing_router,
        fx_converter=fx_converter,
    )

    portfolio = Portfolio(positions=portfolio_positions, base_currency=request.base_currency)
    total = engine.evaluate_portfolio(portfolio)

    return PublicValuationResponse(total_value=total.amount, currency=total.ccy)
