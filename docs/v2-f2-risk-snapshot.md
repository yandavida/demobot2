# V2-F.2 Risk Snapshot Contract

## Purpose
Provides a deterministic, portfolio-level risk view for a set of positions. Used for reporting, risk management, and audit. No margin or scenario logic included in this version.

## Fields
- **pv**: Total present value (float or Money, per repo convention)
- **greeks**: AggregatedGreeks (delta, gamma, vega, theta; all canonical units)
- **margin**: OUT OF SCOPE (not present in v1)

## Determinism
- Output is fully deterministic for a given set of positions and inputs.
- Aggregation is pure: no randomness, time, or external state.

## Dependency on F1 Contracts
- Greeks units: vega per +1% IV, theta per day (see F1 contract)
- FX and options conventions as in F1
- No normalization or scaling beyond qty * contract_multiplier


## Margin v1 (placeholder)

- This margin model is a heuristic placeholder, NOT regulatory or production-grade.
- **Formulas:**
	- margin_options = A_DELTA*|Δ| + B_GAMMA*|Γ| + C_VEGA*|V|
	- margin_fx = K_NOTIONAL * sum(|notional|)
	- required = max(0, margin_options + margin_fx)
- **Components:**
	- options: margin_options
	- fx: margin_fx
- **Units:**
	- Greeks are canonical (F1): vega per 1% IV, theta per day (theta not used in margin v1)
- **Determinism:**
	- Margin calculation is deterministic and permutation-invariant.
- **Audit:**
	- Any change to margin logic must be covered by audit/guardrail tests.
