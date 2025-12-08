# tests/core/test_greeks.py
from __future__ import annotations

from core.greeks import calc_position_greeks
from core.models import Leg, Position


def test_delta_sign_for_call_vs_put() -> None:
    call = Leg(kind="call", direction="long", strike=100.0, qty=1, premium=5.0)
    put = Leg(kind="put", direction="long", strike=100.0, qty=1, premium=5.0)

    pos_call = Position(underlying="TEST", legs=[call])
    pos_put = Position(underlying="TEST", legs=[put])

    greeks_call = calc_position_greeks(
        pos_call, spot=100.0, iv=0.2, r=0.01, days_to_expiry=30
    )
    greeks_put = calc_position_greeks(
        pos_put, spot=100.0, iv=0.2, r=0.01, days_to_expiry=30
    )

    assert greeks_call.delta > 0
    assert greeks_put.delta < 0
