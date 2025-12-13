from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List


class ReasonCode(str, Enum):
    FRESH_QUOTES = "FRESH_QUOTES"
    STALE_QUOTES = "STALE_QUOTES"
    STABLE_EDGE = "STABLE_EDGE"
    UNSTABLE_EDGE = "UNSTABLE_EDGE"
    NET_EDGE_OK = "NET_EDGE_OK"
    NET_EDGE_LOW = "NET_EDGE_LOW"
    NEW_OPPORTUNITY = "NEW_OPPORTUNITY"
    PERSISTENT_OPPORTUNITY = "PERSISTENT_OPPORTUNITY"


@dataclass
class Reason:
    code: ReasonCode
    detail: str


def classify_reasons(signals: dict[str, float], seen_count: int) -> List[Reason]:
    reasons: list[Reason] = []
    freshness_ms = signals.get("freshness_ms", 0)
    stability = signals.get("edge_bps_stability", 1)
    net_edge_bps = signals.get("net_edge_bps", 0)

    if freshness_ms < 10_000:
        reasons.append(Reason(code=ReasonCode.FRESH_QUOTES, detail="Recent quotes"))
    else:
        reasons.append(Reason(code=ReasonCode.STALE_QUOTES, detail="Quotes are aging"))

    if stability >= 0.8:
        reasons.append(Reason(code=ReasonCode.STABLE_EDGE, detail="Edge stable across updates"))
    else:
        reasons.append(Reason(code=ReasonCode.UNSTABLE_EDGE, detail="Edge fluctuating"))

    if net_edge_bps > 0:
        reasons.append(Reason(code=ReasonCode.NET_EDGE_OK, detail="Positive net edge"))
    else:
        reasons.append(Reason(code=ReasonCode.NET_EDGE_LOW, detail="Net edge low or negative"))

    if seen_count <= 1:
        reasons.append(Reason(code=ReasonCode.NEW_OPPORTUNITY, detail="First sighting"))
    else:
        reasons.append(Reason(code=ReasonCode.PERSISTENT_OPPORTUNITY, detail="Repeated sighting"))

    return reasons


__all__ = ["Reason", "ReasonCode", "classify_reasons"]
