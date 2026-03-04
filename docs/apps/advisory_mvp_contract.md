# Advisory MVP Contract

## Purpose

Define a thin application-layer advisory contract for:
EXPOSURE -> SCENARIOS -> HEDGE SUGGESTION -> REPORT

This document is an interface plan only and does not alter core schemas.

## Input JSON Schema (Business Exposures)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AdvisoryMvpInput",
  "type": "object",
  "required": ["snapshot_id", "as_of", "base_currency", "exposures"],
  "properties": {
    "snapshot_id": { "type": "string", "minLength": 1 },
    "as_of": { "type": "string", "format": "date-time" },
    "base_currency": { "type": "string", "minLength": 3, "maxLength": 3 },
    "target_hedge_ratio": { "type": "number", "minimum": 0, "maximum": 1 },
    "scenario_profile_id": { "type": "string" },
    "exposures": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["row_id", "pair", "direction", "notional", "settlement_date"],
        "properties": {
          "row_id": { "type": "string", "minLength": 1 },
          "pair": { "type": "string", "pattern": "^[A-Z]{3}/[A-Z]{3}$" },
          "direction": { "type": "string", "enum": ["receivable", "payable"] },
          "notional": { "type": "number" },
          "settlement_date": { "type": "string", "format": "date" },
          "reference_rate": { "type": "number" },
          "meta": { "type": "object", "additionalProperties": true }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

## Output JSON Schema (Report + Artifact References)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AdvisoryMvpOutput",
  "type": "object",
  "required": [
    "snapshot_id",
    "risk_artifact_ref",
    "exposure_artifact_ref",
    "portfolio_surface_artifact_ref",
    "tables",
    "hedge_suggestion"
  ],
  "properties": {
    "snapshot_id": { "type": "string", "minLength": 1 },
    "risk_artifact_ref": {
      "type": "object",
      "required": ["schema", "version", "sha256"],
      "properties": {
        "schema": { "type": "string" },
        "version": { "type": "string" },
        "sha256": { "type": "string", "minLength": 64, "maxLength": 64 }
      },
      "additionalProperties": false
    },
    "exposure_artifact_ref": {
      "type": "object",
      "required": ["schema", "version", "sha256"],
      "properties": {
        "schema": { "type": "string" },
        "version": { "type": "string" },
        "sha256": { "type": "string", "minLength": 64, "maxLength": 64 }
      },
      "additionalProperties": false
    },
    "portfolio_surface_artifact_ref": {
      "type": "object",
      "required": ["schema", "version", "sha256"],
      "properties": {
        "schema": { "type": "string" },
        "version": { "type": "string" },
        "sha256": { "type": "string", "minLength": 64, "maxLength": 64 }
      },
      "additionalProperties": false
    },
    "tables": {
      "type": "object",
      "required": ["scenario_pnl", "exposure_delta", "loss_ranking"],
      "properties": {
        "scenario_pnl": { "type": "array", "items": { "type": "object" } },
        "exposure_delta": { "type": "array", "items": { "type": "object" } },
        "loss_ranking": { "type": "array", "items": { "type": "object" } }
      },
      "additionalProperties": false
    },
    "hedge_suggestion": {
      "type": "object",
      "required": ["method", "target_ratio", "trades"],
      "properties": {
        "method": { "type": "string", "enum": ["delta_hedge", "multi_delta_hedge"] },
        "target_ratio": { "type": "number", "minimum": 0, "maximum": 1 },
        "trades": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["instrument_id", "quantity", "side"],
            "properties": {
              "instrument_id": { "type": "string" },
              "quantity": { "type": "number" },
              "side": { "type": "string", "enum": ["buy", "sell"] }
            },
            "additionalProperties": false
          }
        }
      },
      "additionalProperties": false
    },
    "narrative": {
      "type": "object",
      "properties": {
        "summary": { "type": "string" },
        "assumptions": { "type": "array", "items": { "type": "string" } }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

## Numeric Authority Rule

LLM or UI narrative may explain results, but all numeric values must originate from deterministic artifacts.

Authoritative numeric sources:
- Risk artifact outputs
- Exposures artifact outputs
- Portfolio surface artifact outputs

No generated text is allowed to invent or modify numeric values.
