from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from core.contracts.risk_types import PortfolioRiskSnapshot
from core.scenarios.risk_report import RiskScenarioReport
from core.risk.semantics import RiskContext
from core.risk.var_types import VarResult

@dataclass(frozen=True)
class UnifiedPortfolioRiskReport:
    """
    V1 institutional offline risk report (audit-ready).
    Composition only: does not modify pricing/engines.
    """
    created_at: datetime
    base_snapshot: PortfolioRiskSnapshot
    scenario_report: RiskScenarioReport
    # Tail risk (computed from scenario deltas)
    historical_var: Optional[VarResult] = None
    historical_cvar: Optional[float] = None  # optional convenience
    notes: dict[str, str] = field(default_factory=dict)
    risk_context: Optional[RiskContext] = None
    risk_assumptions: Optional[object] = None  # placeholder for RiskAssumptions
