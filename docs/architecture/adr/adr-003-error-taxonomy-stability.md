Title: ADR-003 — Error Taxonomy Stability Rule

Status
------
ACCEPTED

Context
-------
Error codes surface to monitoring, alerts, dashboards, and downstream integration. Reusing or repurposing codes breaks historical analysis and can silently change behavior in clients that rely on specific codes.

Decision
--------
The error taxonomy SHALL be treated as an append-only set of error codes. Once an error code is introduced and used in persisted telemetry or emitted messages, that code MUST NOT be repurposed for any other meaning. Codes MAY be deprecated, but deprecated codes SHALL remain recognized by validators and receivers for backward compatibility.

Rationale
---------
- Append-only error codes ensure reliable observability and historical integrity.\
- Deprecation (with mapping and migration) is safer than reuse.\
- This rule prevents semantic drift in alerts and automated responses.

Consequences
------------
- Error producers MUST NOT reuse existing codes for new failure modes.\
- Receivers and monitors MUST treat codes as stable keys; changes require an ADR and migration plan.\
- A process for deprecation and mapping MUST be documented alongside the taxonomy.
