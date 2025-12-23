from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.portfolio.models import Money


@dataclass(frozen=True)
class PositionGreeks:
    delta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    theta: float = 0.0
    rho: float = 0.0

    def __add__(self, other: "PositionGreeks") -> "PositionGreeks":
        if not isinstance(other, PositionGreeks):
            return NotImplemented

        return PositionGreeks(
            delta=self.delta + other.delta,
            gamma=self.gamma + other.gamma,
            vega=self.vega + other.vega,
            theta=self.theta + other.theta,
            rho=self.rho + other.rho,
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, object] | None) -> "PositionGreeks":
        """Build a ``PositionGreeks`` from a mapping of greek name to value."""

        if data is None:
            return cls()

        def _get(name: str) -> float:
            raw = data.get(name, 0.0)
            try:
                return float(raw)  # type: ignore[arg-type]
            except Exception:
                return 0.0

        return cls(
            delta=_get("delta"),
            gamma=_get("gamma"),
            vega=_get("vega"),
            theta=_get("theta"),
            rho=_get("rho"),
        )



