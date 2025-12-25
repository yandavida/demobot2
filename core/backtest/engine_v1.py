import json
import hashlib
from typing import Any, Sequence, Optional
from core.marketdata.fingerprint import market_snapshot_fingerprint
from .schemas import BacktestRequest, BacktestResult, BacktestPoint
from core.scenario.schemas import ScenarioRequest
from core.scenario.engine import compute_scenario

MODEL_VERSION = "backtest_v1_replay"

def build_backtest_hash_key(req: BacktestRequest) -> str:
    def sorted_positions(positions: Sequence[Any]):
        try:
            return sorted(positions, key=lambda p: getattr(p, 'id', str(p)))
        except Exception:
            return sorted(positions, key=lambda p: str(p))
    payload = {
        "positions": [json.loads(json.dumps(p, default=lambda o: o.__dict__, sort_keys=True)) for p in sorted_positions(req.positions)],
        "timeline_fingerprints": [market_snapshot_fingerprint(s) for s in req.market_timeline],
        "spot_shocks": list(req.spot_shocks),
        "vol_shocks": list(req.vol_shocks),
        "model_version": MODEL_VERSION,
    }
    s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode()).hexdigest()

def run_backtest_v1(req: BacktestRequest) -> BacktestResult:
    # 1. Validate timeline ordering
    asofs = [snap.asof for snap in req.market_timeline]
    if any(a2 < a1 for a1, a2 in zip(asofs, asofs[1:])):
        raise ValueError("market_timeline must be ordered by non-decreasing asof")
    points = []
    for snapshot in req.market_timeline:
        scenario_req = ScenarioRequest(
            positions=req.positions,
            market=snapshot,
            spot_shocks=[0.0],
            vol_shocks=[0.0],
            use_cache=req.use_cache
        )
        scenario_resp = compute_scenario(scenario_req)
        pt = scenario_resp.points[0]
        # TODO: integrate risk_snapshot (F2) if available
        points.append(BacktestPoint(
            asof=snapshot.asof,
            risk_snapshot=None,  # TODO: replace with real risk snapshot
            scenario_hash_key=scenario_resp.hash_key,
            pnl_at_zero_shock=pt.pnl
        ))
    run_hash_key = build_backtest_hash_key(req)
    return BacktestResult(points=points, run_hash_key=run_hash_key)
