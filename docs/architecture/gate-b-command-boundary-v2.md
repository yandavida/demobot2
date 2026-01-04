Gate B v2 — Command Boundary & Protocol Hardening

Canonical Specification (Institutional-Grade)

Status: PARTIAL (see Status Table)
Audience: Core / Infra / Audit / Institutional Review
Role: Deterministic Command Firewall between API and Orchestrator

0. Purpose (Why Gate B Exists)

Gate B is not validation sugar and not a business layer.

Gate B is a deterministic command firewall whose sole purpose is to guarantee that only legal, well-formed, non-duplicative, and protocol-consistent commands are allowed to enter the system.

After Gate B:

No duplicate command can mutate state

No illegal ordering can reach business logic

No ambiguous error can leak to API

All retries are safe

All behavior is replay-safe

Finance, Market Data, and Numeric layers must assume Gate B correctness and therefore must not re-defend against protocol errors.

1. Non-Negotiable Architecture Principles (Locked)

Schema Layer Is Sealed

❌ No schema changes

❌ No new tables / columns

✔️ All behavior expressed above persistence

Determinism by Construction

Same input + same order ⇒ same output

No wall-clock

No randomness

No environment dependence

Separation of Responsibilities

Store: persist/load only

Gate B: legality & protocol

Orchestrator: flow only

Finance/Market/Numeric: meaning only

Tests: proof, not decoration

Replay Is First-Class

All Gate B logic must survive restart + replay

No hidden state

No temporal assumptions

Evidence-Driven Closure

No gate is “closed” without:

pytest

ruff

mypy

compileall

2. Gate B Scope (Explicit)

Gate B owns only:

Command protocol

Validation

Ordering legality

Idempotency

Error taxonomy

Deterministic operational outcome

Gate B explicitly does not own:

Finance logic

Market data

Pricing

Risk

Execution

API transport

3. Status Overview (Truth Table)
Sub-Gate	Description	Status
B1	Command Protocol (Types + Registry)	❌ PARTIAL
B2	Ordering Rules	⚠️ PARTIAL
B3	Strict / Lenient Validation Modes	❌ NOT DONE
B4	Error Protocol (Core + API)	❌ NOT DONE
B5	Idempotency Framework	✅ CLOSED
B6	Gate B ↔ Gate A Integration Proof	❌ NOT DONE
4. B1 — Command Protocol (Types + Registry)
B1.1 Command Registry (Allowlist) — NOT DONE

Requirements:

Explicit allowlist of supported command.kind

Unknown kind ⇒ VALIDATION_ERROR

No dynamic registration

Registry is code-level, not config-level

Rationale (Critical):
Without a registry, Gate B is not a firewall — it is a parser.

B1.2 Typed Command Contracts — PARTIAL

Canonical V2 Commands:

IngestEventCommand ✅ CLOSED

IngestQuoteCommand ❌

ComputeRequestCommand ❌

SnapshotRequestCommand ❌

For each command:

Required fields

Payload schema

Strict structural validation

command_id + session_id policy explicitly defined

No behavior allowed here. Contracts only.

B1.3 Schema Versioning Policy — NOT DECIDED (Must be Locked)

Gate B v2 must explicitly choose one:

Option A: schema_version required, validated

Option B: single-version protocol (v1 only), no versioning yet

Ambiguity is forbidden.

5. B2 — Ordering Rules
B2.1 Intra-Command Ordering — CLOSED

client_sequence continuity enforced

B2.2 Cross-Command Ordering — NOT DONE

Examples (must be formalized):

Can ComputeRequestCommand occur before any IngestQuoteCommand?

Is SnapshotRequestCommand allowed at any time?

Are multiple IngestEventCommands always legal?

Rules must be:

Deterministic

Explicit

Proven in tests

6. B3 — Validation Modes (Strict / Lenient)

Status: NOT DONE

Requirements:

strict=True: any violation ⇒ structured error

strict=False: explicitly defined downgrade behavior (or explicitly forbidden)

No silent coercion. No “best effort” unless proven.

This gate is essential for:

Backward compatibility

Gradual rollout

Institutional clients

7. B4 — Error Protocol Contract
B4.1 Core Error Taxonomy — PARTIAL

Already present:

Categories: VALIDATION / SEMANTIC / CONFLICT

Missing:

Allowlist of error codes

Stable message policy

No dynamic text

B4.2 API Mapping Contract — NOT DONE

Must define:

Core → HTTP mapping (400 / 409 / 422)

Envelope shape

Backward compatibility guarantees

Tests at API boundary

Without this, Gate B is not externally trustworthy.

8. B5 — Idempotency Framework — CLOSED (FULL)
Closed Sub-Gates:

B5.1 Identity: (session_id, command_id)

B5.2 Canonical Fingerprint

B5.3 Seen-Command Detection (read-only)

B5.4 Conflict Classification

B5.5 Deterministic Outcome Mapping

This implementation exceeds typical institutional standards.

9. B6 — Gate B ↔ Gate A Integration Proof — NOT DONE

Purpose:
Prove that Gate B semantics survive persistence, restart, and replay.

Required Proofs:

NEW ⇒ ACCEPTED ⇒ persisted ⇒ reopen ⇒ seen=True

IDEMPOTENT_REPLAY ⇒ no new events written

CONFLICT ⇒ no state mutation

All outcomes deterministic across restart

Tests required: integration-level (no finance)

10. Exit Criteria — Gate B v2 CLOSED

Gate B v2 is considered CLOSED only if:

B1 (Registry + Typed Commands) — CLOSED

B2 (Ordering, intra + cross) — CLOSED

B3 (Validation Modes) — CLOSED

B4 (Error Protocol Core + API) — CLOSED

B5 (Idempotency) — CLOSED ✅

B6 (Integration Proof) — CLOSED

No partial closure is acceptable for institutional readiness.

11. Explicit Blacklist (Applies to All Gate B Work)

❌ No schema changes

❌ No finance logic

❌ No market data

❌ No API transport logic inside core

❌ No clocks / randomness

❌ No TODOs

❌ No “temporary” behavior

12. Executive Summary

Gate B v2 is not yet closed, despite the excellent completion of B5.

The remaining work is protocol completeness, not complexity:

Defining what commands exist

Defining what order is legal

Defining how errors surface

Proving persistence interaction

Only after Gate B v2 is closed:

Gate M (Market Data)

Gate N (Numeric Policy)

Gate R (Regression Harness)

Finance / Options features

can begin without systemic risk.
