from api.v2.service_sqlite import V2ServiceSqlite
from datetime import datetime

def test_get_snapshot_materializes_full_state(tmp_path):
    svc = V2ServiceSqlite(str(tmp_path / "test.sqlite"))
    session_id = svc.create_session()
    # cadence N=50, נכניס 10 אירועים בלבד
    svc.snapshot_policy.n = 50
    for i in range(10):
        svc.ingest_event(
            session_id=session_id,
            event_id=f"e{i}",
            ts=datetime(2025, 1, 1, 12, 0, i),
            type="QUOTE_INGESTED",
            payload={"val": i},
        )
    snap = svc.get_snapshot(session_id)
    # כל האירועים חייבים להופיע
    assert set(snap.data.keys()) == {f"e{i}" for i in range(10)}
    assert snap.version == 10
