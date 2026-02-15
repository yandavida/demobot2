import datetime
import ast
import inspect
from pathlib import Path
import re

import pytest

from core.pricing.fx import swap_types


def _make_leg(
    *,
    value_date: datetime.date,
    direction: str,
    notional_foreign: float = 1_000_000.0,
    forward_rate: float = 3.70,
    foreign_ccy: str = "USD",
    domestic_ccy: str = "ILS",
) -> swap_types.FxSwapLeg:
    return swap_types.FxSwapLeg(
        value_date=value_date,
        notional_foreign=notional_foreign,
        forward_rate=forward_rate,
        direction=direction,
        foreign_ccy=foreign_ccy,
        domestic_ccy=domestic_ccy,
    )


def _make_happy_contract() -> swap_types.FxSwapContract:
    near_leg = _make_leg(
        value_date=datetime.date(2026, 3, 1),
        direction="receive_foreign_pay_domestic",
    )
    far_leg = _make_leg(
        value_date=datetime.date(2026, 6, 1),
        direction="pay_foreign_receive_domestic",
        forward_rate=3.75,
    )
    return swap_types.FxSwapContract(near_leg=near_leg, far_leg=far_leg)


def test_happy_path_construction_and_default_reporting_ils():
    contract = _make_happy_contract()
    assert contract.near_leg.value_date < contract.far_leg.value_date
    assert contract.near_leg.foreign_ccy == contract.far_leg.foreign_ccy
    assert contract.near_leg.domestic_ccy == contract.far_leg.domestic_ccy
    assert contract.reporting_ccy == "ILS"
    assert contract.near_leg.domestic_ccy == "ILS"


def test_date_ordering_invariant_rejects_equal_dates():
    near_leg = _make_leg(
        value_date=datetime.date(2026, 3, 1),
        direction="receive_foreign_pay_domestic",
    )
    far_leg = _make_leg(
        value_date=datetime.date(2026, 3, 1),
        direction="pay_foreign_receive_domestic",
    )
    with pytest.raises(ValueError, match="near_leg.value_date"):
        swap_types.FxSwapContract(near_leg=near_leg, far_leg=far_leg)


def test_date_ordering_invariant_rejects_near_after_far():
    near_leg = _make_leg(
        value_date=datetime.date(2026, 7, 1),
        direction="receive_foreign_pay_domestic",
    )
    far_leg = _make_leg(
        value_date=datetime.date(2026, 6, 1),
        direction="pay_foreign_receive_domestic",
    )
    with pytest.raises(ValueError, match="near_leg.value_date"):
        swap_types.FxSwapContract(near_leg=near_leg, far_leg=far_leg)


def test_pair_coherence_rejects_mismatched_foreign_ccy():
    near_leg = _make_leg(
        value_date=datetime.date(2026, 3, 1),
        direction="receive_foreign_pay_domestic",
        foreign_ccy="USD",
    )
    far_leg = _make_leg(
        value_date=datetime.date(2026, 6, 1),
        direction="pay_foreign_receive_domestic",
        foreign_ccy="EUR",
    )
    with pytest.raises(ValueError, match="foreign_ccy"):
        swap_types.FxSwapContract(near_leg=near_leg, far_leg=far_leg)


def test_pair_coherence_rejects_mismatched_domestic_ccy():
    near_leg = _make_leg(
        value_date=datetime.date(2026, 3, 1),
        direction="receive_foreign_pay_domestic",
        domestic_ccy="ILS",
    )
    far_leg = _make_leg(
        value_date=datetime.date(2026, 6, 1),
        direction="pay_foreign_receive_domestic",
        domestic_ccy="EUR",
    )
    with pytest.raises(ValueError, match="domestic_ccy"):
        swap_types.FxSwapContract(near_leg=near_leg, far_leg=far_leg)


def test_direction_coherence_rejects_same_direction_for_both_legs():
    near_leg = _make_leg(
        value_date=datetime.date(2026, 3, 1),
        direction="receive_foreign_pay_domestic",
    )
    far_leg = _make_leg(
        value_date=datetime.date(2026, 6, 1),
        direction="receive_foreign_pay_domestic",
    )
    with pytest.raises(ValueError, match="far_leg.direction"):
        swap_types.FxSwapContract(near_leg=near_leg, far_leg=far_leg)


def test_direction_validation_rejects_invalid_string():
    with pytest.raises(ValueError, match="direction"):
        _make_leg(
            value_date=datetime.date(2026, 3, 1),
            direction="invalid_direction",
        )


