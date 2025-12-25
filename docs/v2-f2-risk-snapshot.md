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

## Out of Scope
- Margin calculation
- Scenario engine
- Market data integration
