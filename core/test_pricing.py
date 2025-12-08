# tests/core/test_pricing.py
from __future__ import annotations

from core.models import Leg, Position
from core.pricing import price_position  # או איך שזה מוגדר אצלך


def test_price_is_reasonable_for_atm_call() -> None:
    call = Leg(kind="call", direction="long", strike=100.0, qty=1, premium=0.0)
    pos = Position(underlying="TEST", legs=[call])

    price = price_position(pos, spot=100.0, iv=0.2, r=0.01, days_to_expiry=30)

    # מחיר אופציית CALL ATM צריך להיות חיובי ולא “מטורף”
    assert 0.1 < price < 20.0
