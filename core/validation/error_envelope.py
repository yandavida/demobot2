from dataclasses import dataclass
from typing import Literal, Dict


@dataclass(frozen=True)
class ErrorEnvelope:
    category: Literal["VALIDATION", "CONFLICT", "SEMANTIC"]
    code: str
    message: str
    details: Dict[str, str]
    error_count: int = 1
