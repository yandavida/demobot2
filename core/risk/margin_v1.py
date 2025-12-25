from dataclasses import dataclass, field
from typing import Dict, List

# Conservative placeholder constants (do not overfit tests to these)
A_DELTA = 0.1
B_GAMMA = 0.2
C_VEGA = 0.15
K_NOTIONAL = 0.05

@dataclass(frozen=True)
class MarginSnapshot:
    required: float
    model: str = "MARGIN_V1_PLACEHOLDER"
    components: Dict[str, float] = field(default_factory=dict)


def compute_margin_v1(delta: float, gamma: float, vega: float, fx_notionals: List[float]) -> MarginSnapshot:
    """
    Compute margin requirement using placeholder v1 model.
    - margin_options = A_DELTA*|Δ| + B_GAMMA*|Γ| + C_VEGA*|V|
    - margin_fx = K_NOTIONAL * sum(abs(n) for n in fx_notionals)
    - required = max(0, margin_options + margin_fx)
    Returns MarginSnapshot with breakdown.
    """
    margin_options = A_DELTA * abs(delta) + B_GAMMA * abs(gamma) + C_VEGA * abs(vega)
    margin_fx = K_NOTIONAL * sum(abs(n) for n in fx_notionals)
    required = max(0.0, margin_options + margin_fx)
    components = {"options": margin_options, "fx": margin_fx}
    return MarginSnapshot(required=required, components=components)
