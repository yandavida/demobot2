from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from core.portfolio.v2_aggregation import PortfolioTotalsV2
from core.portfolio.v2_models import PortfolioStateV2

@dataclass(frozen=True)
class ConstraintsBreachV2:
    rule: str
    message: str
    underlying: Optional[str] = None

@dataclass(frozen=True)
class ConstraintsReportV2:
    passed: bool
    breaches: List[ConstraintsBreachV2]

def empty_constraints_report() -> ConstraintsReportV2:
    return ConstraintsReportV2(passed=True, breaches=[])

def evaluate_constraints(state: PortfolioStateV2, totals: PortfolioTotalsV2) -> ConstraintsReportV2:
    breaches: List[ConstraintsBreachV2] = []
    c = state.constraints
    # max_notional
    if c.max_notional is not None:
        total_notional = sum(ex.abs_notional for _, ex in totals.exposures)
        if total_notional > c.max_notional:
            breaches.append(ConstraintsBreachV2(
                rule="max_notional",
                message=f"Total notional {total_notional} exceeds max {c.max_notional}",
            ))
    # max_abs_delta
    if c.max_abs_delta is not None:
        total_abs_delta = sum(abs(ex.delta) for _, ex in totals.exposures)
        if total_abs_delta > c.max_abs_delta:
            breaches.append(ConstraintsBreachV2(
                rule="max_abs_delta",
                message=f"Total abs(delta) {total_abs_delta} exceeds max {c.max_abs_delta}",
            ))
    # max_concentration_pct
    if c.max_concentration_pct is not None and totals.exposures:
        total_notional = sum(ex.abs_notional for _, ex in totals.exposures)
        for underlying, ex in totals.exposures:
            pct = 100.0 * ex.abs_notional / total_notional if total_notional else 0.0
            if pct > c.max_concentration_pct:
                breaches.append(ConstraintsBreachV2(
                    rule="max_concentration_pct",
                    message=f"Underlying {underlying} concentration {pct:.2f}% exceeds max {c.max_concentration_pct}",
                    underlying=underlying,
                ))
    breaches = sorted(breaches, key=lambda b: (b.rule, b.underlying or ""))
    return ConstraintsReportV2(passed=(not breaches), breaches=breaches)
