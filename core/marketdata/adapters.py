from typing import Sequence
from .schemas import Quote, MarketSnapshot

def build_market_snapshot_v1(asof, quotes: Sequence[Quote]) -> MarketSnapshot:
    # Deterministic: sort by (kind, key)
    sorted_quotes = sorted(quotes, key=lambda q: (q.kind, q.key))
    seen = set()
    spots = {}
    vols = {}
    rates = {}
    divs = {}
    fx_spots = {}
    fx_forwards = {}
    for q in sorted_quotes:
        k = (q.kind, q.key)
        if k in seen:
            raise ValueError(f"Duplicate quote for kind={q.kind}, key={q.key}")
        seen.add(k)
        if q.kind == "spot":
            spots[q.key] = q.value
        elif q.kind == "vol":
            vols[q.key] = q.value
        elif q.kind == "rate":
            rates[q.key] = q.value
        elif q.kind == "div":
            divs[q.key] = q.value
        elif q.kind == "fx_spot":
            fx_spots[q.key] = q.value
        elif q.kind == "fx_forward":
            fx_forwards[q.key] = q.value
        else:
            raise ValueError(f"Unknown quote kind: {q.kind}")
    return MarketSnapshot(
        asof=asof,
        spots=spots,
        vols=vols,
        rates=rates,
        divs=divs,
        fx_spots=fx_spots,
        fx_forwards=fx_forwards,
    )

def validate_required_for_symbols(snapshot: MarketSnapshot, symbols: Sequence[str]) -> None:
    missing = []
    for sym in symbols:
        if sym not in snapshot.spots:
            missing.append(f"spot:{sym}")
        if sym not in snapshot.vols:
            missing.append(f"vol:{sym}")
    if missing:
        raise ValueError(f"Missing required market data: {', '.join(missing)}")
    # divs: missing is allowed (defaults to 0.0 in pricing path)
    # rates: do not default, error if missing and required by pricing path
