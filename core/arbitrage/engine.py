from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List

from core.arbitrage.models import (
    ArbitrageConfig,
    ArbitrageLeg,
    ArbitrageOpportunity,
    VenueQuote,
)


def _net_edge_per_unit(buy_price: float, sell_price: float, buy_fee_bps: float, sell_fee_bps: float) -> float:
    """Return per-unit net edge after accounting for fees."""

    buy_cost = buy_price * (1 + buy_fee_bps / 10_000)
    sell_proceeds = sell_price * (1 - sell_fee_bps / 10_000)
    return sell_proceeds - buy_cost


def _edge_bps(net_edge: float, basis_price: float) -> float:
    if basis_price == 0:
        return 0.0
    return (net_edge / basis_price) * 10_000


def find_cross_venue_opportunities(
    quotes: Iterable[VenueQuote],
    config: ArbitrageConfig | None = None,
) -> List[ArbitrageOpportunity]:
    """Identify simple two-leg cross-venue arbitrage opportunities.

    The function is intentionally minimal for V2: it pairs the best bid and ask
    across venues for each symbol, filters by profitability, and returns
    structured opportunities with fee-adjusted edges.
    """

    cfg = config or ArbitrageConfig()
    grouped: dict[str, list[VenueQuote]] = defaultdict(list)
    for q in quotes:
        if q.has_liquidity():
            grouped[q.symbol].append(q)

    opportunities: list[ArbitrageOpportunity] = []

    for symbol, symbol_quotes in grouped.items():
        if len(symbol_quotes) < 2:
            continue

        best_bid = max(symbol_quotes, key=lambda q: q.bid)
        best_ask = min(symbol_quotes, key=lambda q: q.ask)

        if not cfg.allow_same_venue and best_bid.venue == best_ask.venue:
            continue

        gross_edge = best_bid.bid - best_ask.ask
        if gross_edge <= 0:
            continue

        size_candidates = [s for s in (best_bid.size, best_ask.size) if s is not None and s > 0]
        size = min(size_candidates) if size_candidates else cfg.default_size

        buy_leg = ArbitrageLeg(
            action="buy",
            venue=best_ask.venue,
            price=best_ask.ask,
            quantity=size,
            fees_bps=best_ask.fees_bps,
        )
        sell_leg = ArbitrageLeg(
            action="sell",
            venue=best_bid.venue,
            price=best_bid.bid,
            quantity=size,
            fees_bps=best_bid.fees_bps,
        )

        net_edge_per_unit = _net_edge_per_unit(
            buy_price=buy_leg.price,
            sell_price=sell_leg.price,
            buy_fee_bps=buy_leg.fees_bps,
            sell_fee_bps=sell_leg.fees_bps,
        )
        edge_bps = _edge_bps(net_edge_per_unit, buy_leg.price)

        if edge_bps < cfg.min_edge_bps or size < cfg.min_size:
            continue

        notes: list[str] = []
        if cfg.max_latency_ms is not None:
            if best_bid.latency_ms and best_bid.latency_ms > cfg.max_latency_ms:
                notes.append(
                    f"Latency on {best_bid.venue} exceeds threshold: {best_bid.latency_ms}ms"
                )
            if best_ask.latency_ms and best_ask.latency_ms > cfg.max_latency_ms:
                notes.append(
                    f"Latency on {best_ask.venue} exceeds threshold: {best_ask.latency_ms}ms"
                )

        opportunities.append(
            ArbitrageOpportunity(
                symbol=symbol,
                buy=buy_leg,
                sell=sell_leg,
                gross_edge=gross_edge,
                net_edge=net_edge_per_unit,
                edge_bps=edge_bps,
                size=size,
                notes=notes,
            )
        )

    return opportunities


__all__ = ["find_cross_venue_opportunities"]
