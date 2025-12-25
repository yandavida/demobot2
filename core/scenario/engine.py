
import json
import hashlib
from typing import Any, Sequence, Optional
from .schemas import ScenarioRequest, ScenarioResponse, ScenarioPoint
from .cache import ScenarioCache, DEFAULT_SCENARIO_CACHE
from core.marketdata.fingerprint import market_snapshot_fingerprint

MODEL_VERSION = "scenario_v1_fullrepricing"

# --- Stable hashing ---
def build_scenario_hash_key(req: ScenarioRequest) -> str:
    def sorted_positions(positions: Sequence[Any]):
        try:
            return sorted(positions, key=lambda p: getattr(p, 'id', str(p)))
        except Exception:
            return sorted(positions, key=lambda p: str(p))

    payload = {
        "positions": [json.loads(json.dumps(p, default=lambda o: o.__dict__, sort_keys=True)) for p in sorted_positions(req.positions)],
        "spot_shocks": list(req.spot_shocks),
        "vol_shocks": list(req.vol_shocks),
        "market_fingerprint": market_snapshot_fingerprint(req.market),
        "model_version": MODEL_VERSION,
    }
    s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode()).hexdigest()

# --- Engine ---
def compute_scenario(req: ScenarioRequest, cache: Optional[ScenarioCache] = None) -> ScenarioResponse:
    cache = cache or DEFAULT_SCENARIO_CACHE
    hash_key = build_scenario_hash_key(req)
    if req.use_cache:
        cached = cache.get(hash_key)
        if cached:
            return ScenarioResponse(points=cached.points, hash_key=hash_key, cache_hit=True)

    # --- Full repricing logic ---
    # Placeholder: actual repricing logic must be implemented using F1 canonical pricing
    # For now, return dummy points for structure, but validate required market data
    points = []
    # Validate all symbols in positions have spot+vol in snapshot
    symbols = set(getattr(p, 'symbol', None) for p in req.positions)
    for sym in symbols:
        if sym is None:
            raise ValueError("Position missing 'symbol' attribute for market lookup")
        if sym not in req.market.spots:
            raise ValueError(f"Missing spot for symbol: {sym}")
        if sym not in req.market.vols:
            raise ValueError(f"Missing vol for symbol: {sym}")
    for spot_shock in req.spot_shocks:
        for vol_shock in req.vol_shocks:
            # Dummy values; replace with real repricing
            pv = 0.0
            pnl = 0.0
            components = {"options": 0.0, "fx": 0.0}
            points.append(ScenarioPoint(
                spot_shock=spot_shock,
                vol_shock=vol_shock,
                pv=pv,
                pnl=pnl,
                components=components
            ))
    resp = ScenarioResponse(points=points, hash_key=hash_key, cache_hit=False)
    if req.use_cache:
        cache.set(hash_key, resp)
    return resp
