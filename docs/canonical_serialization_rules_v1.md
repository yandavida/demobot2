# Canonical Serialization Rules V1 (PR-3)

This document freezes the PR-3 canonical serialization and hashing boundary for `OptionPricingArtifactV1` payload hashing.

## Scope
The implemented scope in PR-3 is intentionally narrow:
- artifact identity fields (`artifact_contract_name`, `artifact_contract_version`)
- embedded `OptionValuationResultV1`
- embedded valuation measures from PR-1/PR-2 contracts

No portfolio, scenario, lifecycle, advisory, resolver, or engine-kernel semantics are introduced here.

## Canonical Payload Shape
Canonical payload is a fixed-order object with keys in this exact order:
1. `artifact_contract_name`
2. `artifact_contract_version`
3. `valuation_result`

`valuation_result` is serialized in fixed key order:
1. `engine_name`
2. `engine_version`
3. `model_name`
4. `model_version`
5. `resolved_input_contract_name`
6. `resolved_input_contract_version`
7. `resolved_input_reference`
8. `valuation_measures`

Each `valuation_measures` entry is serialized in fixed key order:
1. `measure_name`
2. `value`

Measure ordering is inherited from the frozen canonical tuple in `valuation_measure_set_v1.py`. No reordering is performed in serialization.

## Decimal Canonicalization Policy
PR-3 uses a frozen normalized plain-text Decimal policy:
- input must be `Decimal`
- non-finite values are rejected
- exponent notation is not emitted
- trailing fractional zeros are removed
- decimal point is removed when unnecessary
- zero is serialized as `"0"`
- negative zero is canonicalized to `"0"`

Examples:
- `Decimal("100.00")` -> `"100"`
- `Decimal("1.2300")` -> `"1.23"`
- `Decimal("0.000")` -> `"0"`

## String, Null, and Boolean Policy
For PR-3 implemented payloads:
- strings are preserved exactly as provided by validated upstream contracts
- no whitespace rewriting is applied by serialization
- null and booleans are encoded by canonical JSON semantics if present in future governed extensions

## JSON Encoding Policy
Canonical serialization uses compact JSON with:
- UTF-8 byte encoding for hash input
- `ensure_ascii=True`
- `allow_nan=False`
- `separators=(",", ":")`
- no pretty-printing
- no variable whitespace

## Hashing Policy
- algorithm: SHA-256
- input: canonical serialized UTF-8 payload bytes
- output: 64-character lowercase hex digest
- no salt
- no wall-clock data
- no environment-dependent components

Semantically identical governed payloads must produce identical hashes. Different payload content must produce different hashes.
The canonical payload hash domain excludes `canonical_payload_hash` itself and is computed only from `artifact_contract_name`, `artifact_contract_version`, and `valuation_result` to prevent circular/self-referential hashing.
