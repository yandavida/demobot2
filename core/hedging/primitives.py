"""Minimal hedging primitives (closed-form, algebraic).

This module implements the smallest, deterministic delta-hedge primitive
needed by Gate F5.2. The function performs algebra only on provided
delta exposures and does not perform any repricing or access external state.

Constraints:
- Deterministic (no randomness, time, or environment)
- No changes to numeric policy or tolerances
- Clear deterministic error when hedge instrument delta is zero
"""
from __future__ import annotations

from typing import Tuple
import math

from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass


def delta_hedge(delta_portfolio: float, delta_hedge_instrument: float) -> Tuple[float, float]:
    """Compute closed-form delta hedge quantity and residual.

    q = - delta_portfolio / delta_hedge_instrument

    Args:
        delta_portfolio: portfolio delta exposure (signed)
        delta_hedge_instrument: delta of single hedge instrument (non-zero)

    Returns:
        Tuple[q, residual_delta]

    Raises:
        ZeroDivisionError: when `delta_hedge_instrument == 0` (deterministic error)
    """
    if delta_hedge_instrument == 0.0:
        raise ZeroDivisionError("delta_hedge_instrument is zero: deterministic hedge impossible")

    if delta_portfolio == 0.0:
        return 0.0, 0.0

    q = -delta_portfolio / delta_hedge_instrument
    residual = delta_portfolio + q * delta_hedge_instrument
    return q, residual


__all__ = ["delta_hedge"]


def multi_delta_hedge(delta_portfolio: float, deltas: list[float]) -> tuple[list[float], float]:
    """Minimal deterministic multi-instrument delta hedge primitive.

    Strategy: to remain minimal while being permutation-invariant, the
    primitive finds the instruments with maximal absolute delta (within
    the SSOT delta tolerance) and allocates the hedge across that set in a
    deterministic, value-based way. For selected instruments S we set

        q_i = delta_portfolio * sign(delta_i) / sum(|delta_j| for j in S)

    which yields sum(q_i * delta_i) == delta_portfolio and therefore a
    residual of zero (modulo floating point rounding within SSOT tolerances).

    Returns (quantities_list, residual) where residual ==
    delta_portfolio - sum(q_i * delta_i).
    """
    n = len(deltas)
    if n == 0:
        return [], delta_portfolio

    tol = DEFAULT_TOLERANCES[MetricClass.DELTA].abs

    # Deterministic guard: forbid near-zero delta instruments using SSOT
    for d in deltas:
        if abs(d) <= tol:
            raise ZeroDivisionError("delta_hedge instrument delta is zero or near-zero: deterministic hedge impossible")

    # Fast-exit: near-zero portfolio exposure
    if abs(delta_portfolio) <= tol:
        return [0.0] * n, 0.0

    abs_vals = [abs(d) for d in deltas]
    max_abs = max(abs_vals)

    # Select all instruments whose abs(delta) is within SSOT tolerance of max_abs
    selected = [i for i, a in enumerate(abs_vals) if abs(a - max_abs) <= tol]

    # Defensive: should not happen due to guards above, but protect division
    sum_abs_selected = sum(abs_vals[i] for i in selected)
    if sum_abs_selected == 0.0:
        raise ZeroDivisionError("sum of selected absolute deltas is zero: deterministic hedge impossible")

    q = [0.0] * n
    # Allocate across selected instruments proportional to their sign, in a
    # way that depends only on the delta values (not on input ordering).
    for i in selected:
        q[i] = delta_portfolio * math.copysign(1.0, deltas[i]) / sum_abs_selected

    residual = delta_portfolio - sum(qi * di for qi, di in zip(q, deltas))
    return q, residual


__all__.append("multi_delta_hedge")
