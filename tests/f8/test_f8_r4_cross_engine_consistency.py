from __future__ import annotations

import datetime
from dataclasses import dataclass

from core import numeric_policy
from core.pricing.fx import forward_mtm
from core.pricing.fx import swap_mtm
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext


PRICE_TOL = numeric_policy.DEFAULT_TOLERANCES[numeric_policy.MetricClass.PRICE]
ABS_TOL = max(PRICE_TOL.abs or 0.0, 1e-8)


@dataclass(frozen=True)
class _Case:
    case_id: str
    spot_near: float
    dfd_near: float
    dff_near: float
    spot_far: float
    dfd_far: float
    dff_far: float
    far_strike: float
    direction: str
    notional: float
    near_days: int
    far_days: int


def _as_of() -> datetime.datetime:
    return datetime.datetime(2026, 3, 2, 12, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))


def _ctx() -> ValuationContext:
    return ValuationContext(as_of_ts=_as_of(), domestic_currency="ILS", strict_mode=True)


def _forward_market(spot: float, dfd: float, dff: float) -> float:
    return spot * dff / dfd


def _near_neutral_rate(case: _Case) -> float:
    return _forward_market(case.spot_near, case.dfd_near, case.dff_near)


def _near_snapshot(case: _Case) -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=_as_of(),
        spot_rate=case.spot_near,
        df_domestic=case.dfd_near,
        df_foreign=case.dff_near,
    )


def _far_snapshot(case: _Case) -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=_as_of(),
        spot_rate=case.spot_far,
        df_domestic=case.dfd_far,
        df_foreign=case.dff_far,
    )


def _settlement(base: datetime.datetime, days: int) -> datetime.date:
    return (base + datetime.timedelta(days=days)).date()


def _swap_contract_far_only(case: _Case) -> swap_mtm.FxSwapContract:
    near_leg = swap_mtm.FxSwapLeg(
        forward_rate=_near_neutral_rate(case),
        direction=case.direction,
        settlement_date=_settlement(_as_of(), case.near_days),
    )
    far_leg = swap_mtm.FxSwapLeg(
        forward_rate=case.far_strike,
        direction=case.direction,
        settlement_date=_settlement(_as_of(), case.far_days),
    )
    return swap_mtm.FxSwapContract(
        base_ccy="USD",
        quote_ccy="ILS",
        notional_foreign=case.notional,
        near=near_leg,
        far=far_leg,
    )


def _far_forward_contract(case: _Case) -> fx_types.FXForwardContract:
    return fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="ILS",
        notional=case.notional,
        forward_date=_settlement(_as_of(), case.far_days),
        forward_rate=case.far_strike,
        direction=case.direction,
    )


def _near_forward_contract(case: _Case) -> fx_types.FXForwardContract:
    return fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="ILS",
        notional=case.notional,
        forward_date=_settlement(_as_of(), case.near_days),
        forward_rate=_near_neutral_rate(case),
        direction=case.direction,
    )


def _assert_close(a: float, b: float, tol: float = ABS_TOL) -> None:
    assert abs(a - b) <= tol


CASES = (
    _Case("atm_1m", 3.64, 0.9950, 0.9982, 3.64, 0.9900, 0.9960, 3.66, "receive_foreign_pay_domestic", 1_000_000.0, 7, 31),
    _Case("deep_itm", 3.70, 0.9850, 0.9930, 3.71, 0.9750, 0.9900, 3.50, "receive_foreign_pay_domestic", 2_000_000.0, 14, 90),
    _Case("deep_otm", 3.68, 0.9865, 0.9925, 3.67, 0.9775, 0.9895, 3.95, "receive_foreign_pay_domestic", 1_500_000.0, 10, 90),
    _Case("extreme_low_dfd", 3.64, 0.0001, 1.0001, 3.64, 0.0100, 0.9900, 3.80, "pay_foreign_receive_domestic", 1_200_000.0, 5, 120),
    _Case("extreme_low_dff", 3.64, 1.0001, 0.0001, 3.64, 0.9800, 0.0100, 3.55, "pay_foreign_receive_domestic", 900_000.0, 4, 60),
)


def test_r4_t1_forward_equals_swap_far_only_matrix():
    for case in CASES:
        swap_contract = _swap_contract_far_only(case)
        near_snapshot = _near_snapshot(case)
        far_snapshot = _far_snapshot(case)

        swap_result = swap_mtm.price_fx_swap_ctx(_ctx(), swap_contract, near_snapshot, far_snapshot)

        forward_result = forward_mtm.price_fx_forward_ctx(
            context=_ctx(),
            contract=_far_forward_contract(case),
            market_snapshot=far_snapshot,
            conventions=None,
        )

        _assert_close(swap_result.pv, forward_result.pv)
        assert swap_result.currency == _ctx().domestic_currency
        assert forward_result.currency == _ctx().domestic_currency
        assert swap_result.metric_class == numeric_policy.MetricClass.PRICE
        assert forward_result.metric_class == numeric_policy.MetricClass.PRICE


def test_r4_t2_swap_decomposition_matrix():
    for case in CASES:
        swap_contract = _swap_contract_far_only(case)
        near_snapshot = _near_snapshot(case)
        far_snapshot = _far_snapshot(case)

        total_result = swap_mtm.price_fx_swap_ctx(_ctx(), swap_contract, near_snapshot, far_snapshot)

        near_result = forward_mtm.price_fx_forward_ctx(
            context=_ctx(),
            contract=_near_forward_contract(case),
            market_snapshot=near_snapshot,
            conventions=None,
        )
        far_result = forward_mtm.price_fx_forward_ctx(
            context=_ctx(),
            contract=_far_forward_contract(case),
            market_snapshot=far_snapshot,
            conventions=None,
        )

        _assert_close(total_result.pv, near_result.pv + far_result.pv)


def test_r4_t4_direction_flip_antisymmetry_cross_engine():
    case = CASES[0]

    swap_contract_a = _swap_contract_far_only(case)
    near_snapshot = _near_snapshot(case)
    far_snapshot = _far_snapshot(case)

    swap_a = swap_mtm.price_fx_swap_ctx(_ctx(), swap_contract_a, near_snapshot, far_snapshot)
    fwd_a = forward_mtm.price_fx_forward_ctx(
        context=_ctx(),
        contract=_far_forward_contract(case),
        market_snapshot=far_snapshot,
        conventions=None,
    )

    flipped_direction = "pay_foreign_receive_domestic"
    if case.direction == "pay_foreign_receive_domestic":
        flipped_direction = "receive_foreign_pay_domestic"

    case_flip = _Case(
        case_id=f"{case.case_id}_flip",
        spot_near=case.spot_near,
        dfd_near=case.dfd_near,
        dff_near=case.dff_near,
        spot_far=case.spot_far,
        dfd_far=case.dfd_far,
        dff_far=case.dff_far,
        far_strike=case.far_strike,
        direction=flipped_direction,
        notional=case.notional,
        near_days=case.near_days,
        far_days=case.far_days,
    )

    swap_b = swap_mtm.price_fx_swap_ctx(_ctx(), _swap_contract_far_only(case_flip), near_snapshot, far_snapshot)
    fwd_b = forward_mtm.price_fx_forward_ctx(
        context=_ctx(),
        contract=_far_forward_contract(case_flip),
        market_snapshot=far_snapshot,
        conventions=None,
    )

    _assert_close(fwd_a.pv, -fwd_b.pv)
    _assert_close(swap_a.pv, -swap_b.pv)
    _assert_close(swap_b.pv, fwd_b.pv)
