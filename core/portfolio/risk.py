from __future__ import annotations

from dataclasses import dataclass

from core.greeks import Greeks
from core.portfolio.engine import PortfolioEngine
from core.portfolio.models import Money, Portfolio


@dataclass(frozen=True)
class PortfolioRiskSnapshot:
    """Aggregated portfolio risk snapshot in base currency."""

    pv_base: Money
    greeks: Greeks


def aggregate_portfolio_risk(
    portfolio: Portfolio, engine: PortfolioEngine
) -> PortfolioRiskSnapshot:
    """Aggregate portfolio PV and Greeks into a risk snapshot.

    For now this piggybacks on the portfolio valuation for PV and returns
    zeroed Greeks (no per-position sensitivities are available yet).
    """

    total_value_base = engine.evaluate_portfolio(portfolio)

    zero_greeks = Greeks(0.0, 0.0, 0.0, 0.0, 0.0)

    return PortfolioRiskSnapshot(pv_base=total_value_base, greeks=zero_greeks)
