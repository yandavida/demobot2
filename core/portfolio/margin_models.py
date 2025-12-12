from __future__ import annotations

from dataclasses import dataclass

from core.portfolio.models import Money


@dataclass
class MarginConfig:
    """Configuration for baseline portfolio margin."""

    rate: float = 0.15
    minimum: float = 0.0
    currency: str | None = None


@dataclass
class MarginResult:
    """Baseline required margin in base currency."""

    required: Money
    rate: float
    minimum: float


__all__ = ["MarginConfig", "MarginResult"]
