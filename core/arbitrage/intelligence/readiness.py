from __future__ import annotations

from dataclasses import dataclass

from core.arbitrage.models import ArbitrageConfig


@dataclass(frozen=True)
class ExecutionConstraints:
    """Lightweight thresholds for deciding whether an item is executable."""

    min_edge_bps: float = 0.0
    min_size: float = 0.0


@dataclass(frozen=True)
class ExecutionReadiness:
    ready: bool
    reasons: list[str]
    constraints: ExecutionConstraints

    def to_dict(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "reasons": list(self.reasons),
            "constraints": {
                "min_edge_bps": self.constraints.min_edge_bps,
                "min_size": self.constraints.min_size,
            },
        }


def default_execution_constraints(config: ArbitrageConfig | None = None) -> ExecutionConstraints:
    if config:
        return ExecutionConstraints(
            min_edge_bps=config.min_edge_bps,
            min_size=config.min_size,
        )
    return ExecutionConstraints()


def evaluate_execution_readiness(
    *,
    edge_bps: float,
    size: float,
    constraints: ExecutionConstraints | None = None,
) -> ExecutionReadiness:
    constraints = constraints or ExecutionConstraints()
    reasons: list[str] = []

    if edge_bps < constraints.min_edge_bps:
        reasons.append("edge_below_threshold")
    if size < constraints.min_size:
        reasons.append("size_below_threshold")

    ready = len(reasons) == 0
    return ExecutionReadiness(ready=ready, reasons=reasons, constraints=constraints)


__all__ = [
    "ExecutionConstraints",
    "ExecutionReadiness",
    "default_execution_constraints",
    "evaluate_execution_readiness",
]
