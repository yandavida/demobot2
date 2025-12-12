from __future__ import annotations

from core.portfolio.margin_models import MarginConfig, MarginResult
from core.portfolio.models import Money
from core.portfolio.risk import PortfolioRiskSnapshot


def calculate_portfolio_margin(
    snapshot: PortfolioRiskSnapshot, config: MarginConfig
) -> MarginResult:
    base_ccy = config.currency or snapshot.pv_base.ccy
    pv_amount = abs(snapshot.pv_base.amount)
    required_raw = pv_amount * config.rate
    required_amount = max(required_raw, config.minimum)
    required_money = Money(amount=required_amount, ccy=base_ccy)

    return MarginResult(
        required=required_money, rate=config.rate, minimum=config.minimum
    )
