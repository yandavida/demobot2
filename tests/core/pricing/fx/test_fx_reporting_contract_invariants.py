import ast
import datetime
import inspect
import re

import pytest

from core import numeric_policy
from core.pricing.fx import forward_mtm
from core.pricing.fx import swap_mtm
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext


def _as_of() -> datetime.datetime:
    return datetime.datetime(2026, 2, 25, 10, 0, 0, tzinfo=datetime.timezone.utc)


def _forward_contract() -> fx_types.FXForwardContract:
    return fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="ILS",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 5, 25),
        forward_rate=3.72,
        direction="receive_foreign_pay_domestic",
    )


def _forward_snapshot(as_of_ts: datetime.datetime, domestic_currency: str | None = "ILS") -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=3.70,
        df_domestic=0.995,
        df_foreign=0.998,
        domestic_currency=domestic_currency,
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


def _near_snapshot(as_of_ts: datetime.datetime, domestic_currency: str | None = "ILS") -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=3.70,
        df_domestic=0.995,
        df_foreign=0.998,
        domestic_currency=domestic_currency,
    )


def _far_snapshot(as_of_ts: datetime.datetime, domestic_currency: str | None = "ILS") -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=3.71,
        df_domestic=0.985,
        df_foreign=0.992,
        domestic_currency=domestic_currency,
    )


def test_forward_result_has_currency_and_metric_class():
    as_of = _as_of()
    result = forward_mtm.price_fx_forward(
        as_of_ts=as_of,
        contract=_forward_contract(),
        market_snapshot=_forward_snapshot(as_of, "ILS"),
        conventions=None,
    )

    assert result.currency == "ILS"
    assert result.metric_class == numeric_policy.MetricClass.PRICE


def test_swap_result_has_currency_and_metric_class():
    as_of = _as_of()
    context = ValuationContext(as_of_ts=as_of, domestic_currency="ILS", strict_mode=True)

    result = swap_mtm.price_fx_swap_ctx(
        context=context,
        swap_contract=_swap_contract(),
        near_snapshot=_near_snapshot(as_of, "ILS"),
        far_snapshot=_far_snapshot(as_of, "ILS"),
    )

    assert result.currency == "ILS"
    assert result.metric_class == numeric_policy.MetricClass.PRICE
    assert result.details["pv_near_currency"] == "ILS"
    assert result.details["pv_far_currency"] == "ILS"


def test_ctx_wrapper_enforces_reporting_currency_consistency():
    as_of = _as_of()
    context = ValuationContext(as_of_ts=as_of, domestic_currency="ILS", strict_mode=True)

    with pytest.raises(ValueError, match="reporting currency must equal context.domestic_currency"):
        forward_mtm.price_fx_forward_ctx(
            context=context,
            contract=_forward_contract(),
            market_snapshot=_forward_snapshot(as_of, "USD"),
            conventions=None,
        )


def test_no_implicit_currency_assumptions():
    as_of = _as_of()

    with pytest.raises(
        ValueError,
        match="domestic reporting currency is required via conventions.domestic_currency or market_snapshot.domestic_currency",
    ):
        forward_mtm.price_fx_forward(
            as_of_ts=as_of,
            contract=_forward_contract(),
            market_snapshot=_forward_snapshot(as_of, None),
            conventions=None,
        )


def test_policy_scan_forbidden_import_tokens_in_fx_reporting_sources():
    modules = [forward_mtm, swap_mtm]
    forbidden = [
        "core.api",
        "api.",
        "lifecycle",
        "curve",
        "bootstrap",
        "interpolation",
        "zero_rate",
        "rate",
        "compounding",
        "daycount",
        "year_fraction",
        "exp(",
        "log(",
    ]

    for module in modules:
        source = inspect.getsource(module)
        import_lines = [line.strip() for line in source.splitlines() if line.strip().startswith(("import ", "from "))]
        import_text = "\n".join(import_lines).lower()

        for token in forbidden:
            token_lower = token.lower()
            if token_lower == "rate":
                assert re.search(r"\brate\b", import_text) is None
            else:
                assert token_lower not in import_text


def test_policy_scan_no_wall_clock_calls_in_fx_reporting_sources():
    modules = [forward_mtm, swap_mtm]

    def _is_forbidden_call(node: ast.Call) -> bool:
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "datetime" and func.attr in {"now", "utcnow"}:
                return True
            if func.value.id == "time" and func.attr in {"time", "perf_counter"}:
                return True
            if func.value.id == "random":
                return True
        return False

    for module in modules:
        tree = ast.parse(inspect.getsource(module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                assert not _is_forbidden_call(node)
