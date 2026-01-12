# Gate M — Market Data Boundary (Hard Boundary) — V2 (SSOT)

## Purpose (Institutional Guarantees)
Gate M defines a hard institutional boundary around Market Data so that **all financial computation** in the system is:
- **Snapshot-anchored**: every SNAPSHOT compute is bound to `market_snapshot_id`.
- **Replayable**: the same ComputeRequest + the same `market_snapshot_id` yields the same outcome (deterministic / value-equivalent where applicable).
- **Provider-independent**: compute must not pull live data, fallback to providers, or synthesize defaults.
- **Audit-ready**: months-later replay is supported for audit / investigations / dispute resolution.

## Non-Negotiables (Locked)
- `market_snapshot_id` is **mandatory** for SNAPSHOT compute requests.
- Compute path MUST NOT:
  - fetch live market data
  - resolve snapshot "as of now"
  - use `datetime.now()/utcnow()`, env-dependent behavior, randomness
  - apply silent defaults for missing market inputs
- Market snapshots are **immutable** artifacts: once written, never mutated.
- Market-data related failures surface as **canonical ErrorEnvelope** (stable taxonomy), mapped at the API boundary.

## Scope
### Gate M is responsible for
- MarketSnapshot payload contract (V0) and identity strategy
- Artifact store (put/get immutable snapshots)
- Replay-only snapshot resolution in compute path
- Semantic market validation (requirements vs snapshot)
- Evidence tests proving determinism, restart/reopen stability, and no provider fallback

### Gate M is NOT responsible for
- Pricing / MTM / Greeks / risk math (Gate F)
- Database schema changes (forbidden in this Gate)
- Read models / materialization / reporting (Gate N/R)
- Real vendor integrations (later; contracts + artifacts only in Gate M)

---

## Contract: MarketSnapshotPayloadV0 (Current Baseline)
### Canonical payload model
The snapshot payload is defined by the canonical model:
- `MarketSnapshotPayloadV0` (see code reference below)

This payload is treated as an **immutable input artifact** for compute.

### What a Market Snapshot represents
A Market Snapshot is a frozen view of market inputs required to evaluate a compute request under replay:
- quotes / FX pairs / tenors / curves / surfaces as represented in V0 payload
- only what is required by the current compute contract (no implied logic)

---

## Snapshot Identity (LOCKED)
### Identity function
`market_snapshot_id` is content-addressed:

- `market_snapshot_id = sha256(canonical_json(payload))`

### Canonicalization rules (as implemented)
Canonical JSON serialization must be stable:
- deterministic key ordering (e.g., `sort_keys=True`)
- stable separators / compact form
- no clock/env/random involvement
- payload is the single source of truth for identity (no provider calls)

> Note: The definitive algorithm is the implementation of `market_snapshot_id` in code.
> This SSOT defines the policy and invariants; the code defines the exact mechanics.

### Permutation invariance requirement
Logically equivalent payloads that differ only by key insertion order must produce:
- the same `market_snapshot_id`

---

## Artifact Store (Immutable Snapshots)
### Responsibilities
- `put_market_snapshot(payload) -> market_snapshot_id`
  - idempotent: re-put of the same payload yields the same id
  - no mutation: once stored, content does not change
- `get_market_snapshot(market_snapshot_id) -> payload`
  - deterministic retrieval
  - missing snapshot returns a canonical not-found error at boundary

### Immutability policy
Snapshots are immutable by design:
- no update API
- no overwrite behavior exposed
- storage is treated as append-only at the boundary

---

## Compute Semantics (Replay-Only)
SNAPSHOT compute requests resolve market data exclusively via:
- `market_snapshot_id` -> artifact store -> payload

Compute path must not:
- call providers
- infer missing values
- use live market data

---

## Validation Semantics (Precedence)
The validation sequence is locked:
1. **Command/schema validation (Gate B)**  
2. **Market semantic validation (Gate M)**  
3. Compute execution

