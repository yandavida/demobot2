from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Tuple, Mapping

from core.portfolio.portfolio_models import Position, PortfolioState, _key_sort_value
from core.portfolio.aggregators import aggregate_portfolio, validate_portfolio_economics_present, PortfolioAggregates
from core.portfolio.constraints import ConstraintSpec, evaluate_constraints, PortfolioConstraintError, ConstraintReport


@dataclass(frozen=True)
class PortfolioCandidate:
    positions: Tuple[Position, ...]
    name: str = "candidate"
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PortfolioEvaluationResult:
    state: PortfolioState
    aggregates: PortfolioAggregates
    constraints: ConstraintReport
    ok: bool
    missing_economics_count: int
    score: float | None = None
    warnings: Tuple[str, ...] = field(default_factory=tuple)


def _make_key_for_execution(execution: object) -> str:
    eid = getattr(execution, "opportunity_id", None)
    return str(eid) if eid is not None else str(execution)


def build_candidate_from_executions(
    executions: Sequence[object], *, quantity: float = 1.0, tags: frozenset[str] | None = None
) -> PortfolioCandidate:
    # Build deterministic (key, execution) pairs
    pairs: list[tuple[str, object]] = []
    for e in executions:
        k = _make_key_for_execution(e)
        pairs.append((k, e))

    # Sort deterministically by (key_sort_value, str(execution))
    pairs.sort(key=lambda ke: (_key_sort_value(ke[0]), str(ke[1])))

    # Deduplicate: keep first occurrence for each key
    seen: set[str] = set()
    unique_pairs: list[tuple[str, object]] = []
    for k, e in pairs:
        if k in seen:
            continue
        seen.add(k)
        unique_pairs.append((k, e))

    positions: list[Position] = []
    tag_val = tags or frozenset()
    from typing import cast
    from core.arbitrage.models import ArbitrageOpportunity
    for k, e in unique_pairs:
        execution_t = cast(ArbitrageOpportunity, e)
        pos = Position(key=k, execution=execution_t, quantity=float(quantity), tags=tag_val)
        positions.append(pos)

    # Ensure deterministic ordering by key
    positions.sort(key=lambda p: _key_sort_value(p.key))

    return PortfolioCandidate(positions=tuple(positions))


def build_portfolio_state_from_candidate(
    candidate: PortfolioCandidate,
    *,
    base_currency: str = "USD",
    revision: int = 0,
    metadata: Mapping[str, str] | None = None,
) -> PortfolioState:
    meta = dict(metadata) if metadata else None
    # Use with_positions with bump_revision=False to preserve revision as caller provided
    from typing import cast
    from core.contracts.money import Currency
    base_ccy = cast(Currency, base_currency)
    return PortfolioState.with_positions(
        list(candidate.positions), base_currency=base_ccy, bump_revision=False, revision=revision, metadata=meta
    )


def evaluate_portfolio_state(
    state: PortfolioState, specs: Sequence[ConstraintSpec], *, strict: bool = False
) -> PortfolioEvaluationResult:
    ag = aggregate_portfolio(state)
    _, missing = validate_portfolio_economics_present(state)

    # Evaluate constraints, catching strict-mode exception to extract report
    try:
        report = evaluate_constraints(state, specs, strict=bool(strict))
    except PortfolioConstraintError as exc:
        report = exc.report

    ok = bool(report.ok and missing == 0)

    warnings_list: list[str] = []
    if missing > 0:
        warnings_list.append(f"missing_economics:{missing}")
    if not report.ok:
        warnings_list.append(f"constraint_violations:{report.violation_count}")

    # Deterministic ordering of warnings
    warnings_list.sort()

    return PortfolioEvaluationResult(
        state=state,
        aggregates=ag,
        constraints=report,
        ok=ok,
        missing_economics_count=missing,
        score=None,
        warnings=tuple(warnings_list),
    )


def evaluate_candidate(
    candidate: PortfolioCandidate,
    specs: Sequence[ConstraintSpec],
    *,
    base_currency: str = "USD",
    strict: bool = False,
) -> PortfolioEvaluationResult:
    state = build_portfolio_state_from_candidate(candidate, base_currency=base_currency)
    return evaluate_portfolio_state(state, specs, strict=strict)


def evaluate_candidates(
    candidates: Sequence[PortfolioCandidate],
    specs: Sequence[ConstraintSpec],
    *,
    base_currency: str = "USD",
    strict: bool = False,
) -> tuple[PortfolioEvaluationResult, ...]:
    # Stable ordering: sort candidates by (name, position_count, first_key)
    def _first_key(c: PortfolioCandidate) -> str:
        return c.positions[0].key if c.positions else ""

    sorted_candidates = sorted(candidates, key=lambda c: (c.name, len(c.positions), _first_key(c)))

    results: list[PortfolioEvaluationResult] = []
    for c in sorted_candidates:
        res = evaluate_candidate(c, specs, base_currency=base_currency, strict=strict)
        results.append(res)

    return tuple(results)


__all__ = [
    "PortfolioCandidate",
    "PortfolioEvaluationResult",
    "build_candidate_from_executions",
    "build_portfolio_state_from_candidate",
    "evaluate_portfolio_state",
    "evaluate_candidate",
    "evaluate_candidates",
]
