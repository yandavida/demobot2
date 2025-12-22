from __future__ import annotations

from core.backtest.timeline import BacktestTimeline
from core.backtest.result import BacktestResult, BacktestStepResult
from core.pricing.engine import PricingEngine
from core.pricing.context import PricingContext
from core.pricing.types import PricingError


class BacktestEngine:
    @staticmethod
    def run_backtest(
        execution: object,
        timeline: BacktestTimeline,
        pricing_engine: PricingEngine,
        *,
        base_currency: str = "USD",
    ) -> BacktestResult:
        steps: list[BacktestStepResult] = []

        for tp in timeline.points:
            ctx = PricingContext(market=tp.snapshot, base_currency=base_currency)
            try:
                pr = pricing_engine.price_execution(execution, ctx)
            except Exception as exc:
                # Surface pricing errors (PricingError expected)
                if isinstance(exc, PricingError):
                    raise
                raise

            steps.append(BacktestStepResult(t=tp.t, price=pr))

        final = steps[-1].price if steps else None
        return BacktestResult(steps=tuple(steps), final_price=final)


__all__ = ["BacktestEngine"]
