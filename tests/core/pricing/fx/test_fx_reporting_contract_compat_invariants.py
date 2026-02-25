import datetime

import pytest

from core import numeric_policy
from core.pricing.fx import forward_mtm
from core.pricing.fx import swap_mtm
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext


def _as_of() -> datetime.datetime:
    return datetime.datetime(2026, 2, 25, 12, 0, 0, tzinfo=datetime.timezone.utc)


def _forward_contract() -> fx_types.FXForwardContract:
    return fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="ILS",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 5, 25),
        forward_rate=3.72,
        direction="receive_foreign_pay_domestic",
    )


def _snapshot(as_of_ts: datetime.datetime) -> fx_types.FxMarketSnapshot:
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
        settlement_date=datetime.date(2026, 3, 20),
    )
    far = swap_mtm.FxSwapLeg(
        forward_rate=3.74,
        direction="pay_foreign_receive_domestic",
        settlement_date=datetime.date(2026, 6, 20),
    )
    return swap_mtm.FxSwapContract(
        base_ccy="USD",
        quote_ccy="ILS",
        notional_foreign=1_000_000.0,
        near=near,
        far=far,
    )


def test_legacy_forward_no_conventions_uses_ils_and_does_not_raise():
    as_of = _as_of()

    result = forward_mtm.price_fx_forward(
        as_of_ts=as_of,
        contract=_forward_contract(),
        market_snapshot=_snapshot(as_of),
        conventions=None,
    )

    assert result.currency == "ILS"
    assert result.metric_class == numeric_policy.MetricClass.PRICE


def test_legacy_swap_no_conventions_uses_ils_and_does_not_raise():
    as_of = _as_of()

    result = swap_mtm.price_fx_swap(
        as_of_ts=as_of,
        contract=_swap_contract(),
        market_near=_snapshot(as_of),
        market_far=fx_types.FxMarketSnapshot(
            as_of_ts=as_of,
            spot_rate=3.71,
            df_domestic=0.985,
            df_foreign=0.992,
        ),
    )

    assert result.currency == "ILS"
    assert result.metric_class == numeric_policy.MetricClass.PRICE


def test_ctx_forward_currency_mismatch_raises_stable_message():
    as_of = _as_of()
    context = ValuationContext(as_of_ts=as_of, domestic_currency="USD", strict_mode=True)

    with pytest.raises(ValueError, match=r"reporting currency must equal context\.domestic_currency"):
        forward_mtm.price_fx_forward_ctx(
            context=context,
            contract=_forward_contract(),
            market_snapshot=_snapshot(as_of),
            conventions=None,
        )


def test_ctx_swap_currency_mismatch_raises_stable_message():
    as_of = _as_of()
    context = ValuationContext(as_of_ts=as_of, domestic_currency="USD", strict_mode=True)

    with pytest.raises(ValueError, match=r"reporting currency must equal context\.domestic_currency"):
        swap_mtm.price_fx_swap_ctx(
            context=context,
            swap_contract=_swap_contract(),
            near_snapshot=_snapshot(as_of),
            far_snapshot=fx_types.FxMarketSnapshot(
                as_of_ts=as_of,
                spot_rate=3.71,
                df_domestic=0.985,
                df_foreign=0.992,
            ),
            conventions=None,
        )


def test_reporting_contract_compat_determinism_same_inputs_same_outputs():
    as_of = _as_of()

    result_1 = forward_mtm.price_fx_forward(
        as_of_ts=as_of,
        contract=_forward_contract(),
        market_snapshot=_snapshot(as_of),
        conventions=None,
    )
    result_2 = forward_mtm.price_fx_forward(
        as_of_ts=as_of,
        contract=_forward_contract(),
        market_snapshot=_snapshot(as_of),
        conventions=None,
    )

    assert result_1 == result_2
