from dataclasses import dataclass, field
from typing import Literal, Dict
from datetime import datetime

@dataclass(frozen=True)
class Quote:
    kind: Literal["spot", "vol", "rate", "div", "fx_spot", "fx_forward"]
    key: str
    value: float

@dataclass(frozen=True)
class MarketSnapshot:
    asof: datetime
    spots: Dict[str, float] = field(default_factory=dict)
    vols: Dict[str, float] = field(default_factory=dict)
    rates: Dict[str, float] = field(default_factory=dict)
    divs: Dict[str, float] = field(default_factory=dict)
    fx_spots: Dict[str, float] = field(default_factory=dict)
    fx_forwards: Dict[str, float] = field(default_factory=dict)
