from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Literal, Sequence, Tuple

from core.arbitrage.models import ArbitrageOpportunity
from core.portfolio.models import Currency


ConstraintId = str
ViolationSeverity = Literal["HARD", "SOFT"]


@dataclass(frozen=True)
class ConstraintViolation:
    constraint_id: ConstraintId
    severity: ViolationSeverity
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FeasibilityContext:
    base_currency: Currency = "USD"
    max_slippage_bps: float | None = None
    max_spread_bps: float | None = None
    min_notional: float | None = None
    max_notional: float | None = None
    lot_size: float | None = None
    tick_size: float | None = None
    allowed_venues: set[str] | None = None
    now_ts: datetime | None = None


@dataclass(frozen=True)
class OptionFeasibility:
    option: ArbitrageOpportunity
    passed: bool
    violations: Tuple[ConstraintViolation, ...]


@dataclass(frozen=True)
class FeasibilityReport:
    options: Tuple[OptionFeasibility, ...]

    def passed_options(self) -> Tuple[OptionFeasibility, ...]:
        return tuple(o for o in self.options if o.passed)

    def failed_options(self) -> Tuple[OptionFeasibility, ...]:
        return tuple(o for o in self.options if not o.passed)


# Ordering helper: HARD before SOFT
_SEVERITY_ORDER = {"HARD": 0, "SOFT": 1}


def _sort_violations(violations: Iterable[ConstraintViolation]) -> Tuple[ConstraintViolation, ...]:
    return tuple(
        sorted(
            violations,
            key=lambda v: (_SEVERITY_ORDER.get(v.severity, 9), v.constraint_id, v.code, v.message),
        )
    )


def _check_venue_allowed(option: ArbitrageOpportunity, ctx: FeasibilityContext) -> list[ConstraintViolation]:
    violations: list[ConstraintViolation] = []
    allowed = ctx.allowed_venues
    if allowed is not None:
        if option.buy.venue not in allowed:
            violations.append(
                ConstraintViolation(
                    constraint_id="VENUE_ALLOWED",
                    severity="HARD",
                    code="BUY_VENUE_NOT_ALLOWED",
                    message=f"Buy venue {option.buy.venue} not in allowed set",
                    details={"venue": option.buy.venue},
                )
            )
        if option.sell.venue not in allowed:
            violations.append(
                ConstraintViolation(
                    constraint_id="VENUE_ALLOWED",
                    severity="HARD",
                    code="SELL_VENUE_NOT_ALLOWED",
                    message=f"Sell venue {option.sell.venue} not in allowed set",
                    details={"venue": option.sell.venue},
                )
            )
    return violations


def _compute_notional(option: ArbitrageOpportunity) -> float | None:
    try:
        # Prefer buy leg notional
        return float(option.buy.price * option.size)
    except Exception:
        return None


def _check_notional_bounds(option: ArbitrageOpportunity, ctx: FeasibilityContext) -> list[ConstraintViolation]:
    violations: list[ConstraintViolation] = []
    notional = _compute_notional(option)
    if notional is None:
        violations.append(
            ConstraintViolation(
                constraint_id="NOTIONAL",
                severity="HARD",
                code="MISSING_NOTIONAL",
                message="Unable to compute notional for option",
            )
        )
        return violations

    if ctx.min_notional is not None and notional < ctx.min_notional:
        violations.append(
            ConstraintViolation(
                constraint_id="NOTIONAL",
                severity="HARD",
                code="NOTIONAL_TOO_SMALL",
                message=f"Notional {notional} below min {ctx.min_notional}",
                details={"notional": notional},
            )
        )

    if ctx.max_notional is not None and notional > ctx.max_notional:
        violations.append(
            ConstraintViolation(
                constraint_id="NOTIONAL",
                severity="HARD",
                code="NOTIONAL_TOO_LARGE",
                message=f"Notional {notional} above max {ctx.max_notional}",
                details={"notional": notional},
            )
        )

    return violations


