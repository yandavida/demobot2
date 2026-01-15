from __future__ import annotations

import pytest

from api.v2.hedging_schemas import HedgeInput, HedgeResidualsOut, HedgeResultOut
from api.v2.hedging_read_model import compute_delta_hedge_read_model


FORBIDDEN_FIELDS = {"timestamp", "ts", "created_at", "updated_at", "uuid", "id", "applied_at"}


def test_no_dynamic_fields_on_models():
    models = [HedgeInput, HedgeResidualsOut, HedgeResultOut]
    for m in models:
        fields = set(m.model_fields.keys())
        assert fields.isdisjoint(FORBIDDEN_FIELDS), f"Model {m.__name__} contains forbidden dynamic fields: {fields & FORBIDDEN_FIELDS}"


def test_deterministic_serialization_of_compute():
    inp = HedgeInput(delta_portfolio=0.5, delta_hedge=0.25)
    out1 = compute_delta_hedge_read_model(inp)
    out2 = compute_delta_hedge_read_model(inp)
    assert out1.model_dump_json() == out2.model_dump_json()


def test_edge_cases_behavior():
    # delta_hedge == 0 -> ValueError with stable message
    inp_bad = HedgeInput(delta_portfolio=0.1, delta_hedge=0.0)
    with pytest.raises(ValueError) as exc:
        compute_delta_hedge_read_model(inp_bad)
    assert "delta_hedge == 0" in str(exc.value)

    # delta_portfolio == 0 -> zero quantity and zero residual
    inp_zero = HedgeInput(delta_portfolio=0.0, delta_hedge=0.3)
    out = compute_delta_hedge_read_model(inp_zero)
    assert out.hedge_quantity == 0.0
    assert out.residuals.delta == 0.0
