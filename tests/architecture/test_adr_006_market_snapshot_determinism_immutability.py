from pathlib import Path


def test_adr_006_doc_exists_and_mentions_snapshot_or_immutable():
    p = Path("docs/architecture/adr/adr-006-market-snapshot-determinism-immutability.md")
    assert p.exists(), "ADR-006 doc must exist"
    text = p.read_text(encoding="utf-8").lower()
    assert ("snapshot" in text or "immut" in text), "ADR-006 should mention snapshot/immutability"
