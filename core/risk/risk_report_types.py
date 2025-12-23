from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from core.contracts.risk_types import PortfolioRiskSnapshot
from core.risk.semantics import RiskContext

@dataclass(frozen=True)
class PortfolioRiskReport:
    base_snapshot: PortfolioRiskSnapshot
    risk_context: RiskContext
    created_at: datetime
