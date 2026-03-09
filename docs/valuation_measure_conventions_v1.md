# Valuation Measure Conventions V1

This document is normative for Phase C PR-1 single-trade FX option valuation measures.

## Scope
These measures apply to single-trade governed option valuation outputs only. They are not portfolio aggregation metrics, scenario-layer transformations, lifecycle outputs, or advisory-layer metrics.
This Phase C measure set is governed exclusively for non-linear FX options; linear FX instruments (including spot FX, FX forwards, and simple deliverable FX positions) are out of scope and must use MTM / exposure / carry vocabulary, and the option valuation measure names in this document must not be used as aliases or substitutes for linear FX terminology.

## Canonical Measure Names
The canonical alias-free names are:
1. `present_value`
2. `intrinsic_value`
3. `time_value`
4. `delta_spot_non_premium_adjusted`
5. `gamma_spot`
6. `vega_1vol_abs`
7. `theta_1d_calendar`
8. `rho_domestic_1pct`
9. `rho_foreign_1pct`

## Measure Semantics
1. `present_value`: canonical monetary valuation measure for the option.
2. `intrinsic_value`: immediate exercise value under governed valuation-state inputs; expressed in domestic valuation currency; decomposition measure only; not discounted.
3. `time_value`: defined exactly as `present_value - intrinsic_value`; no silent clamp to zero.
4. `delta_spot_non_premium_adjusted`: spot delta, non-premium-adjusted.
5. `gamma_spot`: second derivative of PV with respect to spot.
6. `vega_1vol_abs`: PV sensitivity to a +1 vol point bump; 1 vol point equals +0.01 absolute volatility.
7. `theta_1d_calendar`: defined exactly as `PV(t+1 calendar day) - PV(t)`.
8. `rho_domestic_1pct`: PV sensitivity to a +1 percentage point bump in the domestic continuously-compounded rate; bump size equals +0.01 absolute rate.
9. `rho_foreign_1pct`: PV sensitivity to a +1 percentage point bump in the foreign continuously-compounded rate; bump size equals +0.01 absolute rate.

## Units and Sign Conventions
1. Monetary measures (`present_value`, `intrinsic_value`, `time_value`) are interpreted in domestic valuation currency.
2. Sensitivity measures use signed values and preserve model-consistent sign.
3. Bump-defined sensitivities must use the governed bump size exactly as documented in this file.

## Deterministic Governance Requirements
1. No aliases, synonyms, or shorthand names are permitted.
2. No hidden default bump conventions are permitted.
3. Semantics are frozen until explicit governed contract evolution.
