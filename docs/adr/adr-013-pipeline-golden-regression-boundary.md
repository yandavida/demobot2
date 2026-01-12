# ADR-013: Pipeline Golden Regression Boundary

**Status:** ACCEPTED

**Date:** 2026-01-12

## Context

Gate P defines pipeline-level golden regression: a deterministic, fixture-driven regression harness exercised at the pipeline/system level (downstream of pricing). Gate P complements previously established Gates M/N/R by focusing on pipeline reproducibility and end-to-end regression detection without altering numeric policy or pricing-level responsibilities.

## Decision

We define Gate P as a pipeline-level golden regression gate that: (1) uses offline P-INPUT Envelope v1 fixtures, (2) is manifest-driven, (3) verifies canonical expected outputs using the policy-level tolerances in `core.numeric_policy.DEFAULT_TOLERANCES`, and (4) is integrated into CI under a dedicated `pipeline_golden` pytest marker.

## Rationale

Separating pipeline-level regression from pricing-level regression enforces clear responsibilities: pricing engines remain covered by Gate R (pricing-level), while system/pipeline integration and aggregation behavior is covered by Gate P. Using manifest-driven fixtures and a locked numeric policy prevents tests from embedding local tolerances or relying on live services, ensuring reproducibility and auditability.

## Consequences

- Gate P delivers a small, versioned dataset scaffold, canonical expected outputs, a manifest-driven harness, and CI integration (marker + workflow step). These artifacts are archived in the repository and versioned alongside code.
- Comparisons are performed solely against `core.numeric_policy.DEFAULT_TOLERANCES`; changing tolerances or numeric policy requires a new Gate/ADR.
- Gate P does not replace or modify Gate R responsibilities; pricing-level regressions remain evaluated under Gate R.

## Related ADRs

- ADR-005 Institutional Default Bias
- ADR-011 Pricing vs Pipeline Regression Boundary
