from pathlib import Path


def test_adr_007_doc_exists_and_mentions_market_validation():
    p = Path("docs/architecture/adr/adr-007-canonical-market-validation-boundary.md")
    assert p.exists(), "ADR-007 doc must exist"
    text = p.read_text(encoding="utf-8").lower()
    assert "market" in text and ("valid" in text or "validation" in text), "ADR-007 should reference market validation"
