from __future__ import annotations

import datetime

from core.market_data.artifact_store import get_market_snapshot
from core.market_data.df_lookup_v0 import DfLookupError
from core.market_data.df_lookup_v0 import get_pair_dfs_v0
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.pricing.fx.types import FxMarketSnapshot


class SnapshotResolutionError(ValueError):
    pass


_FIXED_AS_OF_TS = datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)


def convert_market_snapshot_payload_v0_to_fx_snapshot_v1(payload: MarketSnapshotPayloadV0) -> FxMarketSnapshot:
    base_ccy = str(payload.fx_rates.base_ccy).strip().upper()
    if not base_ccy:
        raise SnapshotResolutionError("invalid_market_snapshot_payload: empty fx_rates.base_ccy")

    quote_keys = sorted(str(key).strip().upper() for key in payload.fx_rates.quotes.keys())
    if not quote_keys:
        raise SnapshotResolutionError("invalid_market_snapshot_payload: missing fx_rates.quotes")

    domestic_ccy = quote_keys[0]
    raw_spot = payload.fx_rates.quotes.get(domestic_ccy)
    if raw_spot is None:
        raise SnapshotResolutionError("invalid_market_snapshot_payload: missing deterministic spot quote")

    try:
        spot = float(raw_spot)
    except (TypeError, ValueError) as exc:
        raise SnapshotResolutionError("invalid_market_snapshot_payload: spot quote must be numeric") from exc

    try:
        df_domestic, df_foreign = get_pair_dfs_v0(
            payload,
            domestic_ccy=domestic_ccy,
            foreign_ccy=base_ccy,
            ttm_years=1.0,
        )
    except DfLookupError as exc:
        raise SnapshotResolutionError(f"invalid_market_snapshot_payload: {exc}") from exc

    return FxMarketSnapshot(
        as_of_ts=_FIXED_AS_OF_TS,
        spot_rate=spot,
        df_domestic=df_domestic,
        df_foreign=df_foreign,
        domestic_currency=domestic_ccy,
    )


def resolve_fx_market_snapshot_v1(snapshot_id: str) -> FxMarketSnapshot:
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        raise SnapshotResolutionError("invalid_market_snapshot_id")

    try:
        payload = get_market_snapshot(snapshot_id.strip())
    except Exception as exc:
        raise SnapshotResolutionError(f"unknown_market_snapshot_id:{snapshot_id}") from exc

    return convert_market_snapshot_payload_v0_to_fx_snapshot_v1(payload)


__all__ = [
    "SnapshotResolutionError",
    "convert_market_snapshot_payload_v0_to_fx_snapshot_v1",
    "resolve_fx_market_snapshot_v1",
]
