import pytest
from core.v2.snapshot_policy import EveryNSnapshotPolicy

@pytest.mark.parametrize("n, applied_versions, expected_snapshots", [
    (3, [1,2,3,4,5,6,7,8,9], [3,6,9]),
    (2, [1,2,3,4,5], [2,4]),
    (4, [1,2,3,4,5,6,7,8], [4,8]),
])
def test_every_n_snapshot_policy(n, applied_versions, expected_snapshots):
    policy = EveryNSnapshotPolicy(n=n)
    last_snapshot_version = None
    actual = []
    for v in applied_versions:
        should_snap, target = policy.should_snapshot(
            session_id="s1",
            last_snapshot_version=last_snapshot_version,
            next_applied_version=v,
        )
        if should_snap:
            actual.append(target)
            last_snapshot_version = target
    assert actual == expected_snapshots
