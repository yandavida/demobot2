Title: ADR-006 — Market Snapshot Determinism & Immutability

Status
------
ACCEPTED

Context
-------
Applies to: Gate M — Market Data Boundary

The codebase implements a content-addressed market snapshot model and an artifact store used by replayable compute paths. Downstream consumers rely on stable, immutable snapshots for deterministic compute and auditability.

Decision
--------
Market snapshots SHALL be identified by a content-derived identity and stored as immutable artifacts. Once a snapshot artifact is written to the artifact store it SHALL NOT be mutated in-place. Compute paths that depend on snapshots SHALL NOT perform provider fallback at compute time; they must treat the snapshot as authoritative and complete.

Rationale
---------
- Content-addressed identities ensure snapshot integrity and enable efficient verification.\
- Immutable artifacts prevent accidental or silent state drift that would break deterministic replay.\
- Disallowing provider fallback at compute time preserves replay determinism and forensic traceability.

Consequences
------------
- Implementations MUST compute and verify a content hash for any snapshot they persist or consume (see `core/market_data/identity.py` and `core/market_data/artifact_store.py`).\
- Consumers that require fresh market data MUST publish a new snapshot artifact; they MAY NOT mutate existing artifacts.\
- Compute services that accept a snapshot reference MUST validate presence in the artifact store and fail fast if missing, rather than silently querying live providers.

Evidence / References
---------------------
- `core/market_data/artifact_store.py` (artifact persistence and retrieval)\
- `core/market_data/identity.py` (snapshot identity computation)\
- API usage: `api/v2/service_sqlite.py` validates snapshot presence before compute
