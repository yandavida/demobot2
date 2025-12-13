"""Execution-time guardrails for arbitrage opportunities."""

from .defaults import default_execution_constraints
from .gate import evaluate_execution_readiness
from .models import ExecutionConstraints, ExecutionDecision
from .reasons import (
    EDGE_TOO_SMALL,
    INTERNAL_ERROR,
    LATENCY_TOO_HIGH,
    MISSING_QUOTES,
    NOTIONAL_TOO_LARGE,
    QTY_TOO_LARGE,
    QUOTE_TOO_OLD,
    SPREAD_TOO_WIDE,
    VENUE_NOT_ALLOWED,
)

__all__ = [
    "default_execution_constraints",
    "evaluate_execution_readiness",
    "ExecutionConstraints",
    "ExecutionDecision",
    "EDGE_TOO_SMALL",
    "SPREAD_TOO_WIDE",
    "QUOTE_TOO_OLD",
    "NOTIONAL_TOO_LARGE",
    "QTY_TOO_LARGE",
    "LATENCY_TOO_HIGH",
    "VENUE_NOT_ALLOWED",
    "MISSING_QUOTES",
    "INTERNAL_ERROR",
]