def _check_lot_tick_sanity(option: ArbitrageOpportunity, ctx: FeasibilityContext) -> list[ConstraintViolation]:
    violations: list[ConstraintViolation] = []
    if ctx.lot_size is not None:
        # quantity should be a multiple of lot_size within small epsilon
        qty = option.size
        mod = qty % ctx.lot_size
        eps = 1e-9
        if not (mod <= eps or abs(mod - ctx.lot_size) <= eps):
            violations.append(
                ConstraintViolation(
                    constraint_id="LOT_TICK",
                    severity="SOFT",
                    code="LOT_SIZE_MISMATCH",
                    message=f"Quantity {qty} not multiple of lot_size {ctx.lot_size}",
                    details={"quantity": qty, "lot_size": ctx.lot_size},
                )
            )

    if ctx.tick_size is not None:
        # price should align to tick size for buy price
        price = option.buy.price
        modp = (price / ctx.tick_size) % 1
        eps = 1e-9
        if not (modp <= eps or abs(modp - 1) <= eps):
            violations.append(
                ConstraintViolation(
                    constraint_id="LOT_TICK",
                    severity="SOFT",
                    code="TICK_SIZE_MISMATCH",
                    message=f"Price {price} not aligned to tick_size {ctx.tick_size}",
                    details={"price": price, "tick_size": ctx.tick_size},
                )
            )

    return violations


def _check_spread_slippage_caps(option: ArbitrageOpportunity, ctx: FeasibilityContext) -> list[ConstraintViolation]:
    violations: list[ConstraintViolation] = []

    # spread available from option.edge_bps
    spread = float(option.edge_bps or 0.0)
    if ctx.max_spread_bps is not None and spread > ctx.max_spread_bps:
        violations.append(
            ConstraintViolation(
                constraint_id="SPREAD",
                severity="SOFT",
                code="SPREAD_EXCEEDS_MAX",
                message=f"Spread {spread} bps exceeds max {ctx.max_spread_bps}",
                details={"spread_bps": spread},
            )
        )

    # slippage isn't available; treat as soft missing liquidity metric
    if ctx.max_slippage_bps is not None:
        # we don't have slippage metrics in option; report soft missing
        violations.append(
            ConstraintViolation(
                constraint_id="SLIPPAGE",
                severity="SOFT",
                code="MISSING_SLIPPAGE_METRICS",
                message="No slippage metrics available for option",
            )
        )

    return violations


def _check_time_window(option: ArbitrageOpportunity, ctx: FeasibilityContext) -> list[ConstraintViolation]:
    violations: list[ConstraintViolation] = []
    if ctx.now_ts is None:
        # cannot check time; soft violation
        violations.append(
            ConstraintViolation(
                constraint_id="TIME",
                severity="SOFT",
                code="MISSING_NOW",
                message="No reference time provided to context",
            )
        )
        return violations

    if option.as_of is None:
        violations.append(
            ConstraintViolation(
                constraint_id="TIME",
                severity="SOFT",
                code="MISSING_OPTION_TIMESTAMP",
                message="Option missing provenance timestamp",
            )
        )
        return violations

    # if option is older than 5 seconds consider soft stale
    age = ctx.now_ts - option.as_of
    if age > timedelta(seconds=5):
        violations.append(
            ConstraintViolation(
                constraint_id="TIME",
                severity="SOFT",
                code="STALE_OPTION",
                message=f"Option age {age.total_seconds()}s exceeds threshold",
                details={"age_s": age.total_seconds()},
            )
        )

    return violations


def evaluate_feasibility(
    options: Sequence[ArbitrageOpportunity], ctx: FeasibilityContext, *, strict: bool
) -> FeasibilityReport:
    """Evaluate all provided options and return a deterministic FeasibilityReport.

    Determinism guarantees:
    - options are returned in the same order as input
    - violations for each option are sorted by severity and identifiers
    """
    results: list[OptionFeasibility] = []

    for opt in options:
        violations: list[ConstraintViolation] = []
        violations.extend(_check_venue_allowed(opt, ctx))
        violations.extend(_check_notional_bounds(opt, ctx))
        violations.extend(_check_lot_tick_sanity(opt, ctx))
        violations.extend(_check_spread_slippage_caps(opt, ctx))
        violations.extend(_check_time_window(opt, ctx))

        sorted_violations = _sort_violations(violations)

        # Determine pass/fail
        has_hard = any(v.severity == "HARD" for v in sorted_violations)
        has_soft = any(v.severity == "SOFT" for v in sorted_violations)

        passed = not has_hard and not (strict and has_soft)

        results.append(OptionFeasibility(option=opt, passed=passed, violations=sorted_violations))

    return FeasibilityReport(options=tuple(results))


__all__ = [
    "ConstraintViolation",
    "FeasibilityContext",
    "OptionFeasibility",
    "FeasibilityReport",
    "evaluate_feasibility",
]
