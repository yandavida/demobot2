import ast
import datetime
import inspect
import re

import pytest

from core.pricing.fx import swap_mtm
from core.pricing.fx import swap_view
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext


def _as_of() -> datetime.datetime:
    return datetime.datetime(2026, 2, 25, 14, 0, 0, tzinfo=datetime.timezone.utc)


def _context(domestic_currency: str = "ILS") -> ValuationContext:
    return ValuationContext(
        as_of_ts=_as_of(),
        domestic_currency=domestic_currency,
        strict_mode=True,
    )


def _contract(
    *,
    notional: float = 1_000_000.0,
    near_direction: str = "receive_foreign_pay_domestic",
    far_direction: str = "pay_foreign_receive_domestic",
    near_rate: float = 3.70,
    far_rate: float = 3.80,
) -> swap_mtm.FxSwapContract:
    near = swap_mtm.FxSwapLeg(
        forward_rate=near_rate,
        direction=near_direction,
        settlement_date=datetime.date(2026, 3, 25),
    )
    far = swap_mtm.FxSwapLeg(
        forward_rate=far_rate,
        direction=far_direction,
        settlement_date=datetime.date(2026, 6, 25),
    )
    return swap_mtm.FxSwapContract(
        base_ccy="USD",
        quote_ccy="ILS",
        notional_foreign=notional,
        near=near,
        far=far,
    )


def test_sign_correctness_per_direction_for_both_legs():
    contract = _contract(
        notional=2.0,
        near_direction="receive_foreign_pay_domestic",
        far_direction="pay_foreign_receive_domestic",
        near_rate=3.0,
        far_rate=4.0,
    )

    view = swap_view.build_fx_swap_cashflow_view(_context(), contract)

    near_leg, far_leg = view.legs

    # near: receive foreign, pay domestic => +Nf, -Nf*K
    assert near_leg.foreign.amount == 2.0
    assert near_leg.domestic.amount == -6.0

    # far: pay foreign, receive domestic => -Nf, +Nf*K
    assert far_leg.foreign.amount == -2.0
    assert far_leg.domestic.amount == 8.0


def test_linearity_scaling_notional_scales_cashflows_linearly():
    view_1x = swap_view.build_fx_swap_cashflow_view(_context(), _contract(notional=1.0))
    view_3x = swap_view.build_fx_swap_cashflow_view(_context(), _contract(notional=3.0))

    for leg_1x, leg_3x in zip(view_1x.legs, view_3x.legs):
        assert leg_3x.foreign.amount == 3.0 * leg_1x.foreign.amount
        assert leg_3x.domestic.amount == 3.0 * leg_1x.domestic.amount


def test_symmetry_flipping_direction_flips_both_cashflow_signs():
    contract_a = _contract(
        notional=5.0,
        near_direction="receive_foreign_pay_domestic",
        far_direction="pay_foreign_receive_domestic",
        near_rate=3.5,
        far_rate=3.9,
    )
    contract_b = _contract(
        notional=5.0,
        near_direction="pay_foreign_receive_domestic",
        far_direction="receive_foreign_pay_domestic",
        near_rate=3.5,
        far_rate=3.9,
    )

    view_a = swap_view.build_fx_swap_cashflow_view(_context(), contract_a)
    view_b = swap_view.build_fx_swap_cashflow_view(_context(), contract_b)

    for leg_a, leg_b in zip(view_a.legs, view_b.legs):
        assert leg_a.foreign.amount == -leg_b.foreign.amount
        assert leg_a.domestic.amount == -leg_b.domestic.amount
        assert abs(leg_a.foreign.amount) == abs(leg_b.foreign.amount)
        assert abs(leg_a.domestic.amount) == abs(leg_b.domestic.amount)


def test_determinism_repeated_calls_identical_outputs():
    contract = _contract()
    context = _context()

    view_1 = swap_view.build_fx_swap_cashflow_view(context, contract)
    view_2 = swap_view.build_fx_swap_cashflow_view(context, contract)

    assert view_1 == view_2


