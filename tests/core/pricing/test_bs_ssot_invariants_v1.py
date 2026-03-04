from __future__ import annotations

import math

from core.numeric_policy import DEFAULT_TOLERANCES
from core.numeric_policy import MetricClass
from core.pricing.bs_ssot_v1 import TIME_FRACTION_POLICY_ACT_365F
from core.pricing.bs_ssot_v1 import price_european_option_bs_v1


def _abs_tol(metric: MetricClass) -> float:
    return float(DEFAULT_TOLERANCES[metric].abs or 0.0)


def _rel_tol(metric: MetricClass) -> float:
    return float(DEFAULT_TOLERANCES[metric].rel or 0.0)


def _assert_close(a: float, b: float, metric: MetricClass) -> None:
    assert math.isclose(a, b, rel_tol=_rel_tol(metric), abs_tol=_abs_tol(metric))


def _dfs(*, r: float, q: float, t: float) -> tuple[float, float]:
    return (math.exp(-r * t), math.exp(-q * t))


def test_put_call_parity_with_policy_tolerance() -> None:
    s = 100.0
    k = 95.0
    t = 0.75
    r = 0.03
    q = 0.01
    vol = 0.2
    notional = 1.0

    df_d, df_f = _dfs(r=r, q=q, t=t)

    c = price_european_option_bs_v1(
        spot=s,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=vol,
        ttm_years=t,
        option_type="call",
        notional=notional,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    p = price_european_option_bs_v1(
        spot=s,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=vol,
        ttm_years=t,
        option_type="put",
        notional=notional,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )

    rhs = s * df_f - k * df_d
    _assert_close(c.price_per_unit - p.price_per_unit, rhs, MetricClass.PRICE)


def test_spot_monotonicity_call_up_put_down() -> None:
    k = 100.0
    t = 0.5
    r = 0.02
    q = 0.0
    vol = 0.25
    df_d, df_f = _dfs(r=r, q=q, t=t)

    call_low = price_european_option_bs_v1(
        spot=99.0,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=vol,
        ttm_years=t,
        option_type="call",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    call_high = price_european_option_bs_v1(
        spot=101.0,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=vol,
        ttm_years=t,
        option_type="call",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    assert call_high.price_per_unit + _abs_tol(MetricClass.PRICE) >= call_low.price_per_unit

    put_low = price_european_option_bs_v1(
        spot=99.0,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=vol,
        ttm_years=t,
        option_type="put",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    put_high = price_european_option_bs_v1(
        spot=101.0,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=vol,
        ttm_years=t,
        option_type="put",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    assert put_low.price_per_unit + _abs_tol(MetricClass.PRICE) >= put_high.price_per_unit


def test_vol_monotonicity_call_and_put_non_decreasing() -> None:
    s = 100.0
    k = 100.0
    t = 1.0
    r = 0.01
    q = 0.0
    df_d, df_f = _dfs(r=r, q=q, t=t)

    call_low = price_european_option_bs_v1(
        spot=s,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=0.1,
        ttm_years=t,
        option_type="call",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    call_high = price_european_option_bs_v1(
        spot=s,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=0.4,
        ttm_years=t,
        option_type="call",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    assert call_high.price_per_unit + _abs_tol(MetricClass.PRICE) >= call_low.price_per_unit

    put_low = price_european_option_bs_v1(
        spot=s,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=0.1,
        ttm_years=t,
        option_type="put",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    put_high = price_european_option_bs_v1(
        spot=s,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=0.4,
        ttm_years=t,
        option_type="put",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    assert put_high.price_per_unit + _abs_tol(MetricClass.PRICE) >= put_low.price_per_unit


def test_time_monotonicity_non_dividend_call_non_decreasing() -> None:
    s = 100.0
    k = 100.0
    r = 0.03
    q = 0.0
    vol = 0.2

    t1 = 0.25
    t2 = 1.0
    df_d_1, df_f_1 = _dfs(r=r, q=q, t=t1)
    df_d_2, df_f_2 = _dfs(r=r, q=q, t=t2)

    c1 = price_european_option_bs_v1(
        spot=s,
        strike=k,
        domestic_df=df_d_1,
        foreign_df=df_f_1,
        vol=vol,
        ttm_years=t1,
        option_type="call",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    c2 = price_european_option_bs_v1(
        spot=s,
        strike=k,
        domestic_df=df_d_2,
        foreign_df=df_f_2,
        vol=vol,
        ttm_years=t2,
        option_type="call",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )

    assert c2.price_per_unit + _abs_tol(MetricClass.PRICE) >= c1.price_per_unit


def test_limit_checks_vol_zero_and_ttm_zero() -> None:
    s = 120.0
    k = 100.0
    r = 0.02
    q = 0.01

    t = 0.5
    df_d, df_f = _dfs(r=r, q=q, t=t)
    c_vol0 = price_european_option_bs_v1(
        spot=s,
        strike=k,
        domestic_df=df_d,
        foreign_df=df_f,
        vol=0.0,
        ttm_years=t,
        option_type="call",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    expected = max(s * df_f - k * df_d, 0.0)
    _assert_close(c_vol0.price_per_unit, expected, MetricClass.PRICE)

    p_t0 = price_european_option_bs_v1(
        spot=s,
        strike=k,
        domestic_df=1.0,
        foreign_df=1.0,
        vol=0.3,
        ttm_years=0.0,
        option_type="put",
        notional=1.0,
        time_fraction_policy_id=TIME_FRACTION_POLICY_ACT_365F,
    )
    _assert_close(p_t0.price_per_unit, max(k - s, 0.0), MetricClass.PRICE)


def test_determinism_same_inputs_same_output() -> None:
    kwargs = {
        "spot": 100.0,
        "strike": 102.0,
        "domestic_df": math.exp(-0.02 * 0.8),
        "foreign_df": math.exp(-0.01 * 0.8),
        "vol": 0.23,
        "ttm_years": 0.8,
        "option_type": "call",
        "notional": 250000.0,
        "time_fraction_policy_id": TIME_FRACTION_POLICY_ACT_365F,
    }

    a = price_european_option_bs_v1(**kwargs)
    b = price_european_option_bs_v1(**kwargs)

    assert a.price_per_unit == b.price_per_unit
    assert a.pv_domestic == b.pv_domestic
