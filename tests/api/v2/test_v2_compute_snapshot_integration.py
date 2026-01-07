from fastapi.testclient import TestClient
from api.main import app

from core.market_data.market_snapshot_payload_v0 import (
    MarketSnapshotPayloadV0,
    FxRates,
    SpotPrices,
    Curve,
    InterestRateCurves,
    MarketConventions,
)
from core.market_data.artifact_store import put_market_snapshot

client = TestClient(app)


def make_payload(base: str = "USD") -> MarketSnapshotPayloadV0:
    fx = FxRates(base_ccy=base, quotes={f"{base}/EUR": 0.9, f"EUR/{base}": 1.0 / 0.9})
    spots = SpotPrices(prices={base: 1.0, "EUR": 0.9}, currency={base: base, "EUR": "EUR"})
    curve = Curve(day_count="ACT/365", compounding="annual", zero_rates={"1Y": 0.01})
    ircs = InterestRateCurves(curves={base: curve})
    conv = MarketConventions(calendar="TARGET", day_count_default="ACT/365", spot_lag=2)
    return MarketSnapshotPayloadV0(fx_rates=fx, spots=spots, curves=ircs, vols=None, conventions=conv)


def create_session():
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    return resp.json()["session_id"]


def ingest_compute(session_id, kind, params):
    req = {"type": "COMPUTE_REQUESTED", "payload": {"kind": kind, "params": params}}
    return client.post(f"/api/v2/sessions/{session_id}/events", json=req)


def test_compute_with_existing_snapshot_succeeds():
    sid = create_session()
    p = make_payload()
    msid = put_market_snapshot(p)

    # Submit compute referencing persisted artifact
    resp = ingest_compute(sid, "SNAPSHOT", {"market_snapshot_id": msid})
    assert resp.status_code == 201

    # Ensure the compute request is visible in the read model with params
    list_resp = client.get(f"/api/v2/sessions/{sid}/compute/requests?include_params=true")
    assert list_resp.status_code == 200
    items = list_resp.json().get("items", [])
    assert len(items) >= 1
    found = False
    for it in items:
        params = it.get("params")
        if params and params.get("market_snapshot_id") == msid:
            found = True
    assert found


def test_compute_with_missing_snapshot_returns_404_and_error_envelope():
    sid = create_session()
    missing = "f" * 64
    resp = ingest_compute(sid, "SNAPSHOT", {"market_snapshot_id": missing})
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body
    # ErrorEnvelope mapping: expect canonical code
    assert body["detail"].get("code") == "market_snapshot_not_found"