def test_legs_order_is_stable_near_then_far():
    view = swap_view.build_fx_swap_cashflow_view(_context(), _contract())

    assert view.legs[0].leg_id == "near"
    assert view.legs[1].leg_id == "far"
    assert view.legs[0].settlement_date <= view.legs[1].settlement_date


def test_domestic_currency_ssot_from_context():
    with pytest.raises(
        ValueError,
        match="conventions.domestic_currency must match context.domestic_currency",
    ):
        swap_view.build_fx_swap_cashflow_view(
            _context("ILS"),
            _contract(),
            conventions=fx_types.FxConventions(
                day_count="ACT/365",
                compounding="simple",
                domestic_currency="USD",
            ),
        )


def test_domestic_currency_ignores_conventions_when_matching():
    view = swap_view.build_fx_swap_cashflow_view(
        _context("ILS"),
        _contract(),
        conventions=fx_types.FxConventions(
            day_count="ACT/365",
            compounding="simple",
            domestic_currency="ILS",
        ),
    )

    assert view.domestic_currency == "ILS"


def test_negative_notional_raises_value_error():
    with pytest.raises(ValueError, match="notional must be positive"):
        swap_view.build_fx_swap_cashflow_view(
            _context(),
            _contract(notional=-1.0),
        )


def test_settlement_dates_are_date_objects_runtime():
    leg_sig = inspect.signature(swap_mtm.FxSwapLeg)
    leg_fields = set(leg_sig.parameters.keys())

    def _make_leg(direction: str, forward_rate: float, settlement_date: datetime.date):
        kwargs = {}
        if "forward_rate" in leg_fields:
            kwargs["forward_rate"] = forward_rate
        if "direction" in leg_fields:
            kwargs["direction"] = direction
        if "settlement_date" in leg_fields:
            kwargs["settlement_date"] = settlement_date
        return swap_mtm.FxSwapLeg(**kwargs)

    near = _make_leg("receive_foreign_pay_domestic", 3.72, datetime.date(2026, 2, 1))
    far = _make_leg("pay_foreign_receive_domestic", 3.74, datetime.date(2026, 3, 1))

    contract_sig = inspect.signature(swap_mtm.FxSwapContract)
    contract_fields = set(contract_sig.parameters.keys())
    contract_kwargs = {
        "near": near,
        "far": far,
        "notional_foreign": 1_000_000.0,
        "base_ccy": "USD",
        "quote_ccy": "ILS",
    }
    contract = swap_mtm.FxSwapContract(
        **{key: value for key, value in contract_kwargs.items() if key in contract_fields}
    )

    view = swap_view.build_fx_swap_cashflow_view(_context("ILS"), contract)

    assert isinstance(view.legs[0].settlement_date, datetime.date)
    assert isinstance(view.legs[0].foreign.settlement_date, datetime.date)
    assert isinstance(view.legs[0].domestic.settlement_date, datetime.date)


def test_policy_scan_no_forbidden_imports_or_curve_construction_tokens():
    source = inspect.getsource(swap_view)
    import_lines = [line.strip().lower() for line in source.splitlines() if line.strip().startswith(("import ", "from "))]
    import_text = "\n".join(import_lines)

    forbidden = [
        "core.api",
        "api.",
        "lifecycle",
        "curve",
        "bootstrap",
        "interpolation",
        "zero_rate",
        "compounding",
        "daycount",
        "year_fraction",
        "exp(",
        "log(",
    ]

    for token in forbidden:
        assert token not in import_text

    # disallow standalone 'rate' import token but allow field names like forward_rate in code
    assert re.search(r"\brate\b", import_text) is None


def test_policy_scan_no_wall_clock_calls():
    tree = ast.parse(inspect.getsource(swap_view))

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

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            assert not _is_forbidden_call(node)
