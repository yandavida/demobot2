import re
from pathlib import Path


TARGET_DIRS = [
    Path("core/pricing"),
    Path("core/fx"),
    Path("core/portfolio"),
    Path("core/risk"),
]

TARGET_FILES = [
    Path("core/greeks.py"),
    Path("core/black_scholes.py"),
    Path("core/payoff.py"),
    Path("core/fx_math.py"),
    Path("core/binomial_american.py"),
    Path("core/fx_mtm.py"),
]

# Keywords that indicate tolerance context
KEYWORDS = [
    "tol",
    "tolerance",
    "abs_tol",
    "rel_tol",
    "eps",
    "epsilon",
    "isclose",
    "converge",
    "threshold",
    "near_zero",
]

# Patterns to search for
PATTERNS = {
    "sci_notation": re.compile(r"\b1e-\d+\b", flags=re.IGNORECASE),
    "eps_name": re.compile(r"\beps(ilon)?\b", flags=re.IGNORECASE),
    "isclose_with_tol": re.compile(r"math\.isclose\([^)]*(abs_tol|rel_tol)\s*=", flags=re.IGNORECASE),
    "abs_compare_small": re.compile(r"abs\([^)]*\)\s*<\s*1e-\d+", flags=re.IGNORECASE),
}


def _gather_files():
    files = []
    for d in TARGET_DIRS:
        if d.exists():
            files.extend(sorted(p for p in d.rglob("*.py")))
    for f in TARGET_FILES:
        if f.exists():
            files.append(f)
    # Deduplicate
    seen = set()
    out = []
    for p in files:
        s = str(p)
        if s not in seen:
            seen.add(s)
            out.append(p)
    return out


def _line_has_keyword(line: str) -> bool:
    low = line.lower()
    return any(k in low for k in KEYWORDS)


def test_no_hardcoded_eps_in_finance_math():
    files = _gather_files()
    assert files, "No target finance-math files found to scan."

    violations = []

    # Baseline allowlist of existing violations (path, line, rule_id)
    BASELINE = {
        ("core/payoff.py", 99, "sci_notation"),
    }

    for fp in files:
        try:
            text = fp.read_text(encoding="utf8")
        except Exception:
            continue
        for i, raw in enumerate(text.splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            # First-pass matches
            for rule, pattern in PATTERNS.items():
                if pattern.search(line):
                    # second-pass: only flag if tolerance-related keywords present on the same line
                    if _line_has_keyword(line):
                        snippet = (line[:200] + ("..." if len(line) > 200 else ""))
                        violations.append((str(fp), i, snippet, rule))
                    # else: ignore to reduce false positives

            # Direct math.isclose with explicit tolerance anywhere
            if PATTERNS["isclose_with_tol"].search(line):
                snippet = (line[:200] + ("..." if len(line) > 200 else ""))
                violations.append((str(fp), i, snippet, "isclose_with_tol"))

    # Build sets for comparison against baseline
    found_set = set((p, ln, rule) for (p, ln, _, rule) in violations)

    extra = found_set - BASELINE
    missing = BASELINE - found_set

    # If baseline entries disappeared, print informational message (do not fail)
    if missing:
        print("Baseline allowlist entries no longer present:")
        for item in sorted(missing):
            print(f" - {item[0]}:{item[1]} [{item[2]}]")

    if extra:
        msg_lines = [
            "New hardcoded eps/tolerance patterns found in finance math files (not in baseline):\n",
        ]
        for path, lineno, rule in sorted(extra):
            # find snippet for nicer output
            snippet = next((s for (p, ln, s, r) in violations if p == path and ln == lineno and r == rule), "")
            msg_lines.append(f"{path}:{lineno}: [{rule}] {snippet}")
        full = "\n".join(msg_lines)
        raise AssertionError(full)

