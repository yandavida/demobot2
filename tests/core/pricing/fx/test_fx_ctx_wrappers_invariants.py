import datetime

from core.pricing.fx import forward_mtm
from core.pricing.fx import swap_mtm
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext


def _as_of() -> datetime.datetime:
    return datetime.datetime(2026, 2, 22, 16, 0, 0, tzinfo=datetime.timezone.utc)


def _forward_contract() -> fx_types.FXForwardContract:
    return fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="ILS",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 5, 22),
        forward_rate=3.72,
        direction="receive_foreign_pay_domestic",
    )


def _forward_snapshot(as_of_ts: datetime.datetime) -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=3.70,
        df_domestic=0.995,
        df_foreign=0.998,
    )


def _swap_contract() -> swap_mtm.FxSwapContract:
    near = swap_mtm.FxSwapLeg(
        forward_rate=3.72,
        direction="receive_foreign_pay_domestic",
        settlement_date=datetime.date(2026, 3, 15),
    )
    far = swap_mtm.FxSwapLeg(
        forward_rate=3.74,
        direction="pay_foreign_receive_domestic",
        settlement_date=datetime.date(2026, 6, 15),
    )
    return swap_mtm.FxSwapContract(
        base_ccy="USD",
        quote_ccy="ILS",
        notional_foreign=1_000_000.0,
        near=near,
        far=far,
    )


def _near_snapshot(as_of_ts: datetime.datetime) -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=3.70,
        df_domestic=0.995,
        df_foreign=0.998,
    )


def _far_snapshot(as_of_ts: datetime.datetime) -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=3.71,
        df_domestic=0.985,
        df_foreign=0.992,
    )


def test_forward_ctx_wrapper_equals_legacy_when_timestamps_match():
    as_of = _as_of()
    ctx = ValuationContext(as_of_ts=as_of, domestic_currency="ILS", strict_mode=True)
    contract = _forward_contract()
    snapshot = _forward_snapshot(as_of)

    legacy = forward_mtm.price_fx_forward(as_of, contract, snapshot, None)
    ctx_result = forward_mtm.price_fx_forward_ctx(ctx, contract, snapshot, None)

    assert legacy == ctx_result


def test_forward_ctx_wrapper_mismatch_raises_exact_message():
    as_of = _as_of()
    other_as_of = datetime.datetime(2026, 2, 22, 16, 0, 1, tzinfo=datetime.timezone.utc)
    ctx = ValuationContext(as_of_ts=as_of, domestic_currency="ILS", strict_mode=True)
    contract = _forward_contract()
    snapshot = _forward_snapshot(other_as_of)

    try:
        forward_mtm.price_fx_forward_ctx(ctx, contract, snapshot, None)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "market_snapshot.as_of_ts must equal context.as_of_ts"


def test_swap_ctx_wrapper_equals_legacy_when_timestamps_match():
    as_of = _as_of()
    ctx = ValuationContext(as_of_ts=as_of, domestic_currency="ILS", strict_mode=True)

    contract = _swap_contract()
    near_snapshot = _near_snapshot(as_of)
    far_snapshot = _far_snapshot(as_of)

    legacy = swap_mtm.price_fx_swap(as_of, contract, near_snapshot, far_snapshot)
    ctx_result = swap_mtm.price_fx_swap_ctx(ctx, contract, near_snapshot, far_snapshot)

    assert legacy == ctx_result


def test_swap_ctx_wrapper_mismatch_raises_exact_message():
    as_of = _as_of()
    other_as_of = datetime.datetime(2026, 2, 22, 16, 0, 2, tzinfo=datetime.timezone.utc)
    ctx = ValuationContext(as_of_ts=as_of, domestic_currency="ILS", strict_mode=True)

    contract = _swap_contract()
    near_snapshot = _near_snapshot(as_of)
    far_snapshot = _far_snapshot(other_as_of)

    try:
        swap_mtm.price_fx_swap_ctx(ctx, contract, near_snapshot, far_snapshot)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "swap snapshots as_of_ts must equal context.as_of_ts"
