import pytest
from datetime import datetime, timedelta
from core.v2.models import V2Event, hash_payload

def make_event(event_id, session_id, ts, type, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type=type,
        payload=payload,
        payload_hash=hash_payload(payload),
    )


from api.v2.read_models import list_events
from api.v2.service import v2_service, reset_for_tests

@pytest.fixture(autouse=True)
def reset_v2_service():
    reset_for_tests()
    yield
    reset_for_tests()

def test_snapshot_readmodel_consistency():
    session_id = v2_service.create_session()
    base_ts = datetime(2025, 1, 1, 19, 0, 0)
    for i in range(10):
        v2_service.ingest_event(session_id, event_id=f"e{i}", ts=base_ts + timedelta(seconds=i), type="QUOTE_INGESTED", payload={"val": i})
    snap = v2_service.get_snapshot(session_id)
    events_list = list_events(session_id, limit=20, include_payload=True)
    assert len(events_list.items) == 10
    # כל event_id קיים
    assert set(e.event_id for e in events_list.items) == set(snap.data.keys())
    # סדר תואם (ts, event_id)
    sorted_ids = [e.event_id for e in sorted(events_list.items, key=lambda e: (e.ts, e.event_id))]
    assert [e.event_id for e in events_list.items] == sorted_ids

def test_deterministic_ordering_tiebreaker():
    session_id = v2_service.create_session()
    base_ts = datetime(2025, 1, 1, 20, 0, 0)
    # כל האירועים עם אותו timestamp, event_id שונה
    ids = [f"e{i}" for i in range(5)]
    for eid in ids:
        v2_service.ingest_event(session_id, event_id=eid, ts=base_ts, type="QUOTE_INGESTED", payload={"val": eid})
    events_list1 = list_events(session_id, limit=10, include_payload=True)
    events_list2 = list_events(session_id, limit=10, include_payload=True)
    # הסדר חייב להיות דטרמיניסטי (event_id)
    ids1 = [e.event_id for e in events_list1.items]
    ids2 = [e.event_id for e in events_list2.items]
    assert ids1 == sorted(ids1)
    assert ids1 == ids2

def test_idempotency_duplicate_event_id():
    session_id = v2_service.create_session()
    base_ts = datetime(2025, 1, 1, 21, 0, 0)
    v2_service.ingest_event(session_id, event_id="dup1", ts=base_ts, type="QUOTE_INGESTED", payload={"val": 1})
    v2_service.ingest_event(session_id, event_id="dup1", ts=base_ts, type="QUOTE_INGESTED", payload={"val": 1})
    events_list = list_events(session_id, limit=10, include_payload=True)
    assert len(events_list.items) == 1
    assert events_list.items[0].event_id == "dup1"

@pytest.mark.parametrize("limit", [1, 5, 10, 500])
def test_limit_boundaries(limit):
    session_id = v2_service.create_session()
    base_ts = datetime(2025, 1, 1, 22, 0, 0)
    for i in range(20):
        v2_service.ingest_event(session_id, event_id=f"e{i}", ts=base_ts + timedelta(seconds=i), type="QUOTE_INGESTED", payload={"val": i})
    events_list = list_events(session_id, limit=limit, include_payload=False)
    assert len(events_list.items) == min(limit, 20)

@pytest.mark.parametrize("bad_limit", [0, 501, -1])
def test_limit_validation_error(bad_limit):
    session_id = v2_service.create_session()
    with pytest.raises(Exception):
        list_events(session_id, limit=bad_limit, include_payload=False)

def test_empty_session_returns_empty():
    session_id = v2_service.create_session()
    events_list = list_events(session_id, limit=10, include_payload=False)
    assert events_list.items == []

def test_unknown_session_raises_404():
    with pytest.raises(Exception):
        list_events("not-a-session", limit=10, include_payload=False)

# בדיקות נוספות: סדר דטרמיניסטי, גבולות, idempotency, session ריק/לא קיים
# יש להשלים בהתאם ל-API ולפונקציות הזמינות במערכת
