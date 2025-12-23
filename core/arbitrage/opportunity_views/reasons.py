from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict

class ReasonCode(str, Enum):
    INVALID_QUOTES = "INVALID_QUOTES"
    STALE_QUOTES = "STALE_QUOTES"
    MISSING_QUOTES = "MISSING_QUOTES"
    MIN_EDGE_NOT_MET = "MIN_EDGE_NOT_MET"
    MAX_MARGIN_EXCEEDED = "MAX_MARGIN_EXCEEDED"
    DOMAIN_INVARIANT_VIOLATION = "DOMAIN_INVARIANT_VIOLATION"
    INTERNAL_ERROR = "INTERNAL_ERROR"

@dataclass(frozen=True)
class Reason:
    code: ReasonCode
    message: str
    observed: Optional[float | str] = None
    threshold: Optional[float | str] = None
    unit: Optional[str] = None
    context: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        # Deterministic, JSON-safe
        d = asdict(self)
        d["code"] = self.code.value
        d["context"] = dict(sorted((str(k), str(v)) for k, v in self.context.items()))
        return d
