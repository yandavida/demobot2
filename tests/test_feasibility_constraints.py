from datetime import datetime

from core.arbitrage.models import ArbitrageOpportunity, ArbitrageLeg
from core.arbitrage.opportunity_space.constraints import (
    FeasibilityContext,
    evaluate_feasibility,
)


def _make_opportunity(**overrides) -> ArbitrageOpportunity:
    buy = ArbitrageLeg(action="buy", venue=overrides.get("buy_venue", "A"), price=overrides.get("buy_price", 100.0), quantity=overrides.get("size", 1.0))
    sell = ArbitrageLeg(action="sell", venue=overrides.get("sell_venue", "B"), price=overrides.get("sell_price", 101.0), quantity=overrides.get("size", 1.0))
    opp = ArbitrageOpportunity(
        symbol=overrides.get("symbol", "TST"),
        buy=buy,
        sell=sell,
        gross_edge=(sell.price - buy.price),
        net_edge=(sell.price - buy.price),
        edge_bps=((sell.price - buy.price) / buy.price) * 10_000,
        size=overrides.get("size", 1.0),
        ccy=overrides.get("ccy", "USD"),
        notes=[],
        opportunity_id=overrides.get("opportunity_id", ""),
        as_of=overrides.get("as_of", None),
    )
    return opp


def test_strict_vs_non_strict_soft_violation():
    now = datetime.utcnow()
    opp = _make_opportunity(size=3.0, as_of=now)

    ctx = FeasibilityContext(min_notional=None, max_notional=None, lot_size=2.0, now_ts=now)

    # With strict=True, SOFT lot_size mismatch should fail
    report_strict = evaluate_feasibility([opp], ctx, strict=True)
    assert len(report_strict.options) == 1
    assert report_strict.options[0].passed is False
    # violation should be SOFT but strict causes fail
    assert any(v.severity == "SOFT" for v in report_strict.options[0].violations)

    # With strict=False, SOFT violations do not fail
    report_lenient = evaluate_feasibility([opp], ctx, strict=False)
    assert report_lenient.options[0].passed is True


def test_hard_violation_always_fails_and_ordering():
    now = datetime.utcnow()
    # Option with allowed venue restriction violated
    opp = _make_opportunity(buy_venue="X", sell_venue="B", size=1.0, as_of=now)
    ctx = FeasibilityContext(allowed_venues={"A", "B"}, now_ts=now)

    report = evaluate_feasibility([opp], ctx, strict=False)
    opt = report.options[0]
    assert opt.passed is False
    # Violations should be present and include a HARD VENUE_ALLOWED
    codes = [v.code for v in opt.violations]
    assert "BUY_VENUE_NOT_ALLOWED" in codes

    # Deterministic ordering: HARD comes before SOFT - check severity ordering
    severities = [v.severity for v in opt.violations]
    assert severities == sorted(severities, key=lambda s: 0 if s == "HARD" else 1)


def test_missing_notional_is_hard():
    # create an option that will fail to compute notional (size missing)
    now = datetime.utcnow()
    opp = _make_opportunity(size=0.0, as_of=now)
    ctx = FeasibilityContext(min_notional=1.0, now_ts=now)

    report = evaluate_feasibility([opp], ctx, strict=False)
    opt = report.options[0]
    assert opt.passed is False
    codes = [v.code for v in opt.violations]
    assert "MISSING_NOTIONAL" in codes or "NOTIONAL_TOO_SMALL" in codes
