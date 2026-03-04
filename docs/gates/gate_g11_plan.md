# Gate 11 Plan

## Gate Objective

Expose deterministic risk artifacts as product-level outputs for:

- Corporate Treasury FX exposure analysis
- Asset managers / hedge fund portfolio risk consumption

## Architectural Principle

Gate 11 must:

- not modify pricing engines
- not modify risk artifacts schemas
- not introduce stochastic components

It only orchestrates existing deterministic infrastructure.

## Gate 11 Slices

### G11.1 Advisory Input Contract

Business exposures input schema.

Fields example:

company_id  
exposure_rows[]

Each row:

currency_pair  
direction (receivable/payable)  
notional  
maturity_date  
optional hedge_ratio

Output:

normalized exposure object + RiskRequest.

### G11.2 Exposure Adapter

Transforms business exposures into deterministic contracts.

Mapping:

exposure row → FXForwardContract.

Produces:

contracts_by_instrument_id  
RiskRequest.

### G11.3 Advisory Read Model

Transforms artifacts into product outputs.

Tables:

Exposure summary  
Scenario P&L table  
Delta exposure table  
Worst-scenario ranking

Must include:

snapshot_id  
valuation timestamp reference.

### G11.4 Bank Quote Validation

Optional module validating bank quotes.

Input:

bank quote (forward points / outright)

Process:

compare quote vs deterministic fair price.

Output:

spread deviation  
explanation.

### G11.5 Audit Pack Export

Bundle:

input payload  
snapshot_id  
risk artifacts  
recommendation block  
manifest.

Purpose:

audit-ready output.

### G11.6 Portfolio Risk API (AM / HF)

Read model exposing:

portfolio scenario cube  
delta exposures  
stress ranking.

## Out of Scope

Gate 11 does not introduce:

- Greeks engines
- volatility surfaces
- VaR / Expected Shortfall
- trading execution
- UI dashboards
