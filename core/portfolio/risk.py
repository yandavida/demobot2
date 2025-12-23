from __future__ import annotations

from dataclasses import dataclass

from core.contracts.risk_types import Greeks, PortfolioRiskSnapshot
from core.portfolio.engine import PortfolioEngine
from core.portfolio.models import Money, Portfolio





def aggregate_portfolio_risk(
    portfolio: Portfolio, engine: PortfolioEngine
) -> PortfolioRiskSnapshot:
    """Aggregate portfolio PV and Greeks into a risk snapshot.

    For now this piggybacks on the portfolio valuation for PV and returns
    zeroed Greeks (no per-position sensitivities are available yet).
    """

    total_value_base = engine.evaluate_portfolio(portfolio)

    zero_greeks = Greeks(0.0, 0.0, 0.0, 0.0, 0.0)
    return PortfolioRiskSnapshot(total_pv=float(total_value_base.amount), currency=total_value_base.ccy, greeks=zero_greeks, positions=tuple())
