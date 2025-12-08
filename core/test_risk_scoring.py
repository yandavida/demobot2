# tests/core/test_risk_scoring.py
from __future__ import annotations

from core.models import Leg, Position
from core.risk_engine import classify_risk_level
from core.scoring import score_strategy


def make_bull_spread() -> Position:
    long_call = Leg(kind="call", direction="long", strike=100.0, qty=1, premium=5.0)
    short_call = Leg(kind="call", direction="short", strike=110.0, qty=1, premium=2.0)
    return Position(underlying="TEST", legs=[long_call, short_call])


def test_conservative_strategy_has_low_risk_score() -> None:
    pos = make_bull_spread()
    score = score_strategy(pos)
    risk = classify_risk_level(score)

    assert risk in {"low", "medium"}
