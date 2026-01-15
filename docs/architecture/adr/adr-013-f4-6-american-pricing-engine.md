Title: ADR-F4.6 — American Options Pricing Engine (Binomial, Deterministic)

Status
------
ACCEPTED

Date
----
2026-01-15

Gate
----
F4

Tags
----
pricing, american-options, determinism, numeric-policy

Context
-------
PortfolioEngine V2 requires a canonical, auditable, and deterministic pricing implementation for American-style options. Upstream gates have already defined deterministic contracts, numeric policy (Gate N), and golden governance (Gate R). Sub-gates in F4 have delivered: contract surface schemas (F4.1), invariants tests (F4.2), and deterministic FD greeks tooling (F4.4). This ADR locks the architectural choice for the canonical American pricing engine used by V2.

Decision
--------
The canonical American pricing engine for V2 SHALL be a recombining Cox–Ross–Rubinstein (CRR) binomial tree implemented as a pure, deterministic, parameterized function. The implementation SHALL accept an explicit integer step count `N` and SHALL perform early-exercise checks at each node using the intrinsic value vs continuation value. Discounting, up/down factors, and probabilities are computed deterministically from input parameters.

Rationale
---------
- Binomial trees provide an explicit, transparent algorithm where discretization error is explicit and controllable via `N`.
- Alternatives such as Longstaff–Schwartz, PDE solvers, or trinomial schemes introduce either stochastic elements, additional model complexity, or less transparent discretization behaviour; these are deferred until the canonical binomial is stabilized.
- Requiring an explicit `N` and deterministic arithmetic eliminates heuristic auto-selection and ensures repeatable acceptance criteria (convergence via N→2N checks).

Scope
-----
IN SCOPE
- American Call and Put pricing
- Continuous dividend yield (`q`)
- Early exercise handled by node-wise max(intrinsic, continuation)
- Deterministic pricing with explicit step count `N`
- Compatibility with F4.2 invariants and Gate N numeric policy

OUT OF SCOPE
- Greeks (canonical units and deterministic FD helpers are defined in F4.4)
- Golden dataset generation strategy (governed separately by Gate R)
- Performance micro-optimizations and parallel variants
- Monte Carlo or calibration-based methods

Formal Model
------------
Parameters: S (spot), K (strike), T (time to expiry), r (rate), q (dividend yield), sigma (volatility), N (integer steps).

Time step: dt = T / N
Up/Down factors (CRR):
  u = exp(sigma * sqrt(dt))
  d = 1 / u
Risk-neutral probability:
  p = (exp((r - q) * dt) - d) / (u - d)

Discounting: values are discounted by exp(-r * dt) per step.

Early exercise rule: at each node, option value = max(intrinsic, discounted expected continuation).

Engineering Contract
--------------------
The engine SHALL expose a pure function signature (pseudocode):

```
def american_price(s: float, k: float, t: float, sigma: float, r: float, q: float, is_call: bool, N: int) -> float:
    pass  # pure deterministic calculation, no side effects
```

The contract guarantees:
- No side effects (no I/O, no global mutation)
- No wall-clock or environment-dependent behaviour
- No randomness or seeded stochastic processes
- Deterministic numeric result for identical inputs

Numeric Policy & Determinism
----------------------------
- No local ad-hoc epsilons are allowed; all thresholds and tolerances MUST come from the central `core.numeric_policy` or be expressed via discretization proxies (e.g., |P(N) - P(2N)|).
- FD greeks used for diagnostics or golden generation must follow canonical FD step choices and deterministic rounding rules (see Gate F4.4).
- Determinism by construction is mandatory: deterministic ordering, rounding, and serialization rules are required whenever outputs are persisted.

Invariants / Acceptance Criteria
--------------------------------
- No-arbitrage sanity checks (non-negative option prices, call/put parity bounds where applicable)
- Monotonicity: price monotone in S and vol (subject to known exceptions with dividends)
- American price ≥ European price (checked with discretization-aware margins)
- Convergence: price(N), price(2N) comparisons must be stable under numeric policy
- Repeat-run determinism: repeated identical runs must produce byte-identical serialized outputs for golden governance

Testing Strategy
----------------
- Tests-first approach: invariants (F4.2) and FD greeks tests (F4.4) run before any change to production pricing code.
- Regression harness: golden datasets governed by Gate R shall be used to lock canonical inputs/outputs once the engine is stabilized.
- Automated CI: golden and invariants suites must run in CI (see ADR-012)

Consequences
------------
- Provides an auditable, deterministic canonical implementation for American pricing in V2
- Encourages explicit convergence testing instead of hidden heuristics
- Keeps pricing behavior stable and future-proof for audits and institutional usage

References
----------
- ADR-014 — Deterministic Event Time and Replay
- Gate N — Numeric Policy
- Gate F4 — American Options roadmap and sub-gates (F4.1..F4.4)
