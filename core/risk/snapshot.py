from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class AggregatedGreeks:
    delta: float
    gamma: float
    vega: float
    theta: float

@dataclass(frozen=True)
class RiskSnapshot:
    pv: float  # or Money, per repo convention
    greeks: AggregatedGreeks
    # margin: Optional[float] = None  # OUT OF SCOPE for v1


def compute_risk_snapshot(positions: Iterable[object]) -> RiskSnapshot:
    """
    Deterministically aggregate PV and Greeks for a set of positions.
    Each position must have: pv, greeks (delta, gamma, vega, theta), qty, contract_multiplier.
    Scaling: pv and greeks are multiplied by qty * contract_multiplier before summing.
    Ordering: positions are sorted by str(id) for determinism.
    """
    # Defensive: convert to list and sort for deterministic order
    positions = list(positions)
    positions.sort(key=lambda p: str(getattr(p, 'id', id(p))))
    total_pv = 0.0
    total_delta = 0.0
    total_gamma = 0.0
    total_vega = 0.0
    total_theta = 0.0
    for pos in positions:
        scale = float(getattr(pos, 'qty', 1.0)) * float(getattr(pos, 'contract_multiplier', 1.0))
        pv = float(getattr(pos, 'pv', 0.0))
        greeks = getattr(pos, 'greeks', None)
        if greeks is None:
            continue
        total_pv += pv * scale
        total_delta += float(getattr(greeks, 'delta', 0.0)) * scale
        total_gamma += float(getattr(greeks, 'gamma', 0.0)) * scale
        total_vega += float(getattr(greeks, 'vega', 0.0)) * scale
        total_theta += float(getattr(greeks, 'theta', 0.0)) * scale
    agg = AggregatedGreeks(
        delta=total_delta,
        gamma=total_gamma,
        vega=total_vega,
        theta=total_theta,
    )
    return RiskSnapshot(pv=total_pv, greeks=agg)
