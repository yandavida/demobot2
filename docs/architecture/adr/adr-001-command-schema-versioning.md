Title: ADR-001 — Command Schema Versioning Policy

Status
------
ACCEPTED

Context
-------
Gate B commands are a public, canonical contract between upstream producers and downstream consumers. In practice, command shapes evolve over time. Without a clear versioning rule, consumers risk misinterpreting fields or applying incompatible upgrades.

Decision
--------
Every canonical command SHALL include a `schema_version: int` field at the top-level of the command payload. Systems that validate commands MUST reject any command with an unknown, missing, or non-integer `schema_version`. Validators MUST NOT attempt to auto-upgrade or silently coerce older/newer versions.

Rationale
---------
- Explicit versioning makes changes discoverable and auditable.\
- Forensic traceability and migration planning REQUIRE a clear version marker.\
- Automatic in-place upgrades can hide incompatibilities and lead to data loss.

Consequences
------------
- Producers MUST populate `schema_version` when emitting commands.\
- Consumers and validators MUST reject commands without a valid `schema_version` (validation-time failure).\
- Any change in the command contract that affects decoding semantics SHALL increment `schema_version` and be accompanied by a migration plan and tests.\
- Tooling that processes commands MUST surface schema_version mismatches as errors, not warnings.
