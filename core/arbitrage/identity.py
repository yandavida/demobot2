from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass


DEFAULT_PRICE_TICK = 0.01


def _price_bucket(value: float, tick: float) -> float:
    return math.floor(value / tick) * tick


def opportunity_id(
    symbol: str,
    buy_venue: str,
    sell_venue: str,
    base_ccy: str,
    buy_price_base: float,
    sell_price_base: float,
    tick: float = DEFAULT_PRICE_TICK,
) -> str:
    """Generate a deterministic ID for an opportunity within price buckets."""

    buy_bucket = _price_bucket(buy_price_base, tick)
    sell_bucket = _price_bucket(sell_price_base, tick)
    raw = f"{symbol}|{buy_venue}|{sell_venue}|{base_ccy}|{buy_bucket:.4f}|{sell_bucket:.4f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OpportunityIdentity:
    opportunity_id: str
    buy_bucket: float
    sell_bucket: float


__all__ = ["opportunity_id", "OpportunityIdentity", "DEFAULT_PRICE_TICK"]
