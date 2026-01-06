# G0.4a — mypy baseline: scope & policy

Goal
- Provide a pragmatic, institutional-grade mypy baseline for an Always‑Green SaaS.
- Ensure deterministic, incremental typing progress without blocking development.

## What this PR Explicitly Does NOT Do

This document is intentionally non-operative.

This PR does NOT:
- modify mypy configuration (pyproject.toml / mypy.ini)
- change CI behavior or gates
- require any production or test code changes
- claim mypy cleanliness outside the defined baseline scope
- imply readiness for `mypy .` at repository level

Its sole purpose is to define scope, policy, and sequencing.

## Baseline Scope Definition (Phase 1)

The initial mypy baseline is intentionally narrow and risk-contained.

### Included in Phase 1
- `core/validation/**`
- `core/commands/**`

These paths are:
- deterministic
- side-effect free
- foundational to system correctness

### Explicitly Excluded (Phase 1)
- legacy finance / pricing modules
- portfolio math and analytics
- adapters, API layers, UI, and CLI
- tests (except strict contract tests, if applicable)

Expansion beyond this scope requires an explicit, versioned gate.

Policy (enforceable rules)
- Baseline is expressed by an explicit mypy configuration that uses `files=` / `packages=` / `exclude=` to limit scope.
- No use of `ignore_errors = true` or global `# type: ignore` sweep; per-line `# type: ignore` allowed only with a documented justification in source control.
- `warn_unused_ignores = true` must be enabled for the baseline scope.
- No CI job that runs `mypy .` globally until baseline expansion is deliberate and approved.
- Per-module overrides are permitted, but only via configured `mypy` sections and with an explicit PR justification (which files are in scope and why).

Incremental expansion process
1. Proposal: a module/folder is proposed for Phase N+1 with an owner and target typing level.
2. The author adds typing to the module, removes existing local ignores, and resolves type errors locally.
3. The module is added to the baseline `files=` / `packages=` list in a follow-up config PR and merged.
4. CI runs the expanded baseline and the author fixes any CI regressions. No regressions are allowed.

No regressions rule
- Any PR that modifies baseline-scoped files must preserve the mypy-green status for that scoped baseline. Breaks must be fixed before merge.

## Exit Criteria — G0.4a

G0.4a is considered complete when:
- the mypy baseline scope is explicitly documented
- expansion policy is clearly defined
- no code, configuration, or CI changes are introduced

This gate is documentation-only and establishes policy, not enforcement.

Notes
- This PR is docs-only and does not change code, CI, or mypy configuration. It defines the institutional policy for an incremental mypy rollout.