### Market semantic validation (Gate M3)
Gate M validates compute requirements against the referenced snapshot:
- missing symbol / FX pair / tenor / curve node (as represented in V0)
- missing required quote fields
- any mismatch yields a SEMANTIC error (HTTP 422) with canonical envelope

---

## Canonical Errors (Boundary Mapping)
Canonical behavior for SNAPSHOT compute:
- Missing `market_snapshot_id` (or invalid format)  
  -> VALIDATION error (HTTP 400), canonical ErrorEnvelope.
- `market_snapshot_id` provided but artifact not found  
  -> NOT_FOUND error (HTTP 404), canonical ErrorEnvelope.
- Snapshot present but semantic market requirements not satisfied  
  -> SEMANTIC error (HTTP 422), canonical ErrorEnvelope.

---

## “Do Not” Rules (Prevent Mini Pricing Engine)
MarketSnapshot must not evolve into a pricing engine:
- no interpolation
- no implied curve construction
- no derived/estimated values
- no convenience helpers that change semantics

---

## Evidence Index (Code + Tests)
This Gate is evidence-driven. The following are the canonical references:

### Core implementation
- `core/market_data/identity.py` — `market_snapshot_id` implementation (canonical JSON + SHA256)
- `core/market_data/artifact_store.py` — immutable snapshot artifact store (`put_market_snapshot`, `get_market_snapshot`)
- `core/market_data/validate_requirements.py` — semantic market validation returning SEMANTIC ErrorEnvelope

### API boundary enforcement
- `api/v2/validators.py` — requires `market_snapshot_id` for SNAPSHOT; canonical 400 for missing/invalid
- `api/v2/service_sqlite.py` — replay-only resolution:
  - resolves snapshot via artifact store
  - maps semantic failures to 422
  - maps missing snapshot to 404
- `api/v2/http_errors.py` / `api/v2/router.py` — canonical ErrorEnvelope mapping

### Tests (must remain green)
**M1 / M5(1) — snapshot id required (400)**
- `tests/api/v2/test_v2_compute_snapshot_id_validation.py::test_missing_market_snapshot_id_is_400`
- `tests/api/v2/test_v2_compute_snapshot_id_validation.py::test_invalid_market_snapshot_id_is_400`

**M2 — artifact immutability/idempotency + deterministic identity**
- `tests/market_data/test_artifact_store.py::test_put_get_roundtrip_idempotent`
- `tests/market_data/test_artifact_store.py::test_get_missing_raises_valueerror`
- `tests/market_data/test_market_snapshot_identity.py::test_same_payload_same_id`
- `tests/market_data/test_market_snapshot_identity.py::test_different_payload_different_id`

**M3 — semantic validation (422)**
- `tests/market_data/test_market_requirements_validation.py` (semantic codes)
- `tests/api/v2/test_v2_compute_semantic_market_errors_422.py::test_compute_with_unknown_symbol_returns_422`
- `tests/api/v2/test_error_envelope_shape_contract.py` (envelope shape contract)

**M5(2) — snapshot not found (404)**
- `tests/api/v2/test_v2_compute_snapshot_integration.py::test_compute_with_missing_snapshot_returns_404_and_error_envelope`

**M4 — replay evidence hardening (no fallback, permutation invariance, restart determinism)**
- `tests/api/v2/test_v2_m4_replay_evidence.py`  
  (Added as part of Gate M4 closure PR; must remain green.)

---

## Gate M Checklist (Re-baselined)
- M0 — Definitions & Contracts (SSOT): **CLOSED** (this document)
- M1 — Identity binding: **CLOSED** (see Evidence Index)
- M2 — Deterministic immutable snapshots: **CLOSED** (see Evidence Index)
- M3 — Semantic market validation: **CLOSED** (see Evidence Index)
- M4 — Replay evidence hardening: **CLOSED** (see Evidence Index; requires M4 test suite merged)
- M5 — ComputeRequest contract update (required snapshot id + canonical errors): **CLOSED** (see Evidence Index)
