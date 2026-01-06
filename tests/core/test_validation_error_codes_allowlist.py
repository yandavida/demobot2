from pathlib import Path
import re


def _load_allowed_codes(taxonomy_path: Path) -> set[str]:
    text = taxonomy_path.read_text(encoding="utf8")
    # Prefer extracting keys from _MESSAGE_MAP which lists canonical codes
    msg_map_match = re.search(r"_MESSAGE_MAP\s*[:=]\s*{(.*?)}\n\n", text, re.S)
    if msg_map_match:
        body = msg_map_match.group(1)
        codes = set(re.findall(r'"([A-Z0-9_]+)"\s*:', body))
        if codes:
            return codes

    # Fallback: extract from Code = Literal[...]
    literal_match = re.search(r"Code\s*=\s*Literal\[((?:.|\n)*?)\]", text, re.S)
    if literal_match:
        body = literal_match.group(1)
        codes = set(re.findall(r'"([A-Z0-9_]+)"', body))
        return codes

    return set()


def test_error_codes_are_from_canonical_allowlist():
    repo_root = Path("core/validation")
    assert repo_root.exists(), "core/validation directory not found"

    taxonomy_file = repo_root / "error_taxonomy.py"
    assert taxonomy_file.exists(), "core/validation/error_taxonomy.py not found"

    allowed = _load_allowed_codes(taxonomy_file)
    assert allowed, "Could not extract allowed codes from error_taxonomy.py"

    excluded = {"error_taxonomy.py", "error_envelope.py"}
    offenders: dict[str, set[str]] = {}

    # Look for hardcoded occurrences like: code = "SOME_CODE" or code="SOME_CODE"
    pattern = re.compile(r"code\s*=\s*[\"']([A-Z0-9_]+)[\"']")

    for p in sorted(repo_root.rglob("*.py")):
        if p.name in excluded:
            continue
        text = p.read_text(encoding="utf8")
        for m in pattern.findall(text):
            if m not in allowed:
                offenders.setdefault(str(p), set()).add(m)

    if offenders:
        lines = []
        for f, codes in offenders.items():
            lines.append(f"{f}: {', '.join(sorted(codes))}")
        body = "\n".join(lines)
        raise AssertionError(
            "Found hardcoded non-canonical error codes in core/validation files (forbidden).\n"
            "Allowed codes come from core/validation/error_taxonomy.py.\n\n"
            f"Offenders:\n{body}"
        )
