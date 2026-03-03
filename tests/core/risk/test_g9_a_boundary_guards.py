from __future__ import annotations

import datetime
import hashlib
import json
import io
import token as token_mod
import tokenize
from decimal import Decimal
from pathlib import Path

import pytest

from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext
from core.risk.reprice_harness import RiskValidationError
from core.risk.reprice_harness import reprice_fx_forward_risk
from core.risk.risk_artifact import build_risk_artifact_v1
from core.risk.risk_request import RiskRequest
from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import ScenarioSpec


RISK_MODULES = (
    Path("core/risk/risk_request.py"),
    Path("core/risk/scenario_spec.py"),
    Path("core/risk/scenario_set.py"),
    Path("core/risk/scenario_grid.py"),
    Path("core/risk/reprice_harness.py"),
    Path("core/risk/risk_artifact.py"),
)

FORBIDDEN_TOKENS = (
    "datetime.now",
    "time.time",
    "random",
    "numpy.random",
    "pandas",
    "curve",
    "bootstrap",
    "interpolation",
    "zero_rate",
    "provider",
    "requests",
    "os.environ",
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "import random",
    "from random",
    "import time",
    "from time",
    "import pandas",
    "from pandas",
    "import numpy.random",
    "from numpy.random",
    "import requests",
    "from requests",
    "import curve",
    "from curve",
    "import bootstrap",
    "from bootstrap",
)

LAYER_FORBIDDEN_IMPORT_SUBSTRINGS = (
    "core.lifecycle",
    "api.",
    "from api",
    "service_sqlite",
    " bot",
    "from bot",
)

FIXTURE_PATH = Path("tests/core/risk/_data/g9_risk_artifact_v1_fixture.json")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_code_without_comments_and_strings(path: Path) -> str:
    text = _read_text(path)
    buffer = io.StringIO(text)
    chunks: list[str] = []
    for tok in tokenize.generate_tokens(buffer.readline):
        if tok.type in {
            token_mod.STRING,
            tokenize.COMMENT,
            token_mod.NL,
            token_mod.NEWLINE,
            token_mod.INDENT,
            token_mod.DEDENT,
            token_mod.ENDMARKER,
        }:
            continue
        chunks.append(tok.string)
    return " ".join(chunks)


def _context() -> ValuationContext:
    return ValuationContext(
        as_of_ts=datetime.datetime(2026, 3, 2, 12, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2))),
        domestic_currency="ILS",
        strict_mode=True,
    )


def _snapshot() -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=_context().as_of_ts,
        spot_rate=3.64,
        df_domestic=0.995,
        df_foreign=0.9982,
    )


def _contracts() -> dict[str, fx_types.FXForwardContract]:
    return {
        "fwd_a": fx_types.FXForwardContract(
            base_currency="USD",
            quote_currency="ILS",
            notional=1_000_000.0,
            forward_date=datetime.date(2026, 4, 2),
            forward_rate=3.65,
            direction="receive_foreign_pay_domestic",
        ),
        "fwd_b": fx_types.FXForwardContract(
            base_currency="USD",
            quote_currency="ILS",
            notional=1_000_000.0,
            forward_date=datetime.date(2026, 4, 2),
            forward_rate=3.60,
            direction="receive_foreign_pay_domestic",
        ),
    }


def _spec(
    *,
    spot: tuple[Decimal, ...],
    dfd: tuple[Decimal, ...],
    dff: tuple[Decimal, ...],
) -> ScenarioSpec:
    return ScenarioSpec(
        schema_version=1,
        spot_shocks=spot,
        df_domestic_shocks=dfd,
        df_foreign_shocks=dff,
    )


def _request(*, instrument_ids: tuple[str, ...], spec: ScenarioSpec) -> RiskRequest:
    return RiskRequest(
        schema_version=1,
        valuation_context=_context(),
        market_snapshot_id="snap-g9-a-001",
        instrument_ids=instrument_ids,
        scenario_spec=spec,
        strict=True,
    )


def _grid(spec: ScenarioSpec) -> ScenarioGrid:
    return ScenarioGrid.from_scenario_set(ScenarioSet.from_spec(spec))


def _build_artifact(*, instrument_ids: tuple[str, ...], spec: ScenarioSpec) -> dict:
    request = _request(instrument_ids=instrument_ids, spec=spec)
    grid = _grid(spec)
    risk_result = reprice_fx_forward_risk(request, _snapshot(), grid, _contracts())
    return build_risk_artifact_v1(request, grid, risk_result)


# ──────────────────────────────────────────────────────────────────────────────
# Part A — Boundary & forbidden patterns
# ──────────────────────────────────────────────────────────────────────────────


def test_a1_forbidden_tokens_absent_in_gate9_modules() -> None:
    for path in RISK_MODULES:
        text = _read_code_without_comments_and_strings(path)
        for token in FORBIDDEN_TOKENS:
            assert token not in text, f"Forbidden token {token!r} found in {path}"



def test_a2_forbidden_imports_absent_in_gate9_modules() -> None:
    for path in RISK_MODULES:
        lines = _read_text(path).splitlines()
        for line_number, line_text in enumerate(lines, start=1):
            stripped = line_text.strip()
            if not stripped.startswith(("import ", "from ")):
                continue
            for token in FORBIDDEN_IMPORT_SUBSTRINGS:
                assert token not in stripped, (
                    f"Forbidden import token {token!r} in {path}:{line_number} -> {stripped}"
                )



