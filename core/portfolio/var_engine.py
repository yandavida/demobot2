from __future__ import annotations

import math

from core.portfolio.models import Money
from core.portfolio.risk import PortfolioRiskSnapshot
from core.portfolio.var_models import VarConfig, VarResult


def calculate_parametric_var(
    snapshot: PortfolioRiskSnapshot, config: VarConfig
) -> VarResult:
    z_map = {0.95: 1.65, 0.99: 2.33}
    z = z_map.get(config.confidence, 2.33)

    pv_abs = abs(snapshot.total_pv)
    sigma = config.daily_volatility
    var_amount = z * sigma * pv_abs * math.sqrt(config.horizon_days)

    var_money = Money(amount=var_amount, ccy=snapshot.currency)
    return VarResult(
        amount=var_money,
        horizon_days=config.horizon_days,
        confidence=config.confidence,
        daily_volatility=config.daily_volatility,
    )
