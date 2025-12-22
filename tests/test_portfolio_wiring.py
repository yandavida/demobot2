from __future__ import annotations

from typing import Mapping

from core.portfolio.wiring import (
    build_candidate_from_executions,
    evaluate_candidate,
    evaluate_candidates,
    PortfolioCandidate,
)
from core.portfolio.constraints import ConstraintSpec


class ExecStub:
    def __init__(self, opportunity_id: str | None = None, price: float = 1.0, economics: object | None = None) -> None:
        self.opportunity_id = opportunity_id
        self.buy = type("B", (), {"price": price})()
        self.economics = economics

    def __str__(self) -> str:  # deterministic textual fallback
        return f"ExecStub({self.opportunity_id},{getattr(self.buy,'price',None)})"


def _econ_dict(fees: float = 0.0, slippage: float = 0.0, cash: Mapping[str, float] | None = None, exposure: Mapping[str, float] | None = None):
    return {
        "fees": float(fees),
        "slippage": float(slippage),
        "notional": 0.0,
        "cash_usage": dict(cash or {}),
        "exposure_by_currency": dict(exposure or {}),
        "exposure_by_asset": {},
    }


def test_build_candidate_from_executions_is_deterministic():
    a = ExecStub("a", 1.0, _econ_dict())
    b = ExecStub("b", 2.0, _econ_dict())
    order1 = [a, b]
    order2 = [b, a]

    c1 = build_candidate_from_executions(order1)
    c2 = build_candidate_from_executions(order2)

    keys1 = tuple(p.key for p in c1.positions)
    keys2 = tuple(p.key for p in c2.positions)

    assert keys1 == keys2


def test_evaluate_candidate_non_strict_constraints_reported():
    # create single execution
    e = ExecStub("x", 1.0, _econ_dict())
    cand = build_candidate_from_executions([e])

    # constraint that disallows any positions
    spec = ConstraintSpec(name="limit0", kind="max_position_count", limits={"*": 0}, strict=False)

    res = evaluate_candidate(cand, specs=[spec], strict=False)

    assert res.ok is False
    assert any(w.startswith("constraint_violations:") for w in res.warnings)


def test_evaluate_candidate_strict_mode_returns_report_not_raises():
    e = ExecStub("y", 1.0, _econ_dict())
    cand = build_candidate_from_executions([e])
    spec = ConstraintSpec(name="limit0", kind="max_position_count", limits={"*": 0}, strict=True)

    # strict True should not raise here; wiring catches PortfolioConstraintError
    res = evaluate_candidate(cand, specs=[spec], strict=True)
    assert res.ok is False
    assert res.constraints.violation_count >= 1


def test_missing_economics_reported_and_affects_ok():
    e = ExecStub("m", 1.0, economics=None)
    cand = build_candidate_from_executions([e])
    spec = ConstraintSpec(name="none", kind="max_position_count", limits={"*": 10}, strict=False)

    res = evaluate_candidate(cand, specs=[spec], strict=False)
    assert res.missing_economics_count == 1
    assert res.ok is False
    assert any(w.startswith("missing_economics:") for w in res.warnings)


def test_evaluate_candidates_stable_ordering():
    # candidate names will determine ordering
    e1 = ExecStub("c1", 1.0, _econ_dict())
    e2 = ExecStub("c2", 1.0, _econ_dict())

    cand_a = build_candidate_from_executions([e1])
    cand_b = build_candidate_from_executions([e2])

    # set names to check ordering
    cand_a = PortfolioCandidate(positions=cand_a.positions, name="b")
    cand_b = PortfolioCandidate(positions=cand_b.positions, name="a")

    results = evaluate_candidates([cand_a, cand_b], specs=[], strict=False)

    names = tuple(r.state.metadata for r in results)
    # ensure deterministic count and ordering by name via our sort (a then b)
    assert len(results) == 2
    assert results[0].state.positions[0].key == cand_b.positions[0].key
    assert results[1].state.positions[0].key == cand_a.positions[0].key
