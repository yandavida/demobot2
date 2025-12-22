from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Sequence

from core.portfolio.portfolio_models import PortfolioState, CanonicalKey
from core.portfolio.wiring import PortfolioCandidate, build_portfolio_state_from_candidate
from core.pricing.engine import PricingEngine
from core.pricing.context import PricingContext
from core.pricing.types import PriceResult, PricingError
from core.market_data.types import MarketSnapshot
from core.backtest.timeline import BacktestTimeline
from core.portfolio.aggregators import validate_portfolio_economics_present
from core.portfolio.constraints import ConstraintSpec, evaluate_constraints, PortfolioConstraintError, ConstraintReport
from core.portfolio.portfolio_models import _key_sort_value


@dataclass(frozen=True)
class PositionValuation:
    key: CanonicalKey
    pv: float
    currency: str


@dataclass(frozen=True)
class PortfolioValuationStep:
    t: int | str
    valuations: Tuple[PositionValuation, ...]
    total_pv: float
    currency: str
    constraints: ConstraintReport
    missing_economics_count: int
    warnings: Tuple[str, ...]


@dataclass(frozen=True)
class PortfolioBacktestResult:
    steps: Tuple[PortfolioValuationStep, ...]
    final: PortfolioValuationStep | None = None


def valuate_positions(
    state: PortfolioState, pricing_engine: PricingEngine, context: PricingContext
) -> Tuple[PositionValuation, ...]:
    vals: list[PositionValuation] = []

    for p in state.positions:
        # Price per unit
        pr: PriceResult
        try:
            pr = pricing_engine.price_execution(p.execution, context)
        except Exception as exc:
            raise

        # Multiply per-unit PV by position.quantity
        pv = float(pr.pv) * float(p.quantity)

        # Ensure currency matches context.base_currency
        if pr.currency != context.base_currency:
            raise PricingError(f"currency mismatch for position {p.key}: {pr.currency} != {context.base_currency}")

        vals.append(PositionValuation(key=p.key, pv=pv, currency=pr.currency))

    # Ensure deterministic ordering by key
    vals.sort(key=lambda v: _key_sort_value(v.key))
    return tuple(vals)


def build_portfolio_valuation_step(
    t: int | str,
    state: PortfolioState,
    snapshot: MarketSnapshot,
    pricing_engine: PricingEngine,
    constraint_specs: Sequence[ConstraintSpec],
    *,
    base_currency: str = "USD",
    strict_constraints: bool = False,
) -> PortfolioValuationStep:
    context = PricingContext(market=snapshot, base_currency=base_currency)

    valuations = valuate_positions(state, pricing_engine, context)
    total_pv = sum(v.pv for v in valuations)

    _, missing = validate_portfolio_economics_present(state)

    # Evaluate constraints, catching strict-mode exception to extract report
    try:
        report = evaluate_constraints(state, constraint_specs, strict=bool(strict_constraints))
    except PortfolioConstraintError as exc:
        report = exc.report

    warnings: list[str] = []
    if missing > 0:
        warnings.append(f"missing_economics:{missing}")
    if not report.ok:
        warnings.append(f"constraint_violations:{report.violation_count}")
    warnings.sort()

    return PortfolioValuationStep(
        t=t,
        valuations=tuple(valuations),
        total_pv=float(total_pv),
        currency=base_currency,
        constraints=report,
        missing_economics_count=missing,
        warnings=tuple(warnings),
    )


def run_portfolio_backtest(
    candidate: PortfolioCandidate,
    timeline: BacktestTimeline,
    pricing_engine: PricingEngine,
    constraint_specs: Sequence[ConstraintSpec],
    *,
    base_currency: str = "USD",
    strict_constraints: bool = False,
) -> PortfolioBacktestResult:
    state = build_portfolio_state_from_candidate(candidate, base_currency=base_currency)

    steps: list[PortfolioValuationStep] = []
    for tp in timeline.points:
        step = build_portfolio_valuation_step(
            t=tp.t,
            state=state,
            snapshot=tp.snapshot,
            pricing_engine=pricing_engine,
            constraint_specs=constraint_specs,
            base_currency=base_currency,
            strict_constraints=strict_constraints,
        )
        steps.append(step)

    final = steps[-1] if steps else None
    return PortfolioBacktestResult(steps=tuple(steps), final=final)


__all__ = [
    "PositionValuation",
    "PortfolioValuationStep",
    "PortfolioBacktestResult",
    "valuate_positions",
    "build_portfolio_valuation_step",
    "run_portfolio_backtest",
]
