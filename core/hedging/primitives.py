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
