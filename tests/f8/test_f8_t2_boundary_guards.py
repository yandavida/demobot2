from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

TARGET_FILES = (
    REPO_ROOT / "core/pricing/fx/forward_mtm.py",
    REPO_ROOT / "core/pricing/fx/swap_mtm.py",
    REPO_ROOT / "core/pricing/fx/kernels.py",
    REPO_ROOT / "core/pricing/fx/types.py",
    REPO_ROOT / "core/pricing/fx/swap_view.py",
)

# Tier 2 architecture freeze guard tokens.
# "daycount" intentionally checks compact token form (not "day_count") to avoid
# false positives from legacy naming while still guarding against policy drift.
FORBIDDEN_TOKENS = (
    "curve",
    "bootstrap",
    "interpolation",
    "zero_rate",
    "compounding",
    "daycount",
    "datetime.now",
    "time.time",
    "random",
    "pandas",
    "numpy.random",
    "abs(",
)

# Tier 2 boundary policy allows legacy conventions metadata in types.py;
# DF-only guarantees for FxMarketSnapshot are enforced separately in T3.
FILE_TOKEN_EXCEPTIONS = {
    "core/pricing/fx/types.py": {"compounding", "daycount"},
}

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "import random",
    "from random",
    "import time",
    "from time",
    "import pandas",
    "from pandas",
    "import numpy.random",
    "from numpy.random",
    "import curve",
    "from curve",
    "import bootstrap",
    "from bootstrap",
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _line_number_for_token(text: str, token: str) -> int:
    index = text.find(token)
    if index < 0:
        return -1
    return text.count("\n", 0, index) + 1


def _extract_class_block(text: str, class_name: str) -> str:
    class_header = f"class {class_name}:"
    start = text.find(class_header)
    if start < 0:
        raise AssertionError(f"Missing class definition: {class_name}")

    next_class = text.find("\nclass ", start + len(class_header))
    if next_class < 0:
        return text[start:]
    return text[start:next_class]


def test_t2g_t1_forbidden_token_scan_gate_f8_modules():
    for file_path in TARGET_FILES:
        text = _read_text(file_path)
        relative_file = str(file_path.relative_to(REPO_ROOT))
        exceptions = FILE_TOKEN_EXCEPTIONS.get(relative_file, set())
        for token in FORBIDDEN_TOKENS:
            if token in exceptions:
                continue
            line = _line_number_for_token(text, token)
            assert line == -1, (
                f"Forbidden token '{token}' found in {relative_file}"
                f" at line {line}"
            )


def test_t2g_t2_no_forbidden_imports_gate_f8_modules():
    for file_path in TARGET_FILES:
        lines = _read_text(file_path).splitlines()
        for line_number, line_text in enumerate(lines, start=1):
            stripped = line_text.strip()
            if not stripped.startswith(("import ", "from ")):
                continue

            for forbidden_import in FORBIDDEN_IMPORT_SUBSTRINGS:
                assert forbidden_import not in stripped, (
                    f"Forbidden import '{forbidden_import}' found in"
                    f" {file_path.relative_to(REPO_ROOT)} at line {line_number}: {stripped}"
                )


def test_t2g_t3_fx_market_snapshot_df_only_boundary():
    types_file = REPO_ROOT / "core/pricing/fx/types.py"
    types_text = _read_text(types_file)
    snapshot_block = _extract_class_block(types_text, "FxMarketSnapshot")

    forbidden_snapshot_terms = (
        "rate_domestic",
        "rate_foreign",
        "curve",
        "bootstrap",
        "interpolation",
        "zero_rate",
        "compounding",
        "day_count",
    )

    for term in forbidden_snapshot_terms:
        line = _line_number_for_token(snapshot_block, term)
        assert line == -1, (
            f"FxMarketSnapshot must remain DF-only: found forbidden term '{term}'"
            f" in core/pricing/fx/types.py (class block line {line})"
        )
