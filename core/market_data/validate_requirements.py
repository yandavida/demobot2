from typing import Optional, Dict, List

from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.commands.compute_request_command import ComputeRequestPayload
from core.validation.error_envelope import ErrorEnvelope


def _mk(code: str, message: str, details: Optional[Dict[str, str]] = None) -> ErrorEnvelope:
    return ErrorEnvelope(category="SEMANTIC", code=code, message=message, details=details or {})


def validate_market_requirements(
    request: ComputeRequestPayload, snapshot: MarketSnapshotPayloadV0
) -> Optional[ErrorEnvelope]:
    """Validate market requirements for a compute request against a MarketSnapshotPayloadV0.

    Returns an ErrorEnvelope with category=SEMANTIC when a requirement is violated, otherwise None.
    The function is deterministic and side-effect free.
    """
    params = request.params if isinstance(request, ComputeRequestPayload) else {}

    # Symbols: expect list under 'symbols'
    symbols: List[str] | None = params.get("symbols") if isinstance(params.get("symbols"), list) else None
    if symbols:
        for sym in symbols:
            if sym not in snapshot.spots.prices:
                return _mk("UNKNOWN_SYMBOL_IN_SNAPSHOT", "A referenced symbol is missing in snapshot", {"symbol": sym})
            if sym not in snapshot.spots.currency:
                return _mk("MISSING_SPOT_CURRENCY", "Spot currency mapping missing for symbol in snapshot", {"symbol": sym})

    # FX: base currency conversion requirements
    base_ccy = params.get("base_ccy") or params.get("base_currency")
    if base_ccy and symbols:
        for sym in symbols:
            sym_ccy = snapshot.spots.currency.get(sym)
            if sym_ccy is None:
                # already handled above, but be defensive
                return _mk("MISSING_SPOT_CURRENCY", "Spot currency mapping missing for symbol in snapshot", {"symbol": sym})
            if sym_ccy != base_ccy:
                # require explicit FX pair sym_ccy/base_ccy
                pair = f"{sym_ccy}/{base_ccy}"
                if pair not in snapshot.fx_rates.quotes:
                    return _mk("MISSING_FX_PAIR", "Required FX pair is missing in snapshot", {"pair": pair})

    # Curves: required_curves list and optional tenors mapping
    req_curves = params.get("required_curves") if isinstance(params.get("required_curves"), list) else None
    if req_curves:
        for ccy in req_curves:
            if ccy not in snapshot.curves.curves:
                return _mk("MISSING_CURVE", "Required discounting curve missing in snapshot", {"ccy": ccy})

    tenors = params.get("tenors") if isinstance(params.get("tenors"), dict) else None
    if tenors:
        for ccy, tenor_list in tenors.items():
            if ccy not in snapshot.curves.curves:
                return _mk("MISSING_CURVE", "Required discounting curve missing in snapshot", {"ccy": ccy})
            curve = snapshot.curves.curves[ccy]
            for t in tenor_list:
                if t not in curve.zero_rates:
                    return _mk("MISSING_TENOR", "Requested tenor missing in snapshot curve", {"ccy": ccy, "tenor": t})

    return None
