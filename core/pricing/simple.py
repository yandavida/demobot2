from __future__ import annotations

from core.pricing.engine import PricingEngine
from core.pricing.context import PricingContext
from core.pricing.types import PriceResult, PricingError


class SimpleSpotPricingEngine(PricingEngine):
    """Naive spot pricing: pv = market_price * quantity (execution.size).

    Requirements on `execution`:
    - must have `symbol` attribute (asset id)
    - must have `size` attribute (quantity)
    """

    def price_execution(self, execution: object, context: PricingContext) -> PriceResult:
        sym = getattr(execution, "symbol", None)
        if sym is None:
            raise PricingError("execution has no symbol")

        # Pricing returns PV per ONE unit. Position layer will multiply by quantity.
        # find price in snapshot
        price: float | None = None
        currency = None
        for q in context.market.quotes:
            if q.asset == sym:
                price = q.price
                currency = q.currency
                break

        if price is None or currency is None:
            raise PricingError(f"missing market price for {sym}")

        pv_per_unit = float(price)
        breakdown = {"price": float(price)}
        return PriceResult(pv=pv_per_unit, currency=currency, breakdown=breakdown)


__all__ = ["SimpleSpotPricingEngine"]
