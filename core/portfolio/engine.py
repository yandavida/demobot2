from __future__ import annotations

from typing import Iterable

from core.adapters.contracts import MarketDataAdapter
from core.adapters.pricing import PricingRouter
from core.fx.contracts import FxConverter
from core.portfolio.cache import CacheKey, InMemoryCache
from core.portfolio.models import Money, Portfolio, Position


class PortfolioEngine:
    def __init__(
        self,
        market_data: MarketDataAdapter,
        pricing_router: PricingRouter,
        fx_converter: FxConverter | None = None,
        cache: InMemoryCache[CacheKey, Money] | None = None,
    ) -> None:
        self.market_data = market_data
        self.pricing_router = pricing_router
        self.fx_converter = fx_converter
        self.cache = cache or InMemoryCache()

    def evaluate_portfolio(self, portfolio: Portfolio) -> Money:
        symbols: Iterable[str] = [position.symbol for position in portfolio.positions]
        market = self.market_data.get_snapshot(symbols=symbols)
        currency = portfolio.base_currency
        total_value = 0.0

        for position in portfolio.positions:
            price = self.pricing_router.price(position, market, fx_converter=self.fx_converter)
            if price.ccy != currency and self.fx_converter is not None:
                price = self.fx_converter.convert(price, target_currency=currency)
            total_value += price.amount

        return Money(amount=total_value, ccy=currency)

    def build_pl_surface(self, portfolio: Portfolio) -> dict:
        # TODO: implement P&L surface construction leveraging scenario pricing
        return {}

    def compute_margin(self, portfolio: Portfolio) -> float:
        # TODO: integrate with risk engines and margin methodologies
        return 0.0
