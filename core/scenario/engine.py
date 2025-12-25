import json
import hashlib
from typing import Any, Sequence, Optional
from .schemas import ScenarioRequest, ScenarioResponse, ScenarioPoint
from .cache import ScenarioCache, DEFAULT_SCENARIO_CACHE

MODEL_VERSION = "scenario_v1_fullrepricing"

# --- Stable hashing ---
def build_scenario_hash_key(req: ScenarioRequest) -> str:
    def sorted_positions(positions: Sequence[Any]):
        # If positions have a unique id or can be sorted, sort deterministically
        # Otherwise, sort by str()
        try:
            return sorted(positions, key=lambda p: getattr(p, 'id', str(p)))
        except Exception:
            return sorted(positions, key=lambda p: str(p))

    payload = {
        "positions": [json.loads(json.dumps(p, default=lambda o: o.__dict__, sort_keys=True)) for p in sorted_positions(req.positions)],
        "market": {
            k: dict(sorted(getattr(req.market, k).items()))
            for k in req.market.__dataclass_fields__
        },
        "spot_shocks": list(req.spot_shocks),
        "vol_shocks": list(req.vol_shocks),
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
    # For now, return dummy points for structure
    points = []
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
