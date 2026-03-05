from __future__ import annotations

import datetime

import pytest

from core.market_data.artifact_store import put_market_snapshot
from core.market_data.fx_snapshot_resolver_v1 import SnapshotResolutionError
from core.market_data.fx_snapshot_resolver_v1 import convert_market_snapshot_payload_v0_to_fx_snapshot_v1
from core.market_data.fx_snapshot_resolver_v1 import resolve_fx_market_snapshot_v1
from core.market_data.market_snapshot_payload_v0 import Curve
from core.market_data.market_snapshot_payload_v0 import FxRates
from core.market_data.market_snapshot_payload_v0 import InterestRateCurves
from core.market_data.market_snapshot_payload_v0 import MarketConventions
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.market_snapshot_payload_v0 import SpotPrices


def _payload() -> MarketSnapshotPayloadV0:
    return MarketSnapshotPayloadV0(
        fx_rates=FxRates(base_ccy="USD", quotes={"ILS": 3.7}),
        spots=SpotPrices(prices={"USD/ILS": 3.7}, currency={"USD/ILS": "ILS"}),
        curves=InterestRateCurves(
            curves={
                "ILS": Curve(day_count="ACT/365", compounding="annual", zero_rates={"365D": 0.04}),
                "USD": Curve(day_count="ACT/365", compounding="annual", zero_rates={"365D": 0.03}),
            }
        ),
        conventions=MarketConventions(calendar="IL", day_count_default="ACT/365", spot_lag=2),
    )


def test_resolve_fx_market_snapshot_v1_from_artifact_store() -> None:
    payload = _payload()
    snapshot_id = put_market_snapshot(payload)

    s1 = resolve_fx_market_snapshot_v1(snapshot_id)
    s2 = resolve_fx_market_snapshot_v1(snapshot_id)

    assert s1 == s2
    assert s1.spot_rate == 3.7
    assert s1.df_domestic is not None and s1.df_domestic > 0.0
    assert s1.df_foreign is not None and s1.df_foreign > 0.0
    assert s1.domestic_currency == "ILS"
    assert s1.as_of_ts == datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)


def test_convert_payload_missing_quotes_raises() -> None:
    payload = MarketSnapshotPayloadV0(
        fx_rates=FxRates(base_ccy="USD", quotes={}),
        spots=SpotPrices(prices={}, currency={}),
        curves=InterestRateCurves(curves={}),
        conventions=MarketConventions(calendar="IL", day_count_default="ACT/365", spot_lag=2),
    )

    with pytest.raises(SnapshotResolutionError, match="missing fx_rates.quotes"):
        convert_market_snapshot_payload_v0_to_fx_snapshot_v1(payload)
