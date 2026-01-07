from typing import Optional
import re
import math

from api.v2.gate_b import ErrorEnvelope
from .market_snapshot_payload_v0 import MarketSnapshotPayloadV0


TENOR_RE = re.compile(r"^\d+(D|W|M|Y)$")


def _is_reciprocal(a: float, b: float, rel_tol: float = 1e-9) -> bool:
    if a == 0 or b == 0:
        return False
    return math.isclose(a * b, 1.0, rel_tol=rel_tol)


def validate_market_snapshot_v0(snapshot: MarketSnapshotPayloadV0) -> Optional[ErrorEnvelope]:
    # Structural presence already guaranteed by pydantic model; perform semantic checks in deterministic order.

    # 1. FX base rule
    base = snapshot.fx_rates.base_ccy
    base_key = f"{base}/{base}"
    quotes = snapshot.fx_rates.quotes
    if base_key not in quotes:
        return ErrorEnvelope("validation", "fx_missing_base_pair", f"base pair {base_key} missing", {"base": base})
    if not math.isclose(quotes[base_key], 1.0, rel_tol=1e-12):
        return ErrorEnvelope("validation", "fx_base_not_one", f"{base_key} must equal 1.0", {"value": quotes[base_key]})

    # 2. FX symmetry
    for pair, rate in quotes.items():
        if "/" not in pair:
            return ErrorEnvelope("validation", "fx_invalid_pair_format", f"invalid pair format: {pair}", {})
        a, b = pair.split("/")
        inv = f"{b}/{a}"
        if inv not in quotes:
            return ErrorEnvelope("validation", "fx_missing_inverse", f"missing inverse for {pair}", {"missing": inv})
        if not _is_reciprocal(rate, quotes[inv]):
            return ErrorEnvelope("validation", "fx_not_reciprocal", f"rates for {pair} and {inv} not reciprocal", {"pair": pair, "rate": rate, "inverse": quotes[inv]})

    # 3. Spots currency mapping
    for sym in snapshot.spots.prices.keys():
        if sym not in snapshot.spots.currency:
            return ErrorEnvelope("validation", "spot_missing_currency", f"currency mapping missing for symbol {sym}", {"symbol": sym})

    # 4. Curves tenor validation
    for ccy, curve in snapshot.curves.curves.items():
        for tenor in curve.zero_rates.keys():
            if not TENOR_RE.match(tenor):
                return ErrorEnvelope("validation", "curve_invalid_tenor", f"invalid tenor {tenor} on curve {ccy}", {"tenor": tenor, "ccy": ccy})

    # 5. Vol surfaces v0 restrictions
    if snapshot.vols is not None:
        for name, surf in snapshot.vols.surfaces.items():
            if surf.type != "flat":
                return ErrorEnvelope("validation", "volsurface_type_not_allowed", f"vol surface type {surf.type} not allowed in v0", {"surface": name, "type": surf.type})
            # for flat expect data to contain 'vol' numeric
            if not isinstance(surf.data, dict) or "vol" not in surf.data:
                return ErrorEnvelope("validation", "volsurface_flat_invalid", f"flat vol surface {name} missing 'vol'", {"surface": name})
            if not isinstance(surf.data["vol"], (int, float)):
                return ErrorEnvelope("validation", "volsurface_flat_invalid_type", f"flat vol 'vol' must be numeric for {name}", {"surface": name, "value": surf.data.get("vol")})

    # All checks passed
    return None
