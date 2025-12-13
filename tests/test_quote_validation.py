from datetime import datetime, timedelta

from core.market_data.validation import (
    validate_quote_payload,
    validate_quotes_payload,
)


def test_validate_quote_payload_success() -> None:
    payload = {
        "symbol": "ES",
        "venue": "CME",
        "ccy": "usd",
        "bid": 5000,
        "ask": 5000.5,
        "size": 10,
        "fees_bps": 1.2,
        "timestamp": datetime.utcnow().isoformat(),
    }

    result = validate_quote_payload(payload)

    assert result.is_valid
    assert result.errors == []
    assert result.normalized is not None
    assert result.normalized["ccy"] == "USD"
    assert result.normalized["bid"] == 5000.0
    assert result.normalized["ask"] == 5000.5
    assert result.normalized["size"] == 10.0


def test_validate_quote_payload_errors() -> None:
    payload = {
        "symbol": " ",
        "venue": "",
        "ccy": "EUR",
        "bid": -1,
        "ask": None,
        "size": -5,
    }

    result = validate_quote_payload(payload)

    assert not result.is_valid
    assert "symbol is required" in result.errors
    assert "venue is required" in result.errors
    assert "ccy must be a supported currency" in result.errors
    assert "bid must be non-negative" in result.errors
    assert "ask is missing" in result.errors
    assert "size must be non-negative" in result.errors


def test_validate_quotes_payload_mixed() -> None:
    valid = {"symbol": "ES", "venue": "A", "ccy": "USD", "bid": 10, "ask": 11}
    stale_ts = datetime.utcnow() - timedelta(days=10)
    invalid = {
        "symbol": "ES",
        "venue": "B",
        "ccy": "USD",
        "bid": 12,
        "ask": 11,
        "timestamp": stale_ts,
    }

    results = validate_quotes_payload([valid, invalid])

    assert len(results) == 2
    assert results[0].is_valid
    assert not results[1].is_valid
    assert any("bid must be less than or equal to ask" in e for e in results[1].errors)
    # stale timestamp should be recorded as warning even when invalid due to bid/ask
    assert any("timestamp is stale" in w for w in results[1].warnings)
