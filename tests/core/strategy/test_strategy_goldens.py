import hashlib
import json
from pathlib import Path

import pytest

from core.strategy.gaps import compute_portfolio_gaps, PortfolioExposures
from core.strategy.scoped_gaps import compute_scoped_gaps
from core.strategy.targets import PortfolioTargets, ScopedTargets


GOLDEN_DIR = Path("core/strategy/goldens")


def _load(path: Path):
    return json.loads(path.read_text())


def _to_portfolio_targets(d):
    return PortfolioTargets(delta=d.get("delta"), gamma=d.get("gamma"), vega=d.get("vega"))


def _to_exposures(d):
    return PortfolioExposures(delta=d.get("delta", 0.0), gamma=d.get("gamma", 0.0), vega=d.get("vega", 0.0))


def _canonical_payload(portfolio_gaps, scoped_gaps):
    # sort keys and strategy ids; ensure None -> null via json
    po = {k: (v if v is None else float(v)) for k, v in portfolio_gaps.items()}
    sg = {sid: {k: (getattr(g, k) if getattr(g, k) is None else float(getattr(g, k))) for k in ("delta", "gamma", "vega")} for sid, g in scoped_gaps.items()}
    # sort strategies
    ordered_sg = {k: sg[k] for k in sorted(sg.keys())}
    payload = {"portfolio_gaps": po, "scoped_gaps": ordered_sg}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@pytest.mark.parametrize("scenario_file,scenario_key", [
    ("scenarios/portfolio_only.json", "portfolio_only"),
    ("scenarios/scoped_basic.json", "scoped_basic"),
    ("scenarios/none_semantics.json", "none_semantics"),
    ("scenarios/monotonic_step0.json", "monotonic_step0"),
    ("scenarios/monotonic_step1.json", "monotonic_step1"),
    ("scenarios/monotonic_step2.json", "monotonic_step2"),
])
def test_strategy_golden_match(scenario_file, scenario_key):
    manifest = _load(GOLDEN_DIR / "datasets_manifest.json")
    assert scenario_file in manifest["scenarios"], "Scenario not in manifest"

    scenario = _load(GOLDEN_DIR / scenario_file)

    # portfolio
    pt = _to_portfolio_targets(scenario.get("portfolio_targets", {}))
    cur_po = _to_exposures(scenario.get("current_portfolio_exposures", {}))
    portfolio_gaps_obj = compute_portfolio_gaps(cur_po, pt)
    portfolio_gaps = {"delta": portfolio_gaps_obj.delta, "gamma": portfolio_gaps_obj.gamma, "vega": portfolio_gaps_obj.vega}

    # scoped
    overrides = {}
    for sid, v in scenario.get("scoped_targets", {}).items():
        overrides[sid] = _to_portfolio_targets(v)
    scoped_targets = ScopedTargets(overrides=overrides)

    current_by_strategy = {}
    for sid, v in scenario.get("current_by_strategy", {}).items():
        current_by_strategy[sid] = _to_exposures(v)

    scoped_gaps_obj = compute_scoped_gaps(current_by_strategy, scoped_targets)

    canonical = _canonical_payload(portfolio_gaps, scoped_gaps_obj)
    digest = _sha256_hex(canonical)

    expected = _load(GOLDEN_DIR / "expected_hashes.json")
    assert scenario_key in expected, f"Missing expected hash for {scenario_key}"
    assert digest == expected[scenario_key], f"Golden mismatch for {scenario_key}: {digest} != {expected[scenario_key]}"
