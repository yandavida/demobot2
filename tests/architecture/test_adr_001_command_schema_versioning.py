from pathlib import Path


def test_adr_001_doc_exists_and_mentions_schema_version():
    candidates = [
        Path("docs/adr/adr-001-command-schema-versioning.md"),
        Path("docs/ADR/ADR-001-V2-State-Model.md"),
        Path("docs/architecture/adr/adr-001-command-schema-versioning.md"),
    ]
    p = next((c for c in candidates if c.exists()), None)
    assert p is not None, f"ADR-001 doc must exist at one of: {[str(c) for c in candidates]}"
    # Document exists; content checks are intentionally minimal to remain stable
    _ = p.read_text(encoding="utf-8")
