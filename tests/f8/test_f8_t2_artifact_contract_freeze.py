from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from core.pricing.fx import forward_mtm
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext


SCHEMA_NAME = "pe.f8.valuation_artifact"
SCHEMA_VERSION = "1.0"
ENGINE_NAME = "pe.f8.forward_mtm"
ENGINE_VERSION = "1.0"
HASH_CANONICALIZATION = "json.sort_keys=True,separators=(',',':'),ensure_ascii=False"
HASH_SCOPE = "artifact_excluding_sha256"
HASH_ALGORITHM = "sha256"

FIXTURE_PATH = Path(__file__).resolve().parent / "_data" / "f8_t2_artifact_schema_v1_fixture.json"


def _as_of_ts() -> datetime.datetime:
    return datetime.datetime(
        2026, 3, 2, 12, 0, 0,
        tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
    )


def _fixed_context() -> ValuationContext:
    return ValuationContext(
        as_of_ts=_as_of_ts(),
        domestic_currency="ILS",
        strict_mode=True,
    )


def _fixed_contract() -> fx_types.FXForwardContract:
    return fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="ILS",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 4, 2),
        forward_rate=3.65,
        direction="receive_foreign_pay_domestic",
    )


def _fixed_snapshot() -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=_as_of_ts(),
        spot_rate=3.64,
        df_domestic=0.995,
        df_foreign=0.9982,
    )


def _compute_sha256_excluding_key(artifact: dict[str, Any], exclude_key: str) -> str:
    body = {k: v for k, v in artifact.items() if k != exclude_key}
    payload = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_v1_artifact(
    context: ValuationContext,
    contract: fx_types.FXForwardContract,
    snapshot: fx_types.FxMarketSnapshot,
    result: fx_types.PricingResult,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": {
            "name": SCHEMA_NAME,
            "version": SCHEMA_VERSION,
        },
        "engine": {
            "name": ENGINE_NAME,
            "version": ENGINE_VERSION,
        },
        "inputs": {
            "valuation_context": {
                "as_of_ts": context.as_of_ts.isoformat(),
                "domestic_currency": context.domestic_currency,
                "strict_mode": context.strict_mode,
            },
            "contract": {
                "base_currency": contract.base_currency,
                "quote_currency": contract.quote_currency,
                "notional": contract.notional,
                "forward_date": contract.forward_date.isoformat(),
                "forward_rate": contract.forward_rate,
                "direction": contract.direction,
            },
            "market_snapshot": {
                "as_of_ts": snapshot.as_of_ts.isoformat(),
                "spot_rate": snapshot.spot_rate,
                "df_domestic": snapshot.df_domestic,
                "df_foreign": snapshot.df_foreign,
            },
        },
        "outputs": {
            "pricing_result": {
                "pv_domestic": result.pv,
                "currency": result.currency,
                "metric_class": (
                    result.metric_class.value if result.metric_class is not None else None
                ),
            },
        },
        "hashing": {
            "canonicalization": HASH_CANONICALIZATION,
            "hash_scope": HASH_SCOPE,
            "algorithm": HASH_ALGORITHM,
        },
    }
    body["sha256"] = _compute_sha256_excluding_key(body, "sha256")
    return body


def _make_fixed_artifact() -> dict[str, Any]:
    context = _fixed_context()
    contract = _fixed_contract()
    snapshot = _fixed_snapshot()
    result = forward_mtm.price_fx_forward_ctx(
        context=context,
        contract=contract,
        market_snapshot=snapshot,
        conventions=None,
    )
    return _build_v1_artifact(context, contract, snapshot, result)


# ──────────────────────────────────────────────────────────────────────────────
# T1 — Schema identity freeze
# ──────────────────────────────────────────────────────────────────────────────

def test_t2a_t1_schema_identity_freeze():
    artifact = _make_fixed_artifact()

    assert "schema" in artifact, "artifact missing 'schema' key"
    schema = artifact["schema"]
    assert schema["name"] == SCHEMA_NAME, (
        f"schema name mismatch: expected {SCHEMA_NAME!r}, got {schema['name']!r}"
    )
    assert schema["version"] == SCHEMA_VERSION, (
        f"schema version mismatch: expected {SCHEMA_VERSION!r}, got {schema['version']!r}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# T2 — Required keys freeze
# ──────────────────────────────────────────────────────────────────────────────

def test_t2a_t2_required_keys_freeze():
    artifact = _make_fixed_artifact()

    # Top-level keys
    for key in ("schema", "engine", "inputs", "outputs", "hashing", "sha256"):
        assert key in artifact, f"artifact missing required top-level key: '{key}'"

    # inputs.valuation_context
    vc = artifact["inputs"]["valuation_context"]
    for field in ("as_of_ts", "domestic_currency"):
        assert field in vc, f"artifact.inputs.valuation_context missing required field: '{field}'"

    # inputs.contract
    contract = artifact["inputs"]["contract"]
    for field in ("base_currency", "quote_currency", "notional", "forward_date", "forward_rate", "direction"):
        assert field in contract, f"artifact.inputs.contract missing required field: '{field}'"

    # inputs.market_snapshot
    snapshot = artifact["inputs"]["market_snapshot"]
    for field in ("as_of_ts", "spot_rate", "df_domestic", "df_foreign"):
        assert field in snapshot, f"artifact.inputs.market_snapshot missing required field: '{field}'"

    # outputs.pricing_result
    pr = artifact["outputs"]["pricing_result"]
    for field in ("pv_domestic", "currency", "metric_class"):
        assert field in pr, f"artifact.outputs.pricing_result missing required field: '{field}'"

    # hashing
    hashing = artifact["hashing"]
    for field in ("canonicalization", "hash_scope"):
        assert field in hashing, f"artifact.hashing missing required field: '{field}'"


# ──────────────────────────────────────────────────────────────────────────────
# T3 — Hash rule immutability (round-trip)
# ──────────────────────────────────────────────────────────────────────────────

def test_t2a_t3_hash_rule_round_trip():
    artifact = _make_fixed_artifact()

    stored_sha256 = artifact["sha256"]
    recomputed = _compute_sha256_excluding_key(artifact, "sha256")

    assert recomputed == stored_sha256, (
        f"sha256 round-trip failed.\n"
        f"  stored:     {stored_sha256}\n"
        f"  recomputed: {recomputed}\n"
        "Hashing rule may have drifted."
    )


# ──────────────────────────────────────────────────────────────────────────────
# T4 — Backward-compat guard (frozen exemplar fixture)
# ──────────────────────────────────────────────────────────────────────────────

def test_t2a_t4_frozen_fixture_backward_compat():
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Fixture not found at {FIXTURE_PATH}; run _generate_fixture.py to create it.")

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    # Required keys still present
    for key in ("schema", "engine", "inputs", "outputs", "hashing", "sha256"):
        assert key in fixture, f"fixture missing required top-level key: '{key}'"

    # Hash recomputation equals stored sha256 in frozen fixture
    stored = fixture["sha256"]
    recomputed = _compute_sha256_excluding_key(fixture, "sha256")
    assert recomputed == stored, (
        f"Frozen fixture sha256 recomputation failed — artifact schema has drifted.\n"
        f"  stored:     {stored}\n"
        f"  recomputed: {recomputed}"
    )

    # Schema name/version frozen
    assert fixture["schema"]["name"] == SCHEMA_NAME
    assert fixture["schema"]["version"] == SCHEMA_VERSION
