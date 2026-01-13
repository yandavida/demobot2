from pathlib import Path


def test_adr_002_doc_exists_and_mentions_validation_modes():
    candidates = [
        Path("docs/adr/adr-002-validation-modes-strict-lenient.md"),
        Path("docs/ADR/ADR-002-Execution-Boundary.md"),
        Path("docs/architecture/adr/adr-002-validation-modes-strict-lenient.md"),
    ]
    p = next((c for c in candidates if c.exists()), None)
    assert p is not None, f"ADR-002 doc must exist at one of: {[str(c) for c in candidates]}"
    text = p.read_text(encoding="utf-8").lower()
    assert "validation" in text, "ADR-002 doc should mention 'validation'"
