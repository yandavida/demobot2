from typing import Optional
import re
import math

from core.validation.error_envelope import ErrorEnvelope
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
        return ErrorEnvelope(category="VALIDATION", code="fx_missing_base_pair", message=f"base pair {base_key} missing", details={"base": base})
    if not math.isclose(quotes[base_key], 1.0, rel_tol=1e-12):
        return ErrorEnvelope(category="VALIDATION", code="fx_base_not_one", message=f"{base_key} must equal 1.0", details={"value": quotes[base_key]})

    # 2. FX symmetry
    for pair, rate in quotes.items():
        if "/" not in pair:
            return ErrorEnvelope(category="VALIDATION", code="fx_invalid_pair_format", message=f"invalid pair format: {pair}", details={})
        a, b = pair.split("/")
        inv = f"{b}/{a}"
        if inv not in quotes:
            return ErrorEnvelope(category="VALIDATION", code="fx_missing_inverse", message=f"missing inverse for {pair}", details={"missing": inv})
        if not _is_reciprocal(rate, quotes[inv]):
            return ErrorEnvelope(category="VALIDATION", code="fx_not_reciprocal", message=f"rates for {pair} and {inv} not reciprocal", details={"pair": pair, "rate": rate, "inverse": quotes[inv]})

    # 3. Spots currency mapping
    for sym in snapshot.spots.prices.keys():
        if sym not in snapshot.spots.currency:
            return ErrorEnvelope(category="VALIDATION", code="spot_missing_currency", message=f"currency mapping missing for symbol {sym}", details={"symbol": sym})

    # 4. Curves tenor validation
    for ccy, curve in snapshot.curves.curves.items():
        for tenor in curve.zero_rates.keys():
            if not TENOR_RE.match(tenor):
                return ErrorEnvelope(category="VALIDATION", code="curve_invalid_tenor", message=f"invalid tenor {tenor} on curve {ccy}", details={"tenor": tenor, "ccy": ccy})

    # 5. Vol surfaces v0 restrictions
    if snapshot.vols is not None:
        for name, surf in snapshot.vols.surfaces.items():
            if surf.type != "flat":
                return ErrorEnvelope(category="VALIDATION", code="volsurface_type_not_allowed", message=f"vol surface type {surf.type} not allowed in v0", details={"surface": name, "type": surf.type})
            # for flat expect data to contain 'vol' numeric
            if not isinstance(surf.data, dict) or "vol" not in surf.data:
                return ErrorEnvelope(category="VALIDATION", code="volsurface_flat_invalid", message=f"flat vol surface {name} missing 'vol'", details={"surface": name})
            if not isinstance(surf.data["vol"], (int, float)):
                return ErrorEnvelope(category="VALIDATION", code="volsurface_flat_invalid_type", message=f"flat vol 'vol' must be numeric for {name}", details={"surface": name, "value": surf.data.get("vol")})

    # All checks passed
    return None
