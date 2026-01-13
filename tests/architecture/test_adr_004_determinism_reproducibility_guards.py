from pathlib import Path


def test_adr_004_doc_exists_and_repro_guards_present():
    candidates = [
        Path("docs/adr/adr-004-gate-b-gate-a-integration-guarantees.md"),
        Path("docs/ADR/ADR-004-Determinism-Caching-Reproducibility.md"),
        Path("docs/architecture/adr/adr-004-gate-b-gate-a-integration-guarantees.md"),
    ]
    p = next((c for c in candidates if c.exists()), None)
    assert p is not None, f"ADR-004 doc must exist at one of: {[str(c) for c in candidates]}"
    text = p.read_text(encoding="utf-8").lower()
    assert "determin" in text or "reproduc" in text, "ADR-004 should mention determinism/reproducibility"

    # Structural reinforcement: ensure at least one determinism-focused test file exists under tests/v2
    t = Path("tests/v2/test_gate_d_no_wallclock_fallback.py")
    assert t.exists(), "Expected determinism guard test tests/v2/test_gate_d_no_wallclock_fallback.py to exist"
