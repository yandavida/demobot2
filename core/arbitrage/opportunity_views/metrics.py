from dataclasses import dataclass, asdict
from typing import Optional, Literal

@dataclass(frozen=True)
class MetricValue:
    name: str
    value: Optional[float] = None
    unit: str = ""
    direction: Literal["max", "min"] = "max"
    notes: Optional[str] = None

    def as_dict(self) -> dict:
        d = asdict(self)
        return d
