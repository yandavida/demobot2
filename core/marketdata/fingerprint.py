import json
import hashlib
from .schemas import MarketSnapshot

def market_snapshot_to_canonical_dict(snapshot: MarketSnapshot) -> dict:
    # asof as ISO string
    return {
        "asof": snapshot.asof.isoformat() if hasattr(snapshot.asof, 'isoformat') else str(snapshot.asof),
        "spots": dict(sorted(snapshot.spots.items())),
        "vols": dict(sorted(snapshot.vols.items())),
        "rates": dict(sorted(snapshot.rates.items())),
        "divs": dict(sorted(snapshot.divs.items())),
        "fx_spots": dict(sorted(snapshot.fx_spots.items())),
        "fx_forwards": dict(sorted(snapshot.fx_forwards.items())),
    }

def market_snapshot_fingerprint(snapshot: MarketSnapshot) -> str:
    d = market_snapshot_to_canonical_dict(snapshot)
    s = json.dumps(d, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode()).hexdigest()
