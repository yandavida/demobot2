from __future__ import annotations

from typing import Mapping

from pydantic import BaseModel, Field

from core.adapters.contracts import PricingAdapter
from core.adapters.market_data import InMemoryMarketDataAdapter
from core.adapters.pricing import PricingRouter
from core.fx.converter import FxConverter
from core.fx.provider import FxRateProvider
from core.portfolio.engine import PortfolioEngine
from core.portfolio.margin_engine import calculate_portfolio_margin
from core.portfolio.margin_models import MarginConfig, MarginResult
from core.portfolio.models import Currency, Money, Portfolio, Position
from core.portfolio.risk import PortfolioRiskSnapshot, aggregate_portfolio_risk
from core.portfolio.var_engine import calculate_parametric_var
from core.portfolio.var_models import VarConfig, VarResult


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
    margin_rate: float = Field(
        default=0.15,
        description="Portfolio margin rate applied to absolute PV (baseline).",
    )
    margin_minimum: float = Field(
        default=0.0,
        description="Minimum absolute margin requirement in base currency.",
    )
    var_horizon_days: int = Field(default=1, description="VaR horizon in days.")
    var_confidence: float = Field(
        default=0.99, description="Confidence level used for VaR (e.g. 0.99)."
    )
    var_daily_volatility: float = Field(
        default=0.02,
        description="Assumed daily volatility (fraction, e.g. 0.02 = 2%).",
    )


class PublicGreeks(BaseModel):
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


class PublicMargin(BaseModel):
    required: float
    currency: Currency
    rate: float
    minimum: float


class PublicVar(BaseModel):
    amount: float
    currency: Currency
    horizon_days: int
    confidence: float
    daily_volatility: float


class PublicPortfolioRisk(BaseModel):
    pv: float
    currency: Currency
    greeks: PublicGreeks
    margin: PublicMargin | None = None
    var: PublicVar | None = None


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

        return Money(amount=price * position.quantity, ccy=str(currency))


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

    margin_config = MarginConfig(
        rate=request.margin_rate,
        minimum=request.margin_minimum,
    )
    var_config = VarConfig(
        horizon_days=request.var_horizon_days,
        confidence=request.var_confidence,
        daily_volatility=request.var_daily_volatility,
    )

    margin_result = calculate_portfolio_margin(risk_snapshot, margin_config)
    var_result = calculate_parametric_var(risk_snapshot, var_config)

    portfolio_risk = _snapshot_to_public_risk(
        risk_snapshot,
        margin_result=margin_result,
        var_result=var_result,
    )

    return PublicValuationResponse(
        total_value=risk_snapshot.pv_base.amount,
        currency=risk_snapshot.pv_base.ccy,
        portfolio_risk=portfolio_risk,
        base_currency=request.base_currency,
        fx_rates=fx_rates,
    )


def _snapshot_to_public_risk(
    snapshot: PortfolioRiskSnapshot,
    *,
    margin_result: MarginResult,
    var_result: VarResult,
) -> PublicPortfolioRisk:
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
        margin=PublicMargin(
            required=margin_result.required.amount,
            currency=margin_result.required.ccy,
            rate=margin_result.rate,
            minimum=margin_result.minimum,
        ),
        var=PublicVar(
            amount=var_result.amount.amount,
            currency=var_result.amount.ccy,
            horizon_days=var_result.horizon_days,
            confidence=var_result.confidence,
            daily_volatility=var_result.daily_volatility,
        ),
    )
