from __future__ import annotations

from .hedging_schemas import HedgeInput, HedgeResultOut, HedgeResidualsOut
from core.hedging.primitives import delta_hedge


STABLE_ZERO_HEDGE_MSG = "delta_hedge == 0: deterministic hedge instrument delta must be non-zero"


def compute_delta_hedge_read_model(inp: HedgeInput) -> HedgeResultOut:
    dp = inp.delta_portfolio
    dh = inp.delta_hedge

    if dh == 0.0:
        raise ValueError(STABLE_ZERO_HEDGE_MSG)

    if dp == 0.0:
        return HedgeResultOut(hedge_type="delta", hedge_quantity=0.0, residuals=HedgeResidualsOut(delta=0.0))

    q, residual = delta_hedge(dp, dh)
    return HedgeResultOut(hedge_type="delta", hedge_quantity=q, residuals=HedgeResidualsOut(delta=residual))


__all__ = ["compute_delta_hedge_read_model"]
