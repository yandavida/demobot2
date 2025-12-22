from __future__ import annotations

import random

from core.vol.inmemory import InMemoryVolProvider
from core.vol.types import VolKey, VolQuote
from core.vol.errors import MissingVolError


def test_exact_match_retrieval():
    key = VolKey(underlying="AAA", expiry_t=0.5, strike=100.0, option_type="call")
    q = VolQuote(key=key, vol=0.25)
    prov = InMemoryVolProvider([q])

    v = prov.get_vol(underlying="AAA", expiry_t=0.5, strike=100.0, option_type="call", strict=True)
    assert v == 0.25


def test_per_underlying_default():
    prov = InMemoryVolProvider({"AAA": 0.15})
    v = prov.get_vol(underlying="AAA", expiry_t=1.0, strike=110.0, option_type="put", strict=True)
    assert v == 0.15


def test_missing_strict_raises():
    prov = InMemoryVolProvider({})
    try:
        prov.get_vol(underlying="X", expiry_t=1.0, strike=100.0, option_type="call", strict=True)
        assert False, "expected MissingVolError"
    except MissingVolError:
        pass


def test_missing_non_strict_returns_zero():
    prov = InMemoryVolProvider({})
    v = prov.get_vol(underlying="X", expiry_t=1.0, strike=100.0, option_type="call", strict=False)
    assert v == 0.0


def test_snapshot_ordering_is_deterministic():
    keys = [
        VolKey("B", 1.0, 100.0, "call"),
        VolKey("A", 0.5, 90.0, "put"),
        VolKey("A", 0.5, None, "call"),
    ]
    quotes = [VolQuote(k, vol=0.1 + i * 0.01) for i, k in enumerate(keys)]
    # shuffle to ensure insertion order doesn't matter
    random.shuffle(quotes)
    prov = InMemoryVolProvider(quotes)
    snap = prov.snapshot()
    # snapshot should be sorted by underlying then expiry then strike then option_type
    assert tuple(q.key for q in snap) == tuple(sorted((q.key for q in quotes), key=lambda k: (k.underlying, float(k.expiry_t), float(k.strike) if k.strike is not None else float("inf"), k.option_type or "")))
