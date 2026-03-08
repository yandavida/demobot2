# FX Options Contract Domain Preparation V1

## 1. Background

PortfolioEngine V2 is intended to support treasury-oriented derivatives workflows, including FX hedging and future FX option analytics.

Before implementing FX option pricing, the domain model must be complete enough to support:

- pricing
- valuation measures
- lifecycle events
- premium handling
- settlement handling
- advisory and risk use cases

## 2. Why FX Options Need Domain Completeness

Incomplete FX option contract terms create downstream architecture risk even when pricing formulas appear to work in isolation.

Common failure modes from incomplete terms include:

- premium cashflow ambiguity
- settlement ambiguity
- fixing ambiguity
- expiry cutoff ambiguity
- domestic versus foreign curve ambiguity
- volatility quote convention ambiguity

These ambiguities propagate into lifecycle outcomes, valuation lineage, and risk/advisory interpretation.

## 3. Minimum FX Option Contract Terms

The minimum institutional domain requires explicit representation of the following terms:

- `currency pair orientation`: defines directional interpretation of the FX pair and prevents inconsistent strike and settlement interpretation.
- `base currency`: identifies the base leg of the currency pair for contract and valuation semantics.
- `quote currency`: identifies the quote leg of the currency pair and pricing denomination context.
- `option type (call / put)`: defines payoff direction.
- `exercise style`: defines exercise admissibility rules and lifecycle behavior.
- `notional`: defines economic exposure magnitude.
- `notional currency semantics`: defines the currency context for notional interpretation and payoff consistency.
- `strike`: defines exercise exchange rate.
- `expiry date`: defines contractual maturity date.
- `expiry cut-off time`: defines the operational cut-off boundary on expiry date.
- `expiry cut-off timezone`: defines timezone-normalized interpretation of the cut-off boundary.
- `premium currency`: defines premium cashflow denomination.
- `premium amount or premium representation basis`: defines premium economics as explicit amount or governed representation basis.
- `premium payment date`: defines premium settlement timing.
- `settlement style (deliverable / non-deliverable)`: defines settlement mechanism and resulting economic interpretation.
- `settlement date`: defines settlement value date.
- `settlement calendars`: defines calendar-adjusted settlement logic.
- `fixing source`: defines authoritative market source for fixing.
- `fixing date`: defines fixing determination date.
- `domestic curve id`: links valuation to domestic discounting curve governance.
- `foreign curve id`: links valuation to foreign discounting curve governance.
- `volatility surface quote convention`: defines volatility interpretation boundary used by valuation and controls.
- `exercise schedule if applicable`: defines schedule-based exercise semantics where contract style requires it.

## 4. Premium and Settlement Semantics

FX option contracts must explicitly support:

- premium currency
- premium payment timing
- settlement style
- settlement date logic
- deliverable versus non-deliverable semantics

These are first-class economic terms, not optional metadata, because they define realized cashflows and settlement outcomes that must be reproducible in lifecycle, valuation, and audit artifacts.

## 5. Fixing and Expiry Semantics

The contract domain must explicitly support:

- fixing source
- fixing date
- expiry cut-off time
- expiry timezone
- exercise timing implications where relevant

These fields are required for deterministic lifecycle and settlement logic, including consistent event ordering, exercise admissibility, and valuation cut-off behavior.

## 6. Curve and Volatility Dependencies

FX option valuation depends on explicit linkage to:

- domestic curve
- foreign curve
- volatility surface convention

These dependencies must be domain-visible and governed, not hidden in ad hoc pricing assumptions.

## 7. Lifecycle and Artifact Impact

FX option domain completeness is required not only for pricing but also for:

- lifecycle events
- settlement outcomes
- cashflow artifacts
- valuation lineage
- risk artifacts
- advisory outputs

Without domain-complete terms, these outputs cannot remain deterministic, auditable, and governance-aligned.

## 8. Out Of Scope

This document does not:

- implement FX option pricing formulas
- choose a final runtime contract schema
- implement lifecycle code
- implement settlement code
- implement pricing engines

## 9. Final Architecture Position

Decision:
Future FX options support in PortfolioEngine V2 requires a domain-complete contract definition from the start.
Economic-term completeness is a prerequisite for pricing, lifecycle, settlement, and risk correctness.
