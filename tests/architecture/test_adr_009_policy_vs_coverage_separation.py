from pathlib import Path


def test_adr_009_doc_exists_and_mentions_policy_vs_coverage():
    p = Path("docs/architecture/adr/adr-009-policy-vs-coverage-separation.md")
    assert p.exists(), "ADR-009 doc must exist"
    text = p.read_text(encoding="utf-8").lower()
    assert "policy" in text and ("coverage" in text or "coverage" in text), "ADR-009 should mention policy vs coverage separation"
