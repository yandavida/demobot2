from dataclasses import dataclass, field
from typing import Literal, Dict

# Allowlist of compute kinds discovered in the repository
ComputeKind = Literal["SNAPSHOT", "PORTFOLIO_RISK", "SCENARIO_GRID"]


@dataclass(frozen=True)
class ComputeRequestPayload:
    kind: ComputeKind
    params: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ComputeRequestCommand:
    command_id: str
    session_id: str
    payload: ComputeRequestPayload
    kind: Literal["COMPUTE_REQUEST"] = "COMPUTE_REQUEST"
    strict: bool = True
    meta: Dict[str, object] | None = None
