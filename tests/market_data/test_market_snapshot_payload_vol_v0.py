from __future__ import annotations

from core.market_data.market_snapshot_payload_v0 import Curve
from core.market_data.market_snapshot_payload_v0 import FxRates
from core.market_data.market_snapshot_payload_v0 import InterestRateCurves
from core.market_data.market_snapshot_payload_v0 import MarketConventions
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.market_snapshot_payload_v0 import SpotPrices
from core.market_data.market_snapshot_payload_v0 import VolLookupError
from core.market_data.market_snapshot_payload_v0 import VolSurface
from core.market_data.market_snapshot_payload_v0 import VolSurfaces
from core.market_data.market_snapshot_payload_v0 import get_vol
from core.market_data.market_snapshot_payload_v0 import make_vol_lookup_key
from core.vol.types import VolKey


def _base_payload(*, vols: VolSurfaces | None) -> MarketSnapshotPayloadV0:
    fx = FxRates(base_ccy="USD", quotes={"USD/USD": 1.0, "USD/ILS": 3.7, "ILS/USD": 1 / 3.7})
    spots = SpotPrices(prices={"AAPL": 150.0}, currency={"AAPL": "USD"})
    curve = Curve(day_count="ACT/365", compounding="annual", zero_rates={"1M": 0.01, "1Y": 0.02})
    curves = InterestRateCurves(curves={"USD": curve})
    conv = MarketConventions(calendar="NONE", day_count_default="ACT/365", spot_lag=2)
    return MarketSnapshotPayloadV0(fx_rates=fx, spots=spots, curves=curves, vols=vols, conventions=conv)


def test_payload_without_vols_is_backward_compatible() -> None:
    payload = _base_payload(vols=None)
    encoded = payload.model_dump_json()
    decoded = MarketSnapshotPayloadV0.model_validate_json(encoded)
    assert payload.model_dump() == decoded.model_dump()


def test_payload_with_keyed_vol_quotes_roundtrip_and_lookup() -> None:
    key = make_vol_lookup_key(VolKey(underlying="AAPL", expiry_t=0.5, strike=150.0, option_type="call"))
    vols = VolSurfaces(
        surfaces={
            "AAPL": VolSurface(type="flat", data={"vol": 0.25}),
            "OPTIONS": VolSurface(type="flat", data={"quotes": {key: 0.31}}),
        }
    )
    payload = _base_payload(vols=vols)

    encoded = payload.model_dump_json()
    decoded = MarketSnapshotPayloadV0.model_validate_json(encoded)
    assert payload.model_dump() == decoded.model_dump()

    looked_up = get_vol(decoded, VolKey(underlying="AAPL", expiry_t=0.5, strike=150.0, option_type="call"))
    assert looked_up == 0.31


def test_missing_vol_lookup_fails_explicitly_no_fallback() -> None:
    vols = VolSurfaces(surfaces={"OPTIONS": VolSurface(type="flat", data={"quotes": {}})})
    payload = _base_payload(vols=vols)

    try:
        get_vol(payload, VolKey(underlying="AAPL", expiry_t=1.0, strike=200.0, option_type="put"))
        assert False, "expected VolLookupError"
    except VolLookupError as exc:
        assert "vol not found" in str(exc)
