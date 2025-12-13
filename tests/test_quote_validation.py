from __future__ import annotations

import pytest

from core.arbitrage.models import ArbitrageConfig
from core.arbitrage.quote_validation import validate_quotes
from core.services.arbitrage_orchestration import (
    StrictValidationError,
    create_arbitrage_session,
    get_history_window,
    get_session_history,
    ingest_quotes_and_scan,
)


def _build_valid_quotes() -> list[dict[str, object]]:
    return [
        {"symbol": "ES", "venue": "EX_A", "ccy": "USD", "bid": 4998.0, "ask": 4999.0},
        {"symbol": "ES", "venue": "EX_B", "ccy": "USD", "bid": 5002.0, "ask": 5002.5},
    ]


def test_validation_ordering_and_capping() -> None:
    quotes = [
        {"symbol": f"ES{i}", "venue": "", "bid": -1 * (i + 1), "ask": -2.0}
        for i in range(12)
    ]

    _, summary = validate_quotes(quotes, max_issues=5)
    payload = summary.to_dict()

    assert payload["total_quotes"] == len(quotes)
    assert payload["invalid_quotes"] == len(quotes)
    assert payload["capped"] is True
    assert len(payload["issues"]) == 5

    issues_from_summary = payload["issues"]
    sorted_again = sorted(
        issues_from_summary,
        key=lambda issue: (
            issue["code"],
            issue.get("field", ""),
            issue.get("venue", ""),
            issue.get("symbol", ""),
            issue["message"],
        ),
    )
    assert issues_from_summary == sorted_again


def test_strict_validation_rejects_invalid_payload() -> None:
    session_id = create_arbitrage_session(
        base_currency="ILS", config=ArbitrageConfig(min_edge_bps=0.0, default_size=1.0)
    )

    bad_quotes = [
        {"symbol": "", "venue": "EX_A", "bid": None, "ask": None},
        {"symbol": "ES", "venue": "EX_B", "bid": -1, "ask": 0},
    ]

    with pytest.raises(StrictValidationError) as exc:
        ingest_quotes_and_scan(
            session_id=session_id,
            quotes_payload=bad_quotes,
            fx_rate_usd_ils=3.5,
            strict_validation=True,
        )

    summary = exc.value.summary
    assert summary["total_quotes"] == len(bad_quotes)
    assert summary["invalid_quotes"] == len(bad_quotes)
    assert summary["total_issues"] >= len(bad_quotes)


def test_non_strict_validation_returns_summary_and_history() -> None:
    session_id = create_arbitrage_session(
        base_currency="ILS", config=ArbitrageConfig(min_edge_bps=0.0, default_size=1.0)
    )

    quotes_payload = _build_valid_quotes() + [
        {"symbol": "ES", "venue": "EX_C", "ccy": "USD", "bid": None, "ask": 5001.0}
    ]

    scan_result = ingest_quotes_and_scan(
        session_id=session_id, quotes_payload=quotes_payload, fx_rate_usd_ils=3.6
    )

    assert len(scan_result["opportunities"]) == 1
    history = get_session_history(session_id=session_id, symbol="ES")
    window = get_history_window(session_id=session_id, symbol="ES", limit=10)

    assert scan_result["opportunities"][0]["opportunity_id"] == history["opportunities"][0][
        "opportunity_id"
    ]
    assert history["opportunities"][0]["opportunity_id"] == window["opportunities"][0][
        "opportunity_id"
    ]
    assert scan_result["opportunities"][0]["execution_readiness"] == history["opportunities"][0][
        "execution_readiness"
    ]
    assert history["validation_summary"] == scan_result["validation_summary"]
    assert window["validation_summary"] == scan_result["validation_summary"]