@pytest.mark.parametrize("bad_notional", [0.0, -1.0])
def test_numeric_validation_rejects_non_positive_notional(bad_notional: float):
    with pytest.raises(ValueError, match="notional_foreign"):
        _make_leg(
            value_date=datetime.date(2026, 3, 1),
            direction="receive_foreign_pay_domestic",
            notional_foreign=bad_notional,
        )


@pytest.mark.parametrize("bad_forward_rate", [0.0, -0.1])
def test_numeric_validation_rejects_non_positive_forward_rate(bad_forward_rate: float):
    with pytest.raises(ValueError, match="forward_rate"):
        _make_leg(
            value_date=datetime.date(2026, 3, 1),
            direction="receive_foreign_pay_domestic",
            forward_rate=bad_forward_rate,
        )


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("notional_foreign", float("nan")),
        ("notional_foreign", float("inf")),
        ("forward_rate", float("nan")),
        ("forward_rate", float("inf")),
    ],
)
def test_numeric_validation_rejects_nan_inf(field_name: str, bad_value: float):
    kwargs = {
        "value_date": datetime.date(2026, 3, 1),
        "direction": "receive_foreign_pay_domestic",
    }
    kwargs[field_name] = bad_value
    with pytest.raises(ValueError, match=field_name):
        _make_leg(**kwargs)


@pytest.mark.parametrize("bad_ccy", ["usd", "US", "USDD", "12$", "ilS"])
def test_currency_code_validation_rejects_invalid_code_format(bad_ccy: str):
    with pytest.raises(ValueError, match="foreign_ccy"):
        _make_leg(
            value_date=datetime.date(2026, 3, 1),
            direction="receive_foreign_pay_domestic",
            foreign_ccy=bad_ccy,
        )


def test_currency_code_validation_rejects_same_foreign_and_domestic():
    with pytest.raises(ValueError, match="foreign_ccy"):
        _make_leg(
            value_date=datetime.date(2026, 3, 1),
            direction="receive_foreign_pay_domestic",
            foreign_ccy="ILS",
            domestic_ccy="ILS",
        )


def test_israel_presentation_lock_rejects_domestic_not_ils():
    near_leg = _make_leg(
        value_date=datetime.date(2026, 3, 1),
        direction="receive_foreign_pay_domestic",
        foreign_ccy="EUR",
        domestic_ccy="USD",
    )
    far_leg = _make_leg(
        value_date=datetime.date(2026, 6, 1),
        direction="pay_foreign_receive_domestic",
        foreign_ccy="EUR",
        domestic_ccy="USD",
    )
    with pytest.raises(ValueError, match="domestic_ccy"):
        swap_types.FxSwapContract(near_leg=near_leg, far_leg=far_leg)


def test_israel_presentation_lock_rejects_reporting_not_ils():
    near_leg = _make_leg(
        value_date=datetime.date(2026, 3, 1),
        direction="receive_foreign_pay_domestic",
    )
    far_leg = _make_leg(
        value_date=datetime.date(2026, 6, 1),
        direction="pay_foreign_receive_domestic",
    )
    with pytest.raises(ValueError, match="reporting_ccy"):
        swap_types.FxSwapContract(near_leg=near_leg, far_leg=far_leg, reporting_ccy="USD")


def test_israel_presentation_lock_rejects_reporting_domestic_mismatch():
    near_leg = _make_leg(
        value_date=datetime.date(2026, 3, 1),
        direction="receive_foreign_pay_domestic",
        foreign_ccy="EUR",
        domestic_ccy="USD",
    )
    far_leg = _make_leg(
        value_date=datetime.date(2026, 6, 1),
        direction="pay_foreign_receive_domestic",
        foreign_ccy="EUR",
        domestic_ccy="USD",
    )
    with pytest.raises(ValueError, match="reporting_ccy|domestic_ccy"):
        swap_types.FxSwapContract(near_leg=near_leg, far_leg=far_leg, reporting_ccy="ILS")


def test_governance_no_wall_clock_patterns_in_test_module_source():
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    def _is_forbidden_call(node: ast.Call) -> bool:
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "datetime" and func.attr in {"now", "utcnow"}:
                return True
            if func.value.id == "time" and func.attr in {"time", "perf_counter"}:
                return True
            if func.value.id == "random":
                return True
            if func.value.id == "uuid":
                return True
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            assert not _is_forbidden_call(node)


def test_governance_no_pricing_or_curve_tokens_in_swap_types_source():
    source = inspect.getsource(swap_types)
    assert "exp(" not in source
    assert "log(" not in source
    assert re.search(r"\brate\b", source) is None
    assert "zero_rate" not in source
    assert "compounding" not in source
    assert "daycount" not in source
    assert "year_fraction" not in source
    assert "curve" not in source
    assert "yield" not in source
    assert "interpolation" not in source
    assert "bootstrap" not in source
