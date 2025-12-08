# tests/core/test_payoff.py
from __future__ import annotations

from core.models import Leg, Position
from core.payoff import payoff_position


def make_simple_call_position() -> Position:
    call_leg = Leg(
        kind="call",
        direction="long",
        strike=100.0,
        qty=1,
        premium=5.0,
        expiry=None,  # אם יש לך שדה expiry – תתאימי
    )
    return Position(
        underlying="TEST",
        legs=[call_leg],
    )


def test_call_payoff_in_the_money() -> None:
    pos = make_simple_call_position()
    payoff = payoff_position(pos, spot=120.0)
    # (120 - 100) - 5 = 15
    assert payoff == 15.0


def test_call_payoff_out_of_the_money() -> None:
    pos = make_simple_call_position()
    payoff = payoff_position(pos, spot=90.0)
    # הפסד פרמיה בלבד
    assert payoff == -5.0
