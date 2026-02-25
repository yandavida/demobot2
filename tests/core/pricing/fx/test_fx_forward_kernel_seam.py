import datetime

from core import numeric_policy
from core.pricing.fx import forward_mtm
from core.pricing.fx.kernels import DefaultFXForwardKernel
from core.pricing.fx import types as fx_types


def _approx_equal(a: float, b: float) -> bool:
    tol = numeric_policy.DEFAULT_TOLERANCES[numeric_policy.MetricClass.PRICE]
    abs_diff = abs(a - b)
    if abs_diff <= tol.abs:
        return True
    rel_diff = abs_diff / max(abs(a), abs(b), 1.0)
    return rel_diff <= tol.rel


def test_price_fx_forward_default_path_matches_hand_formula():
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 5, 12)

    S = 1.10
    K = 1.08
    DFd = 0.99
    DFf = 0.98
    Nf = 1_000_000.0

    contract = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=Nf,
        forward_date=maturity,
        forward_rate=K,
        direction="receive_foreign_pay_domestic",
    )
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=S,
        df_domestic=DFd,
        df_foreign=DFf,
    )

    result = forward_mtm.price_fx_forward(as_of, contract, snapshot, None)

    f_mkt = S * DFf / DFd
    expected_pv = Nf * DFd * (f_mkt - K)

    assert _approx_equal(result.pv, expected_pv)
    assert _approx_equal(result.details["forward_market"], f_mkt)


def test_default_kernel_matches_public_forward_function_output():
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 5, 12)

    contract = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=1_000_000.0,
        forward_date=maturity,
        forward_rate=1.08,
        direction="receive_foreign_pay_domestic",
    )
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=1.10,
        df_domestic=0.99,
        df_foreign=0.98,
    )

    kernel = DefaultFXForwardKernel()
    result_public = forward_mtm.price_fx_forward(as_of, contract, snapshot, None)
    result_kernel = kernel.price_forward(as_of, contract, snapshot, None)

    assert result_public == result_kernel
    assert result_public.details == result_kernel.details


def test_forward_details_payload_stays_stable():
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 5, 12)

    contract = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=1_000_000.0,
        forward_date=maturity,
        forward_rate=1.08,
        direction="receive_foreign_pay_domestic",
    )
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=1.10,
        df_domestic=0.99,
        df_foreign=0.98,
    )

    result1 = forward_mtm.price_fx_forward(as_of, contract, snapshot, None)
    result2 = forward_mtm.price_fx_forward(as_of, contract, snapshot, None)

    expected_keys = [
        "forward_market",
        "spot",
        "df_domestic",
        "df_foreign",
        "forward_rate",
        "notional_foreign",
        "direction",
    ]

    assert list(result1.details.keys()) == expected_keys
    assert result1 == result2
