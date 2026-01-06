# G0.4a — mypy baseline: scope & policy

Goal
- Provide a pragmatic, institutional-grade mypy baseline for an Always‑Green SaaS.
- Ensure deterministic, incremental typing progress without blocking development.

Phase 1 Scope (IN)
- core/contracts/  — typed data contracts and DTOs.
- core/validation/ — validators and canonical error factories.
- core/commands/   — typed command contracts and small command helpers.
- Optional: `api/v2/` (schemas/validators) only if its surface is stable; otherwise defer to Phase 2.

Phase 1 Out of Scope (OUT)
- `ui/` (interactive UI/Streamlit/etc.)
- legacy modules and experimental packages (`sandbox/`, `pages/`, `strategies_legacy.py`, etc.)
- most tests unless explicitly added to Phase 1

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

Exit criteria for G0.4a
- This document is reviewed and approved by the core team.
- An initial `mypy` scope config (not part of this PR) is agreed that lists Phase 1 targets.

Notes
- This PR is docs-only and does not change code, CI, or mypy configuration. It defines the institutional policy for an incremental mypy rollout.
