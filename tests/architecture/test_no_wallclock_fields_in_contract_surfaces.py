from pathlib import Path


def test_unified_report_not_exported_to_api():
    """
    Structural guard: ensure `UnifiedPortfolioRiskReport` is not referenced
    from any `api/` source (i.e. not exported as an API schema/response).

    This test is intentionally conservative: any match will fail and list
    the offending files so reviewers can decide whether a production change
    is required (out of scope for this docs-only sprint).
    """
    api_dir = Path("api")
    assert api_dir.exists(), "api/ directory missing in workspace"

    matches = []
    for p in api_dir.rglob("*.py"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if "UnifiedPortfolioRiskReport" in txt:
            matches.append(str(p))

    assert not matches, (
        "UnifiedPortfolioRiskReport appears in API sources — this indicates the\n"
        "risk report type may be exported as part of an API contract.\n"
        f"Files: {matches}"
    )


def test_created_at_only_metadata_when_unified_report_present():
    """
    If by any chance `UnifiedPortfolioRiskReport` *is* referenced from API
    sources, ensure there's no `created_at` wall‑clock field exported as
    part of that contract. If the unified report isn't referenced at all
    this test is a no-op (passes).
    """
    api_dir = Path("api")
    unified_files = []
    for p in api_dir.rglob("*.py"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if "UnifiedPortfolioRiskReport" in txt:
            unified_files.append((p, txt))

    # If no unified report references in API, test is satisfied.
    if not unified_files:
        return

    offending = []
    for p, txt in unified_files:
        if "created_at" in txt:
            offending.append(str(p))

    assert not offending, (
        "Found 'created_at' in API sources that reference UnifiedPortfolioRiskReport.\n"
        "Such wall-clock fields must not be part of contractual API payloads.\n"
        f"Files: {offending}"
    )