def test_a3_layering_guard_no_lifecycle_api_or_orchestrator_imports() -> None:
    for path in RISK_MODULES:
        lines = _read_text(path).splitlines()
        for line_number, line_text in enumerate(lines, start=1):
            stripped = line_text.strip()
            if not stripped.startswith(("import ", "from ")):
                continue
            for token in LAYER_FORBIDDEN_IMPORT_SUBSTRINGS:
                assert token not in stripped, (
                    f"Layering violation token {token!r} in {path}:{line_number} -> {stripped}"
                )


# ──────────────────────────────────────────────────────────────────────────────
# Part B — Semantic consistency behavioral proofs
# ──────────────────────────────────────────────────────────────────────────────


def test_b1_1_rejects_shock_with_non_positive_factor() -> None:
    spec = _spec(
        spot=(Decimal("-1.00"),),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )
    request = _request(instrument_ids=("fwd_a",), spec=spec)
    grid = _grid(spec)

    with pytest.raises(RiskValidationError):
        reprice_fx_forward_risk(request, _snapshot(), grid, {"fwd_a": _contracts()["fwd_a"]})



def test_b1_2_spot_monotonicity_for_unambiguous_case() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.05")),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )
    request = _request(instrument_ids=("fwd_a",), spec=spec)
    grid = _grid(spec)

    result = reprice_fx_forward_risk(request, _snapshot(), grid, {"fwd_a": _contracts()["fwd_a"]})
    cube = result.results[0]
    by_shock = {
        key.spot_shock: pv.pv_domestic
        for key, pv in zip(grid.scenarios, cube.scenario_pvs)
    }

    low = by_shock[Decimal("-0.05")]
    high = by_shock[Decimal("0.05")]

    assert low != high
    assert low < high



def test_b1_3_zero_shocks_equal_base_exactly() -> None:
    spec = _spec(
        spot=(Decimal("0.00"),),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )
    request = _request(instrument_ids=("fwd_a",), spec=spec)
    grid = _grid(spec)

    result = reprice_fx_forward_risk(request, _snapshot(), grid, {"fwd_a": _contracts()["fwd_a"]})
    cube = result.results[0]

    assert len(cube.scenario_pvs) == 1
    assert cube.scenario_pvs[0].pv_domestic == cube.base_pv



def test_b2_scenario_ordering_is_behaviorally_lexicographic() -> None:
    spec_unsorted = _spec(
        spot=(Decimal("0.05"), Decimal("-0.05"), Decimal("0.00")),
        dfd=(Decimal("0.01"), Decimal("-0.01"), Decimal("0.00")),
        dff=(Decimal("0.02"), Decimal("-0.02"), Decimal("0.00")),
    )
    grid = _grid(spec_unsorted)

    actual = tuple((k.spot_shock, k.df_domestic_shock, k.df_foreign_shock) for k in grid.scenarios)
    expected = tuple(sorted(actual))

    assert actual == expected
    assert actual[0] == min(actual)
    assert actual[-1] == max(actual)



def test_b3_artifact_hashing_behavioral_immutability() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        dff=(Decimal("-0.02"), Decimal("0.00"), Decimal("0.02")),
    )

    artifact_a = _build_artifact(instrument_ids=("fwd_a", "fwd_b"), spec=spec)
    artifact_b = _build_artifact(instrument_ids=("fwd_a", "fwd_b"), spec=spec)

    assert artifact_a == artifact_b
    assert artifact_a["sha256"] == artifact_b["sha256"]

    if FIXTURE_PATH.exists():
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        fixture_body = {k: v for k, v in fixture.items() if k != "sha256"}
        canonical = json.dumps(fixture_body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        recomputed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert recomputed == fixture["sha256"]



def test_b4_end_to_end_determinism_with_mocked_pricing_seam() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )
    request = _request(instrument_ids=("fwd_a",), spec=spec)
    grid = _grid(spec)

    def mock_price_forward(contract, valuation_context, market_snapshot):
        pv = market_snapshot.spot_rate * 1000.0 + contract.forward_rate
        return fx_types.PricingResult(
            as_of_ts=valuation_context.as_of_ts,
            pv=pv,
            details={"mock": True},
            currency=valuation_context.domestic_currency,
            metric_class=fx_types.numeric_policy.MetricClass.PRICE,
        )

    result_a = reprice_fx_forward_risk(
        request,
        _snapshot(),
        grid,
        {"fwd_a": _contracts()["fwd_a"]},
        price_forward=mock_price_forward,
    )
    result_b = reprice_fx_forward_risk(
        request,
        _snapshot(),
        grid,
        {"fwd_a": _contracts()["fwd_a"]},
        price_forward=mock_price_forward,
    )

    artifact_a = build_risk_artifact_v1(request, grid, result_a)
    artifact_b = build_risk_artifact_v1(request, grid, result_b)

    assert artifact_a == artifact_b
    assert artifact_a["sha256"] == artifact_b["sha256"]



def test_b5_permutation_invariance_structural() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )

    artifact_a = _build_artifact(instrument_ids=("fwd_b", "fwd_a"), spec=spec)
    artifact_b = _build_artifact(instrument_ids=("fwd_a", "fwd_b"), spec=spec)

    assert artifact_a == artifact_b
    assert artifact_a["sha256"] == artifact_b["sha256"]
