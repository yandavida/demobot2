from __future__ import annotations

import datetime
import math

from core import numeric_policy
from core.pricing.fx import forward_mtm
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext


PRICE_TOL = numeric_policy.DEFAULT_TOLERANCES[numeric_policy.MetricClass.PRICE]
ABS_TOL = PRICE_TOL.abs or 1e-8


def _as_of_ts() -> datetime.datetime:
    return datetime.datetime(2026, 3, 2, 12, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))


def _context() -> ValuationContext:
    return ValuationContext(as_of_ts=_as_of_ts(), domestic_currency="ILS", strict_mode=True)


def _contract(*, notional: float, strike: float, direction: str) -> fx_types.FXForwardContract:
    return fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="ILS",
        notional=notional,
        forward_date=datetime.date(2026, 4, 2),
        forward_rate=strike,
        direction=direction,
    )


def _snapshot(*, spot: float, dfd: float, dff: float) -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=_as_of_ts(),
        spot_rate=spot,
        df_domestic=dfd,
        df_foreign=dff,
    )


def _price(*, notional: float, strike: float, direction: str, spot: float, dfd: float, dff: float) -> float:
    result = forward_mtm.price_fx_forward_ctx(
        context=_context(),
        contract=_contract(notional=notional, strike=strike, direction=direction),
        market_snapshot=_snapshot(spot=spot, dfd=dfd, dff=dff),
        conventions=None,
    )
    return result.pv


def _assert_close(left: float, right: float, tol: float = ABS_TOL) -> None:
    assert abs(left - right) <= tol


def test_r2_i1_df_strict_positivity_enforcement():
    try:
        _snapshot(spot=3.64, dfd=0.0, dff=0.9982)
        assert False, "Expected ValueError for non-positive df_domestic"
    except ValueError as exc:
        assert "df_domestic must be positive" in str(exc)

    try:
        _snapshot(spot=3.64, dfd=0.995, dff=0.0)
        assert False, "Expected ValueError for non-positive df_foreign"
    except ValueError as exc:
        assert "df_foreign must be positive" in str(exc)


def test_r2_i2_notional_strict_positivity_enforcement():
    try:
        _contract(notional=0.0, strike=3.65, direction="receive_foreign_pay_domestic")
        assert False, "Expected ValueError for zero notional"
    except ValueError as exc:
        assert str(exc) == "notional must be positive"

    try:
        _contract(notional=-1.0, strike=3.65, direction="receive_foreign_pay_domestic")
        assert False, "Expected ValueError for negative notional"
    except ValueError as exc:
        assert str(exc) == "notional must be positive"


def test_r2_i3_notional_scaling_linearity():
    base = _price(
        notional=1_000_000.0,
        strike=3.65,
        direction="receive_foreign_pay_domestic",
        spot=3.64,
        dfd=0.995,
        dff=0.9982,
    )

    for scale in (0.1, 10.0, 100.0):
        scaled = _price(
            notional=1_000_000.0 * scale,
            strike=3.65,
            direction="receive_foreign_pay_domestic",
            spot=3.64,
            dfd=0.995,
            dff=0.9982,
        )
        _assert_close(scaled, base * scale)


def test_r2_i4_spot_shock_affine_linearity():
    strike = 3.65
    notional = 1_000_000.0
    direction = "receive_foreign_pay_domestic"
    dfd = 0.995
    dff = 0.9982

    s_mid = 3.64
    s_low = s_mid * 0.5
    s_high = s_mid * 2.0

    pv_low = _price(notional=notional, strike=strike, direction=direction, spot=s_low, dfd=dfd, dff=dff)
    pv_mid = _price(notional=notional, strike=strike, direction=direction, spot=s_mid, dfd=dfd, dff=dff)
    pv_high = _price(notional=notional, strike=strike, direction=direction, spot=s_high, dfd=dfd, dff=dff)

    slope_1 = (pv_mid - pv_low) / (s_mid - s_low)
    slope_2 = (pv_high - pv_mid) / (s_high - s_mid)

    _assert_close(slope_1, slope_2)


