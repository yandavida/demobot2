import datetime
import inspect
import re

import pytest

from core import numeric_policy
from core.pricing.fx import swap_mtm
from core.pricing.fx.types import FxMarketSnapshot


def _price_tol():
    return numeric_policy.DEFAULT_TOLERANCES[numeric_policy.MetricClass.PRICE]


def _approx_equal(a: float, b: float) -> bool:
    tol = _price_tol()
    abs_diff = abs(a - b)
    if abs_diff <= tol.abs:
        return True
    rel_diff = abs_diff / max(abs(a), abs(b), 1e-9)
    return rel_diff <= tol.rel


def _as_of_ts() -> datetime.datetime:
    return datetime.datetime(2026, 2, 17, 16, 0, 0, tzinfo=datetime.timezone.utc)


def _near_leg(*, notional: float, direction: str, forward_rate: float, settlement_date: datetime.date):
    return swap_mtm.FxSwapLeg(
        forward_rate=forward_rate,
        direction=direction,
        settlement_date=settlement_date,
    )


def _far_leg(*, notional: float, direction: str, forward_rate: float, settlement_date: datetime.date):
    return swap_mtm.FxSwapLeg(
        forward_rate=forward_rate,
        direction=direction,
        settlement_date=settlement_date,
    )


def _contract(*, notional: float, near: swap_mtm.FxSwapLeg, far: swap_mtm.FxSwapLeg) -> swap_mtm.FxSwapContract:
    return swap_mtm.FxSwapContract(
        base_ccy="USD",
        quote_ccy="ILS",
        notional_foreign=notional,
        near=near,
        far=far,
    )


def _near_market(as_of_ts: datetime.datetime) -> FxMarketSnapshot:
    return FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=3.70,
        df_domestic=0.995,
        df_foreign=0.998,
    )


def _far_market(as_of_ts: datetime.datetime) -> FxMarketSnapshot:
    return FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=3.71,
        df_domestic=0.985,
        df_foreign=0.992,
    )


def test_swap_determinism_same_inputs_identical_outputs():
    as_of_ts = _as_of_ts()
    near = _near_leg(
        notional=1_000_000.0,
        direction="receive_foreign_pay_domestic",
        forward_rate=3.72,
        settlement_date=datetime.date(2026, 3, 15),
    )
    far = _far_leg(
        notional=1_000_000.0,
        direction="pay_foreign_receive_domestic",
        forward_rate=3.74,
        settlement_date=datetime.date(2026, 6, 15),
    )
    contract = _contract(notional=1_000_000.0, near=near, far=far)
    near_mkt = _near_market(as_of_ts)
    far_mkt = _far_market(as_of_ts)

    result_1 = swap_mtm.price_fx_swap(
        as_of_ts=as_of_ts,
        contract=contract,
        market_near=near_mkt,
        market_far=far_mkt,
    )
    result_2 = swap_mtm.price_fx_swap(
        as_of_ts=as_of_ts,
        contract=contract,
        market_near=near_mkt,
        market_far=far_mkt,
    )

    assert result_1.pv == result_2.pv
    assert result_1.details == result_2.details


def test_swap_parity_zero_when_both_legs_at_market():
    as_of_ts = _as_of_ts()
    near_mkt = _near_market(as_of_ts)
    far_mkt = _far_market(as_of_ts)

    f_mkt_near = near_mkt.spot_rate * near_mkt.df_foreign / near_mkt.df_domestic
    f_mkt_far = far_mkt.spot_rate * far_mkt.df_foreign / far_mkt.df_domestic

    near = _near_leg(
        notional=1_000_000.0,
        direction="receive_foreign_pay_domestic",
        forward_rate=f_mkt_near,
        settlement_date=datetime.date(2026, 3, 15),
    )
    far = _far_leg(
        notional=1_000_000.0,
        direction="pay_foreign_receive_domestic",
        forward_rate=f_mkt_far,
        settlement_date=datetime.date(2026, 6, 15),
    )
    contract = _contract(notional=1_000_000.0, near=near, far=far)

    result = swap_mtm.price_fx_swap(
        as_of_ts=as_of_ts,
        contract=contract,
        market_near=near_mkt,
        market_far=far_mkt,
    )

    assert _approx_equal(result.pv, 0.0)


def test_swap_linearity_double_notional_doubles_pv():
    as_of_ts = _as_of_ts()
    near = _near_leg(
        notional=1_000_000.0,
        direction="receive_foreign_pay_domestic",
        forward_rate=3.72,
        settlement_date=datetime.date(2026, 3, 15),
    )
    far = _far_leg(
        notional=1_000_000.0,
        direction="pay_foreign_receive_domestic",
        forward_rate=3.74,
        settlement_date=datetime.date(2026, 6, 15),
    )
    contract_1x = _contract(notional=1_000_000.0, near=near, far=far)
    contract_2x = _contract(notional=2_000_000.0, near=near, far=far)

    near_mkt = _near_market(as_of_ts)
    far_mkt = _far_market(as_of_ts)

    result_1x = swap_mtm.price_fx_swap(
        as_of_ts=as_of_ts,
        contract=contract_1x,
        market_near=near_mkt,
        market_far=far_mkt,
    )
    result_2x = swap_mtm.price_fx_swap(
        as_of_ts=as_of_ts,
        contract=contract_2x,
        market_near=near_mkt,
        market_far=far_mkt,
    )

    assert _approx_equal(result_2x.pv, 2.0 * result_1x.pv)


