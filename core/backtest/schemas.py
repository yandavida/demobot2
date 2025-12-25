from dataclasses import dataclass
from typing import Any, Sequence, List, Mapping, Optional
from datetime import datetime
from core.marketdata.schemas import MarketSnapshot

@dataclass(frozen=True)
class BacktestRequest:
    positions: Sequence[Any]
    market_timeline: Sequence[MarketSnapshot]
    spot_shocks: List[float]
    vol_shocks: List[float]
    use_cache: bool = True

@dataclass(frozen=True)
class BacktestPoint:
    asof: datetime
    risk_snapshot: Optional[Mapping[str, Any]]  # TODO: replace with RiskSnapshot type if available
    scenario_hash_key: str
    pnl_at_zero_shock: float

@dataclass(frozen=True)
class BacktestResult:
    points: List[BacktestPoint]
    run_hash_key: str
