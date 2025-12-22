from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Tuple, Dict

from core.portfolio.portfolio_models import PortfolioState
from core.portfolio.aggregators import aggregate_portfolio


ConstraintKind = str


@dataclass(frozen=True)
class ConstraintSpec:
    name: str
    kind: ConstraintKind
    limits: Mapping[str, float]
    strict: bool = False


@dataclass(frozen=True)
class ConstraintViolation:
    name: str
    kind: str
    key: str
    limit: float
    actual: float
    message: str


@dataclass(frozen=True)
class ConstraintReport:
    ok: bool
    violations: Tuple[ConstraintViolation, ...]
    violation_count: int


class PortfolioConstraintError(ValueError):
    def __init__(self, report: ConstraintReport) -> None:
        super().__init__("Portfolio constraints violated in strict mode")
        self.report = report


def _as_dict(pairs: Tuple[Tuple[str, float], ...]) -> Dict[str, float]:
    return {str(k): float(v) for k, v in pairs}


def evaluate_constraints(
    state: PortfolioState,
    specs: Sequence[ConstraintSpec],
    *,
    strict: bool | None = None,
) -> ConstraintReport:
    # Deterministic processing: sort specs by (kind, name)
    specs_sorted = sorted(specs, key=lambda s: (s.kind, s.name))

    ag = aggregate_portfolio(state)

    violations: list[ConstraintViolation] = []

    # determine effective strict mode
    if strict is None:
        strict_mode = any(s.strict for s in specs_sorted)
    else:
        strict_mode = bool(strict)

    # helper dicts
    cash_usage = _as_dict(ag.cash_usage_by_currency)
    exposure_ccy = _as_dict(ag.exposure_by_currency)
    exposure_asset = _as_dict(ag.exposure_by_asset)

    for spec in specs_sorted:
        kind = spec.kind
        limits = spec.limits or {}

        if kind == "max_position_count":
            limit = float(limits.get("*", 0.0))
            actual = float(ag.position_count)
            if actual > limit:
                violations.append(
                    ConstraintViolation(
                        name=spec.name,
                        kind=kind,
                        key="*",
                        limit=limit,
                        actual=actual,
                        message=f"position_count {actual} > limit {limit}",
                    )
                )

        elif kind == "max_cash_usage_by_ccy":
            for k, lim in sorted(limits.items(), key=lambda kv: str(kv[0])):
                actual = abs(float(cash_usage.get(k, 0.0)))
                limit = float(lim)
                if actual > limit:
                    violations.append(
                        ConstraintViolation(
                            name=spec.name,
                            kind=kind,
                            key=str(k),
                            limit=limit,
                            actual=actual,
                            message=f"cash usage {actual} for {k} exceeds {limit}",
                        )
                    )

        elif kind == "max_gross_exposure_by_ccy":
            for k, lim in sorted(limits.items(), key=lambda kv: str(kv[0])):
                actual = abs(float(exposure_ccy.get(k, 0.0)))
                limit = float(lim)
                if actual > limit:
                    violations.append(
                        ConstraintViolation(
                            name=spec.name,
                            kind=kind,
                            key=str(k),
                            limit=limit,
                            actual=actual,
                            message=f"gross exposure {actual} for {k} exceeds {limit}",
                        )
                    )

        elif kind == "max_net_exposure_by_ccy":
            for k, lim in sorted(limits.items(), key=lambda kv: str(kv[0])):
                actual = float(exposure_ccy.get(k, 0.0))
                limit = float(lim)
                if actual < -limit or actual > limit:
                    violations.append(
                        ConstraintViolation(
                            name=spec.name,
                            kind=kind,
                            key=str(k),
                            limit=limit,
                            actual=actual,
                            message=f"net exposure {actual} for {k} outside [-{limit},{limit}]",
                        )
                    )

        elif kind == "max_exposure_by_asset":
            for k, lim in sorted(limits.items(), key=lambda kv: str(kv[0])):
                actual = abs(float(exposure_asset.get(k, 0.0)))
                limit = float(lim)
                if actual > limit:
                    violations.append(
                        ConstraintViolation(
                            name=spec.name,
                            kind=kind,
                            key=str(k),
                            limit=limit,
                            actual=actual,
                            message=f"exposure {actual} for asset {k} exceeds {limit}",
                        )
                    )

        else:
            # Unknown spec kind: ignore deterministically
            continue

    # Sort violations deterministically by (kind, name, key)
    violations_sorted = tuple(sorted(violations, key=lambda v: (v.kind, v.name, v.key)))

    report = ConstraintReport(ok=(len(violations_sorted) == 0), violations=violations_sorted, violation_count=len(violations_sorted))

    if strict_mode and report.violation_count > 0:
        raise PortfolioConstraintError(report)

    return report


__all__ = ["ConstraintSpec", "ConstraintViolation", "ConstraintReport", "evaluate_constraints", "PortfolioConstraintError"]