def test_swap_symmetry_flip_both_legs_directions_flips_sign():
    as_of_ts = _as_of_ts()
    near = _near_leg(
        notional=1_000_000.0,
        direction="receive_foreign_pay_domestic",
        forward_rate=3.72,
        settlement_date=datetime.date(2026, 3, 15),
    )
    far = _far_leg(
        notional=1_000_000.0,
        direction="pay_foreign_receive_domestic",
        forward_rate=3.74,
        settlement_date=datetime.date(2026, 6, 15),
    )
    near_flip = _near_leg(
        notional=1_000_000.0,
        direction="pay_foreign_receive_domestic",
        forward_rate=3.72,
        settlement_date=datetime.date(2026, 3, 15),
    )
    far_flip = _far_leg(
        notional=1_000_000.0,
        direction="receive_foreign_pay_domestic",
        forward_rate=3.74,
        settlement_date=datetime.date(2026, 6, 15),
    )

    contract = _contract(notional=1_000_000.0, near=near, far=far)
    contract_flip = _contract(notional=1_000_000.0, near=near_flip, far=far_flip)

    near_mkt = _near_market(as_of_ts)
    far_mkt = _far_market(as_of_ts)

    result = swap_mtm.price_fx_swap(
        as_of_ts=as_of_ts,
        contract=contract,
        market_near=near_mkt,
        market_far=far_mkt,
    )
    result_flip = swap_mtm.price_fx_swap(
        as_of_ts=as_of_ts,
        contract=contract_flip,
        market_near=near_mkt,
        market_far=far_mkt,
    )

    assert _approx_equal(result_flip.pv, -result.pv)
    assert _approx_equal(abs(result_flip.pv), abs(result.pv))


def test_swap_contract_date_order_guard_raises_value_error():
    with pytest.raises(ValueError, match="near.settlement_date"):
        _contract(
            notional=1_000_000.0,
            near=_near_leg(
                notional=1_000_000.0,
                direction="receive_foreign_pay_domestic",
                forward_rate=3.72,
                settlement_date=datetime.date(2026, 6, 15),
            ),
            far=_far_leg(
                notional=1_000_000.0,
                direction="pay_foreign_receive_domestic",
                forward_rate=3.74,
                settlement_date=datetime.date(2026, 6, 15),
            ),
        )


def test_swap_missing_market_df_rejection_raises_value_error():
    as_of_ts = _as_of_ts()
    contract = _contract(
        notional=1_000_000.0,
        near=_near_leg(
            notional=1_000_000.0,
            direction="receive_foreign_pay_domestic",
            forward_rate=3.72,
            settlement_date=datetime.date(2026, 3, 15),
        ),
        far=_far_leg(
            notional=1_000_000.0,
            direction="pay_foreign_receive_domestic",
            forward_rate=3.74,
            settlement_date=datetime.date(2026, 6, 15),
        ),
    )
    near_mkt = FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=3.70,
        df_domestic=None,
        df_foreign=0.998,
    )
    far_mkt = _far_market(as_of_ts)

    with pytest.raises(ValueError, match="df_domestic"):
        swap_mtm.price_fx_swap(
            as_of_ts=as_of_ts,
            contract=contract,
            market_near=near_mkt,
            market_far=far_mkt,
        )


def test_swap_contract_validation_currency_mismatch_raises():
    near = _near_leg(
        notional=1_000_000.0,
        direction="receive_foreign_pay_domestic",
        forward_rate=3.72,
        settlement_date=datetime.date(2026, 3, 15),
    )
    far = _far_leg(
        notional=1_000_000.0,
        direction="pay_foreign_receive_domestic",
        forward_rate=3.74,
        settlement_date=datetime.date(2026, 6, 15),
    )

    with pytest.raises(ValueError, match="base_ccy"):
        swap_mtm.FxSwapContract(
            base_ccy="USD",
            quote_ccy="USD",
            notional_foreign=1_000_000.0,
            near=near,
            far=far,
        )


def test_swap_architecture_firewall_no_forbidden_substrings():
    source = inspect.getsource(swap_mtm)
    forbidden = [
        "core." + "a" + "pi",
        "a" + "pi.",
        "life" + "cycle",
        "cu" + "rve",
        "boot" + "strap",
        "inter" + "polation",
        "zero_" + "rate",
        "zero_" + "rates",
        "ra" + "te",
        "com" + "pounding",
        "day" + "count",
        "year_" + "fraction",
        "exp(",
        "log(",
    ]

    for token in forbidden:
        if token == ("ra" + "te"):
            assert re.search(r"\brate\b", source) is None
        else:
            assert token not in source


def test_swap_domestic_pv_unit_sanity_check():
    # PV is returned by forward engine in domestic (quote) currency units.
    as_of_ts = _as_of_ts()
    near = _near_leg(
        notional=1_000_000.0,
        direction="receive_foreign_pay_domestic",
        forward_rate=3.72,
        settlement_date=datetime.date(2026, 3, 15),
    )
    far = _far_leg(
        notional=1_000_000.0,
        direction="pay_foreign_receive_domestic",
        forward_rate=3.74,
        settlement_date=datetime.date(2026, 6, 15),
    )
    contract = _contract(notional=1_000_000.0, near=near, far=far)
    result = swap_mtm.price_fx_swap(
        as_of_ts=as_of_ts,
        contract=contract,
        market_near=_near_market(as_of_ts),
        market_far=_far_market(as_of_ts),
    )

    # With quote_ccy="ILS", returned PV should be ILS-valued scalar from the forward formula composition.
    assert isinstance(result.pv, float)
