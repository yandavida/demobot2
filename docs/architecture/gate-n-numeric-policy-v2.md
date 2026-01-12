# Gate N — Numeric Policy (V2) — SSOT

**Status:** NORMATIVE
**Scope:** PortfolioEngine V2 (all compute paths)
**Non-goals:** Pricing engines, datasets, performance optimization

---

## Purpose

Gate N exists to prevent numeric drift:

- across Python versions
- across machines
- across engines
- across time

Gate N defines HOW numbers are compared and represented, not WHAT financial models compute.

---

## Numeric Representation Policy

- Policy-level statement on numeric types: the policy specifies when floating-point types are permitted and when Decimal-style exact representations are required; this is a policy decision only, not an implementation mandate.
- Mixed implicit casting is prohibited: policy forbids designs that rely on implicit casts between representation types within a single compute path.
- No recommendations beyond the explicit statements above are included in this policy.

---

## Units & Scaling Policy

Canonical units are defined for all core numeric domains. Any change to canonical units requires a new Gate or an ADR.

| Metric | Canonical Unit |
|---|---|
| prices | canonical unit of currency per asset (unit defined by Gate) |
| rates | decimal fraction per annum (unit defined by Gate) |
| volatility | decimal fraction (annualized where applicable) |
| greeks (delta) | change in price per unit underlying |
| greeks (gamma) | change in delta per unit underlying |
| greeks (vega) | change in price per unit volatility (decimal) |
| greeks (theta) | change in price per unit time |

Any unit change requires a new Gate or an ADR.

---

## Rounding Policy

- No rounding is allowed inside core computations.
- Rounding is permitted only at presentation boundaries (for example: UI, reporting, export), explicitly outside compute paths.
- Rounding inside compute paths is forbidden.

---

## Tolerances Policy

- Absolute vs relative tolerance concepts are defined as policy primitives: absolute tolerance applies to metrics with fixed scales; relative tolerance applies where proportional differences are meaningful.
- Tolerances are defined per metric class (for example: price, rate, volatility, greeks).
- This document specifies policy only; no numeric tolerance values are included here.

---

## Stability Expectations

- Numeric stability in this system means that results are reproducible within the permitted tolerances across supported environments, versions, and compute engines.
- Stability expectations will be validated by future Gate N tests (e.g., conceptual Gate N3); tests are referenced conceptually only, with no implementation in this document.

---

## Explicit Non-Goals

- Gate N does NOT implement pricing.
- Gate N does NOT choose models.
- Gate N does NOT define datasets.
- Gate N does NOT optimize performance.

---

## Governance & Change Rules

- Any change to numeric policy requires either a new Gate or an explicit ADR.
- Gate N, once closed, is immutable unless a new Gate or ADR authorizes modification.

---

## Style Rules

- Use a clear, formal, institutional tone.
- No prose beyond what is required by the sections above.
- No examples unless explicitly required by a Gate.
- No speculation.
- No future promises beyond the Gates explicitly stated.
