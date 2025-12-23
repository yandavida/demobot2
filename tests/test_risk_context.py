from core.risk.semantics import RiskContext, default_risk_context
from dataclasses import FrozenInstanceError
import pytest

def test_invalid_horizon():
    with pytest.raises(ValueError):
        RiskContext(horizon_days=0, confidence=0.99, base_currency="ILS")
    with pytest.raises(ValueError):
        RiskContext(horizon_days=2, confidence=0.99, base_currency="ILS")
    with pytest.raises(ValueError):
        RiskContext(horizon_days=30, confidence=0.99, base_currency="ILS")

def test_invalid_confidence():
    with pytest.raises(ValueError):
        RiskContext(horizon_days=1, confidence=0.5, base_currency="ILS")
    with pytest.raises(ValueError):
        RiskContext(horizon_days=1, confidence=1.0, base_currency="ILS")

def test_default_risk_context():
    ctx = default_risk_context()
    assert ctx.horizon_days == 1
    assert ctx.confidence == 0.99
    assert ctx.base_currency == "ILS"
    assert ctx.notes == {}
    assert ctx.as_of is None

def test_risk_context_immutable():
    ctx = default_risk_context()
    with pytest.raises(FrozenInstanceError):
        ctx.horizon_days = 10
