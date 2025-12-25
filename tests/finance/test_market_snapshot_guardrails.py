import pytest
from datetime import datetime
from core.marketdata import Quote, build_market_snapshot_v1, market_snapshot_fingerprint, validate_required_for_symbols, market_snapshot_to_canonical_dict

@pytest.fixture
def base_quotes():
    return [
        Quote(kind="spot", key="AAPL", value=100.0),
        Quote(kind="vol", key="AAPL", value=0.2),
        Quote(kind="rate", key="USD", value=0.03),
        Quote(kind="div", key="AAPL", value=0.01),
        Quote(kind="fx_spot", key="USD/ILS", value=3.7),
        Quote(kind="fx_forward", key="USD/ILS", value=3.75),
    ]

def test_determinism(base_quotes):
    asof = datetime(2025, 1, 1, 12, 0, 0)
    snap1 = build_market_snapshot_v1(asof, base_quotes)
    snap2 = build_market_snapshot_v1(asof, base_quotes)
    dict1 = market_snapshot_to_canonical_dict(snap1)
    dict2 = market_snapshot_to_canonical_dict(snap2)
    assert dict1 == dict2
    assert market_snapshot_fingerprint(snap1) == market_snapshot_fingerprint(snap2)

def test_permutation_invariance(base_quotes):
    asof = datetime(2025, 1, 1, 12, 0, 0)
    shuffled = list(reversed(base_quotes))
    snap1 = build_market_snapshot_v1(asof, base_quotes)
    snap2 = build_market_snapshot_v1(asof, shuffled)
    assert market_snapshot_fingerprint(snap1) == market_snapshot_fingerprint(snap2)

def test_validation_missing_required():
    asof = datetime(2025, 1, 1, 12, 0, 0)
    quotes = [Quote(kind="spot", key="AAPL", value=100.0)]
    snap = build_market_snapshot_v1(asof, quotes)
    with pytest.raises(ValueError) as e:
        validate_required_for_symbols(snap, ["AAPL"])
    assert "vol:AAPL" in str(e.value)

def test_duplicate_key_raises(base_quotes):
    asof = datetime(2025, 1, 1, 12, 0, 0)
    quotes = base_quotes + [Quote(kind="spot", key="AAPL", value=101.0)]
    with pytest.raises(ValueError) as e:
        build_market_snapshot_v1(asof, quotes)
    assert "Duplicate quote" in str(e.value)
