V1 HARD LOCK (Final)

Locked (must not change without V2-breaking plan):

- Contracts (canonical paths):
	- core/contracts/risk_types.py (Greeks, PortfolioRiskSnapshot, RiskScenarioResult, etc.)
	- core/risk/semantics.py (RiskContext / RiskAssumptions semantics)
	- core/risk/var_types.py
	- core/risk/var_parametric.py
	- core/risk/var_historical.py
	- core/risk/unified_report_types.py

- Semantics:
	- PV is per-unit at pricing level; scaling occurs only at portfolio aggregation
	- Greeks are mathematical derivatives; aggregated consistently
	- Historical VaR/CVaR are scenario-based using delta_pv_abs distribution

- Guaranteed by tests (Stage 3):
	- VaR/CVaR invariants, boundaries, determinism, cross-check sanity

- Explicit non-goals of V1:
	- No realtime
	- No stateful execution
	- No streaming
	- No execution layer
	- No persistence requirements
Stage 1 — Risk Vocabulary

Horizon: 1d, 10d

Confidence: 0.99 default, configurable

Base currency: ILS default

Note: “Stage 1 adds semantics only; VaR/CVaR in Stage 2”
Locked Contracts

PriceResult

Greeks

RiskScenarioResult

PortfolioRiskSnapshot

Locked Semantics

PV is per-unit / per-contract

Scaling happens only at portfolio level

Greeks represent true mathematical derivatives

FX conversion applies only in portfolio risk layer

Explicitly NOT Locked

Pricing formulas

Volatility models

Engines

New risk methodologies

Purpose: single source of truth for V1 discipline.
