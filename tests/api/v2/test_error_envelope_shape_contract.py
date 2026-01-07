from fastapi.testclient import TestClient
from api.main import app

from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0, FxRates, SpotPrices, Curve, InterestRateCurves, MarketConventions
from core.market_data.artifact_store import put_market_snapshot

client = TestClient(app)


def create_session():
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    return resp.json()["session_id"]


def ingest_compute(session_id, kind, params):
    req = {"type": "COMPUTE_REQUESTED", "payload": {"kind": kind, "params": params}}
    return client.post(f"/api/v2/sessions/{session_id}/events", json=req)


def make_payload(base: str = "USD") -> MarketSnapshotPayloadV0:
    fx = FxRates(base_ccy=base, quotes={f"{base}/EUR": 0.9, f"EUR/{base}": 1.0 / 0.9})
    spots = SpotPrices(prices={base: 1.0, "EUR": 0.9}, currency={base: base, "EUR": "EUR"})
    curve = Curve(day_count="ACT/365", compounding="annual", zero_rates={"1Y": 0.01})
    ircs = InterestRateCurves(curves={base: curve})
    conv = MarketConventions(calendar="TARGET", day_count_default="ACT/365", spot_lag=2)
    return MarketSnapshotPayloadV0(fx_rates=fx, spots=spots, curves=ircs, vols=None, conventions=conv)


def test_400_validation_error_uses_envelope_detail_no_wrapper():
    sid = create_session()

    # Missing (empty) market_snapshot_id triggers validation 400 from validators
    resp = ingest_compute(sid, "SNAPSHOT", {"market_snapshot_id": ""})
    assert resp.status_code == 400
    body = resp.json()
    assert "detail" in body
    assert isinstance(body["detail"], dict)
    assert body["detail"].get("code") is not None
    assert body.get("error") is None


def test_422_semantic_error_uses_envelope_detail_no_wrapper():
    sid = create_session()
    p = make_payload()
    msid = put_market_snapshot(p)

    # Request symbols not present in snapshot -> semantic validation (422)
    resp = ingest_compute(sid, "SNAPSHOT", {"market_snapshot_id": msid, "symbols": ["NOTINSHOT"]})
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body
    assert isinstance(body["detail"], dict)
    assert body["detail"].get("code") is not None
    assert body.get("error") is None
