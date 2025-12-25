from dataclasses import dataclass, field
from typing import Any, Sequence, Dict, List

@dataclass(frozen=True)
class ScenarioMarketInputs:
    spot_by_symbol: Dict[str, float]
    vol_by_symbol: Dict[str, float]
    rate_by_symbol_or_ccy: Dict[str, float]
    div_by_symbol: Dict[str, float] = field(default_factory=dict)
    fx_forward_by_pair: Dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class ScenarioRequest:
    positions: Sequence[Any]
    market: ScenarioMarketInputs
    spot_shocks: List[float]
    vol_shocks: List[float]
    use_cache: bool = True

@dataclass(frozen=True)
class ScenarioPoint:
    spot_shock: float
    vol_shock: float
    pv: float
    pnl: float
    components: Dict[str, float]

@dataclass(frozen=True)
class ScenarioResponse:
    points: List[ScenarioPoint]
    hash_key: str
    cache_hit: bool
