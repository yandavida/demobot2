"""F6.1: Theoretical PnL invariants - architecture-level checks.

Static scan to ensure no wall-clock access is used in the theoretical
PnL surface modules (determinism guard per ADR-014 / ADR-015).
"""
from pathlib import Path

FORBIDDEN_TOKENS = [
    "datetime.now",
    "date.today",
    "time.time",
    "time_ns",
    "perf_counter",
    "Timestamp.now",
    "utcnow",
]

TARGET_FILES = [
    Path("core/pnl/theoretical.py"),
    Path("core/pnl/portfolio_breakdown.py"),
]


def test_no_wallclock_in_theoretical_surfaces():
    found = []
    for p in TARGET_FILES:
        assert p.exists(), f"Expected file present: {p}"
        txt = p.read_text(encoding="utf8")
        for tok in FORBIDDEN_TOKENS:
            if tok in txt:
                found.append((str(p), tok))
    if found:
        msgs = [f"{f}:{t}" for f, t in found]
        raise AssertionError("Forbidden wall-clock tokens present: " + ", ".join(msgs))
