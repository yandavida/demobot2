Title: ADR-007 — Canonical Market Validation Boundary

Status
------
ACCEPTED

Context
-------
Applies to: Gate M — Semantic Validation

The repository contains validation logic for market snapshots that must be enforced prior to any compute. Pricings and engines expect canonical, validated market payloads and must not be responsible for validation or enrichment.

Decision
--------
Semantic market validation SHALL occur prior to compute and SHALL be performed by dedicated validation code. Pricing functions and pricers SHALL NOT resolve, fetch, or enrich market data at compute time. Validation failures SHALL be returned in the canonical error envelope shape used across the codebase; validation code SHALL NOT propagate raw exceptions as-is.

Rationale
---------
- Separating validation from compute preserves single-responsibility and deterministic compute.\
- Returning a canonical error envelope ensures consistent error handling across API and compute layers.\
- Preventing pricers from fetching/enriching market data avoids hidden IO and preserves replayability.

Consequences
------------
- Validation modules (used by API/service layers) MUST run prior to compute requests.\
- Pricing engines and core pricers MUST assume inputs are canonical and validated.\
- Validation failures MUST be translated to the canonical ErrorEnvelope and mapped to appropriate HTTP semantics where applicable.

Evidence / References
---------------------
- Validation code used by compute: `core/market_data/validate_requirements.py`\
- Example integration: `api/v2/service_sqlite.py` lazy-validates snapshot requirements before compute
