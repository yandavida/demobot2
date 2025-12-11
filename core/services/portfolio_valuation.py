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
from core.portfolio.risk import PortfolioRiskSnapshot, aggregate_portfolio_risk


class PublicPosition(BaseModel):
    symbol: str
    quantity: float
    price: float
    currency: Currency = Field(default="USD", description="Currency of the quoted price")
    instrument_type: str = Field(default="equity", description="Instrument type for routing")


class PublicValuationRequest(BaseModel):
    positions: list[PublicPosition]
    fx_rates: Mapping[str, float] = Field(
        default_factory=dict,
        description="Optional FX rates mapping; required when converting across currencies",
    )
    base_currency: Currency = Field(
        default="ILS",
        description="Base currency for aggregation; defaults to ILS for backward compatibility",
    )


class PublicGreeks(BaseModel):
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


class PublicPortfolioRisk(BaseModel):
    pv: float
    currency: Currency
    greeks: PublicGreeks


class PublicValuationResponse(BaseModel):
    total_value: float
    currency: Currency
    portfolio_risk: PublicPortfolioRisk | None = None
    base_currency: Currency | None = Field(
        default=None,
        description="Echoed base currency used for aggregation (if provided)",
    )
    fx_rates: Mapping[str, float] | None = Field(
        default=None,
        description="FX rates applied during valuation (if provided)",
    )


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

    fx_rates = request.fx_rates or {}
    fx_provider = FxRateProvider(rates=fx_rates)
    fx_converter = FxConverter(provider=fx_provider, base_ccy=request.base_currency)

    engine = PortfolioEngine(
        market_data=market_adapter,
        pricing_router=pricing_router,
        fx_converter=fx_converter,
    )

    portfolio = Portfolio(positions=portfolio_positions, base_currency=request.base_currency)
    risk_snapshot = aggregate_portfolio_risk(portfolio=portfolio, engine=engine)

    portfolio_risk = _snapshot_to_public_risk(risk_snapshot)

    return PublicValuationResponse(
        total_value=risk_snapshot.pv_base.amount,
        currency=risk_snapshot.pv_base.ccy,
        portfolio_risk=portfolio_risk,
        base_currency=request.base_currency,
        fx_rates=fx_rates,
    )


def _snapshot_to_public_risk(snapshot: PortfolioRiskSnapshot) -> PublicPortfolioRisk:
    return PublicPortfolioRisk(
        pv=snapshot.pv_base.amount,
        currency=snapshot.pv_base.ccy,
        greeks=PublicGreeks(
            delta=snapshot.greeks.delta,
            gamma=snapshot.greeks.gamma,
            vega=snapshot.greeks.vega,
            theta=snapshot.greeks.theta,
            rho=snapshot.greeks.rho,
        ),
    )
