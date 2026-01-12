# Codex Working Protocol (Institutional Grade) — SSOT

**Status:** NORMATIVE  
**Scope:** Applies to all PortfolioEngine V2 Gates work  
**Non-goals:** Does not change system behavior; documentation-only

---

## Purpose

This document defines the **mandatory working protocol** when using Codex.

Its goals are to ensure that:
- No architectural drift is introduced
- No uncontrolled decisions enter the codebase
- All changes are auditable, reviewable, and replayable
- Codex acts strictly as a precise executor — not a decision-maker

These rules are a **formal part of the system architecture**.

---

## Non-Negotiable Principles

### 1. Codex Does Not Make Architectural Decisions

Codex implements decisions — it does not make them.

Codex must **not decide** on:
- Gate boundaries
- Policy changes
- Semantic meaning
- Contract changes
- Behavioral interpretation

All such decisions are made **outside the code** and only then handed off for implementation.

If there is doubt — Codex must stop and ask. Guessing is forbidden.

---

### 2. One Task at a Time

- No parallel tasks
- No “while at it”
- No bundled objectives

Each task must be:
- Small
- Hermetic
- Expressible in a single clear sentence

If a task cannot be described in one sentence, it is too large.

---

### 3. One PR = One Topic

- No side refactors
- No opportunistic cleanup
- No “it was already here so I fixed it”

If something is outside the defined scope:
- Skip it, or
- Propose a future Gate / PR explicitly

---

## Mandatory Branch Discipline

Before starting any work, Codex must execute and show:

```bash
git switch -c <new-branch-name>
git branch --show-current
git status
 (See <attachments> above for file contents. You may not need to search or read the file again.)
```

There are no exceptions:

Not for docs

Not for tests

Not for “safe changes”

Without evidence — no commit.

Evidence Over Assertions

Statements such as:

“This is deterministic”

“This cannot regress”

“This is safe”

Are not acceptable without tests.

Determinism and guarantees must be enforced by:

Failing tests

Explicit invariants

Regression protection

Ambiguity Handling Protocol

If Codex encounters:

Ambiguity

Two or more reasonable options

A mismatch between documentation and code

Codex must:

Stop

Present 1–2 options only

Explain the tradeoff briefly

Choose the most conservative default

State explicitly what was chosen and why

Codex must never:

Decide silently

Infer intent

“Align with existing code” without approval

Forbidden Actions

Codex must not:

Change schemas

Modify existing policy

Touch closed Gates

Add silent defaults

Add convenience helpers

Mix layers (core ↔ api ↔ tests)

Introduce clock, environment, or randomness

Any of the above constitutes an architectural bug.

Gate-Based Work Only

All work must be associated with an explicit Gate:

Open Gate → work allowed

Closed Gate → no changes permitted

Changes to a closed Gate require:

A new ADR, or

A new Gate

There is no such thing as a “small change” to a closed Gate.

Mandatory PR Format

Title

<type>(v2): Gate <X> <short description>


Body (minimal)

What changed (bullets)

Why (architectural guarantee)

Evidence (ruff / compileall / pytest)

Risk (usually: low)

Notes (optional)

No prose. No marketing.

Post-Merge Responsibility

Once a Gate is closed:

It is documented

It is locked

It is protected by tests

Codex must not return to it unless explicitly instructed.

Principle Summary

Codex is:

A precise executor

A force multiplier

Not a source of authority

The system remains:

Deterministic

Audit-ready

Institutional-grade (See <attachments> above for file contents. You may not need to search or read the file again.)
