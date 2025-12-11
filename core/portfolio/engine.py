from __future__ import annotations

from typing import Iterable

from core.adapters.contracts import MarketDataAdapter
from core.adapters.pricing import PricingRouter
from core.fx.converter import FxConverter
from core.portfolio.cache import CacheKey, InMemoryCache
from core.portfolio.models import Money, Portfolio



class PortfolioEngine:
    def __init__(
        self,
        market_data: MarketDataAdapter,
        pricing_router: PricingRouter,
        fx_converter: FxConverter,
        cache: InMemoryCache[CacheKey, Money] | None = None,
    ) -> None:
        self.market_data = market_data
        self.pricing_router = pricing_router
        self.fx = fx_converter
        self.cache = cache or InMemoryCache()

    def evaluate_portfolio(self, portfolio: Portfolio) -> Money:
        symbols: Iterable[str] = [position.symbol for position in portfolio.positions]
        market = self.market_data.get_snapshot(symbols=symbols)
        total_value = 0.0

        for position in portfolio.positions:
            price = self.pricing_router.price(position, market, fx_converter=self.fx)
            price_base = self.fx.to_base(price)
            total_value += price_base.amount

        return Money(amount=total_value, ccy=self.fx.base_ccy)

    def build_pl_surface(self, portfolio: Portfolio) -> dict:
        # TODO: implement P&L surface construction leveraging scenario pricing
        return {}

    def compute_margin(self, portfolio: Portfolio) -> float:
        # TODO: integrate with risk engines and margin methodologies
        return 0.0
