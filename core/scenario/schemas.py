
from dataclasses import dataclass
from typing import Any, Sequence, Dict, List
from core.marketdata.schemas import MarketSnapshot

@dataclass(frozen=True)
class ScenarioRequest:
    positions: Sequence[Any]
    market: MarketSnapshot
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
