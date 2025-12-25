from core.portfolio.v2_reducer import reduce_portfolio_state
from core.v2.models import V2Event
from datetime import datetime
import copy

def make_event(event_id, type, ts, payload):
    return V2Event(
        event_id=event_id,
        session_id="sess1",
        ts=ts,
        type=type,
        payload=payload,
        payload_hash="h",
    )

def test_determinism_and_idempotency():
    ts0 = datetime(2023, 1, 1, 10, 0, 0)
    ts1 = datetime(2023, 1, 1, 10, 1, 0)
    ts2 = datetime(2023, 1, 1, 10, 2, 0)
    base_payload = {"base_currency": "USD", "constraints": {"max_notional": 1000.0}}
    upsert_payload = {
        "position_id": "p1",
        "legs": [
            {
                "leg_id": "l1",
                "underlying": "AAPL",
                "pv_per_unit": 1.0,
                "greeks_per_unit": {"delta": 1.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0},
                "notional_per_unit": 100.0,
                "quantity": 10.0,
            }
        ],
    }
    events = [
        make_event("e1", "PORTFOLIO_CREATED", ts0, base_payload),
        make_event("e2", "PORTFOLIO_POSITION_UPSERTED", ts1, upsert_payload),
        make_event("e3", "PORTFOLIO_POSITION_REMOVED", ts2, {"position_id": "p1"}),
    ]
    # Out-of-order, with duplicate
    events2 = [events[2], events[0], events[1], events[1]]
    state1 = reduce_portfolio_state(events)
    state2 = reduce_portfolio_state(events2)
    assert state1 == state2
    # Idempotency: duplicate event_id
    assert len(state1.positions) == 0

def test_upsert_replaces_position():
    ts0 = datetime(2023, 1, 1, 10, 0, 0)
    ts1 = datetime(2023, 1, 1, 10, 1, 0)
    base_payload = {"base_currency": "USD", "constraints": {}}
    upsert1 = {
        "position_id": "p1",
        "legs": [
            {
                "leg_id": "l1",
                "underlying": "AAPL",
                "pv_per_unit": 1.0,
                "greeks_per_unit": {"delta": 1.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0},
                "notional_per_unit": 100.0,
                "quantity": 10.0,
            }
        ],
    }
    upsert2 = copy.deepcopy(upsert1)
    upsert2["legs"][0]["quantity"] = 20.0
    events = [
        make_event("e1", "PORTFOLIO_CREATED", ts0, base_payload),
        make_event("e2", "PORTFOLIO_POSITION_UPSERTED", ts1, upsert1),
        make_event("e3", "PORTFOLIO_POSITION_UPSERTED", ts1, upsert2),
    ]
    state = reduce_portfolio_state(events)
    assert len(state.positions) == 1
    pos = state.positions["p1"]
    assert pos.legs[0].quantity == 20.0

def test_remove_deletes_position():
    ts0 = datetime(2023, 1, 1, 10, 0, 0)
    ts1 = datetime(2023, 1, 1, 10, 1, 0)
    base_payload = {"base_currency": "USD", "constraints": {}}
    upsert = {
        "position_id": "p1",
        "legs": [
            {
                "leg_id": "l1",
                "underlying": "AAPL",
                "pv_per_unit": 1.0,
                "greeks_per_unit": {"delta": 1.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0},
                "notional_per_unit": 100.0,
                "quantity": 10.0,
            }
        ],
    }
    events = [
        make_event("e1", "PORTFOLIO_CREATED", ts0, base_payload),
        make_event("e2", "PORTFOLIO_POSITION_UPSERTED", ts1, upsert),
        make_event("e3", "PORTFOLIO_POSITION_REMOVED", ts1, {"position_id": "p1"}),
    ]
    state = reduce_portfolio_state(events)
    assert len(state.positions) == 0
