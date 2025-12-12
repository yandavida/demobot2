from __future__ import annotations

from dataclasses import dataclass

from core.portfolio.models import Money


@dataclass
class VarConfig:
    """Baseline parametric VaR configuration."""

    horizon_days: int = 1
    confidence: float = 0.99
    daily_volatility: float = 0.02


@dataclass
class VarResult:
    """Parametric VaR result in base currency."""

    amount: Money
    horizon_days: int
    confidence: float
    daily_volatility: float


__all__ = ["VarConfig", "VarResult"]
