from __future__ import annotations

from core.backtest.timeline import BacktestTimeline, TimePoint
from core.backtest.result import BacktestResult, BacktestStepResult
from core.pricing.engine import PricingEngine
from core.pricing.context import PricingContext
from core.pricing.types import PricingError



class BacktestEngine:
    def _run_step(
        self,
        tp: TimePoint,
        execution: object,
        pricing_engine: PricingEngine,
        base_currency: str = "USD",
    ) -> BacktestStepResult:
        """
        Canonical order (F6.1):
        1) resolve context
        2) compute pricing
        3) build step result (pure)
        """
        from typing import cast
        from core.contracts.money import Currency
        # (1) resolve context
        base_ccy = cast(Currency, base_currency)
        ctx = PricingContext(market=tp.snapshot, base_currency=base_ccy)
        # (2) compute pricing/result
        try:
            pr = pricing_engine.price_execution(execution, ctx)
        except Exception as exc:
            if isinstance(exc, PricingError):
                raise
            raise
        # (3) build step result
        return BacktestStepResult(t=tp.t, price=pr)

    @staticmethod
    def run_backtest(
        execution: object,
        timeline: BacktestTimeline,
        pricing_engine: PricingEngine,
        *,
        base_currency: str = "USD",
    ) -> BacktestResult:
        steps: list[BacktestStepResult] = []
        engine = BacktestEngine()
        for tp in timeline.points:
            steps.append(engine._run_step(tp, execution, pricing_engine, base_currency=base_currency))
        final = steps[-1].price if steps else None
        return BacktestResult(steps=tuple(steps), final_price=final)


__all__ = ["BacktestEngine"]
