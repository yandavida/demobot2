Gate B4 - Unify HTTP error mapping (v2)

What: Canonicalize API v2 HTTP error responses so every handler raises an HTTPException with `detail` set to a flat `ErrorEnvelope` dict.

Files changed: see working patch and file list in this branch under `var/verification`:
- var/verification/working_changes.patch
- var/verification/working_changes_files.txt

Verification:
- Lint: ruff (local) — passed
- Compile: python -m compileall — passed
- Tests: pytest — 468 passed, 1 skipped

Notes:
- No DB schema or core business logic changes.
- A narrow legacy compatibility behavior for session-not-found was preserved in `api/v2/router.py` to avoid breaking minimal API expectations; recommend updating tests to the canonical envelope in follow-up.

Commit: 1787256d77064da861aa2cd3962843f5cbe9adbf
Branch: codex/v2-b4-http-error-mapping-clean
