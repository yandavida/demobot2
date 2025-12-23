from dataclasses import dataclass, field, asdict
from typing import Tuple, Dict, Literal
from .reasons import Reason, ReasonCode
from .metrics import MetricValue

@dataclass(frozen=True)
class OpportunityDecisionTrace:
    candidate_id: str
    accepted: bool
    reasons: Tuple[Reason, ...] = field(default_factory=tuple)
    metrics: Tuple[MetricValue, ...] = field(default_factory=tuple)
    pareto: Dict[str, int | bool | None] = field(default_factory=dict)
    tie_break_key: str = ""
    schema_version: Literal["v2-d.1"] = "v2-d.1"

    def __post_init__(self):
        self.validate_invariants()

    def validate_invariants(self):
        # accepted must not have hard reject reasons
        hard_rejects = {
            ReasonCode.INVALID_QUOTES,
            ReasonCode.STALE_QUOTES,
            ReasonCode.MISSING_QUOTES,
            ReasonCode.MIN_EDGE_NOT_MET,
            ReasonCode.MAX_MARGIN_EXCEEDED,
            ReasonCode.DOMAIN_INVARIANT_VIOLATION,
        }
        if self.accepted:
            for r in self.reasons:
                if r.code in hard_rejects:
                    raise ValueError(f"Accepted trace must not contain hard reject reason: {r.code}")
        else:
            if not self.reasons:
                raise ValueError("Rejected trace must have at least one reason.")
        # Duplicate metric names forbidden
        names = [m.name for m in self.metrics]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate metric names in metrics.")
        # tie_break_key must exist and be deterministic
        if not self.tie_break_key:
            object.__setattr__(self, "tie_break_key", self.candidate_id)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["reasons"] = [r.to_dict() for r in self.reasons]
        d["metrics"] = [m.as_dict() for m in self.metrics]
        d["schema_version"] = self.schema_version
        return d