def test_r2_i5_direction_flip_antisymmetry():
    common = {
        "notional": 1_000_000.0,
        "strike": 3.65,
        "spot": 3.64,
        "dfd": 0.995,
        "dff": 0.9982,
    }

    pv_receive = _price(direction="receive_foreign_pay_domestic", **common)
    pv_pay = _price(direction="pay_foreign_receive_domestic", **common)

    _assert_close(pv_receive, -pv_pay)


def test_r2_i6_extreme_but_valid_df_robustness():
    df_cases = (
        (0.0001, 1.0001),
        (1.0001, 0.0001),
        (0.01, 0.99),
    )

    for dfd, dff in df_cases:
        pv = _price(
            notional=1_000_000.0,
            strike=3.65,
            direction="receive_foreign_pay_domestic",
            spot=3.64,
            dfd=dfd,
            dff=dff,
        )
        assert math.isfinite(pv)


def test_r2_i7_aggregation_linearity():
    cases = [
        (1_000_000.0, 3.64, 3.65, 0.9950, 0.9982, "receive_foreign_pay_domestic"),
        (2_000_000.0, 3.70, 3.55, 0.9850, 0.9930, "receive_foreign_pay_domestic"),
        (1_500_000.0, 3.68, 3.95, 0.9865, 0.9925, "receive_foreign_pay_domestic"),
        (1_200_000.0, 3.76, 3.82, 0.9350, 0.9550, "pay_foreign_receive_domestic"),
        (800_000.0, 3.64, 3.6405, 0.9999, 0.99995, "pay_foreign_receive_domestic"),
        (950_000.0, 3.61, 3.60, 0.9970, 0.9989, "receive_foreign_pay_domestic"),
        (1_050_000.0, 3.67, 3.70, 0.9920, 0.9960, "pay_foreign_receive_domestic"),
        (1_300_000.0, 3.75, 3.73, 0.9800, 0.9890, "receive_foreign_pay_domestic"),
        (1_700_000.0, 3.58, 3.62, 0.9900, 0.9950, "pay_foreign_receive_domestic"),
        (2_100_000.0, 3.66, 3.61, 0.9870, 0.9940, "receive_foreign_pay_domestic"),
    ]

    individual = [
        _price(notional=n, spot=s, strike=k, dfd=dfd, dff=dff, direction=direction)
        for n, s, k, dfd, dff, direction in cases
    ]

    pv_total = 0.0
    for value in individual:
        pv_total += value

    _assert_close(pv_total, sum(individual), tol=1e-8)


def test_r2_i8_permutation_invariance_ordering():
    cases = [
        (1_000_000.0, 3.64, 3.65, 0.9950, 0.9982, "receive_foreign_pay_domestic"),
        (2_000_000.0, 3.70, 3.55, 0.9850, 0.9930, "receive_foreign_pay_domestic"),
        (1_500_000.0, 3.68, 3.95, 0.9865, 0.9925, "receive_foreign_pay_domestic"),
        (1_200_000.0, 3.76, 3.82, 0.9350, 0.9550, "pay_foreign_receive_domestic"),
        (800_000.0, 3.64, 3.6405, 0.9999, 0.99995, "pay_foreign_receive_domestic"),
        (950_000.0, 3.61, 3.60, 0.9970, 0.9989, "receive_foreign_pay_domestic"),
        (1_050_000.0, 3.67, 3.70, 0.9920, 0.9960, "pay_foreign_receive_domestic"),
        (1_300_000.0, 3.75, 3.73, 0.9800, 0.9890, "receive_foreign_pay_domestic"),
        (1_700_000.0, 3.58, 3.62, 0.9900, 0.9950, "pay_foreign_receive_domestic"),
        (2_100_000.0, 3.66, 3.61, 0.9870, 0.9940, "receive_foreign_pay_domestic"),
    ]

    values = [
        _price(notional=n, spot=s, strike=k, dfd=dfd, dff=dff, direction=direction)
        for n, s, k, dfd, dff, direction in cases
    ]

    total_original = sum(values)
    total_reversed = sum(reversed(values))

    permutation = (3, 0, 9, 1, 6, 4, 8, 2, 7, 5)
    total_permuted = sum(values[index] for index in permutation)

    _assert_close(total_original, total_reversed, tol=1e-8)
    _assert_close(total_original, total_permuted, tol=1e-8)
