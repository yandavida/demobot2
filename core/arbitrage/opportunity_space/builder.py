from __future__ import annotations

from typing import Iterable, List, Tuple

from core.arbitrage.models import (
    ArbitrageConfig,
    ArbitrageLeg,
    ArbitrageOpportunity,
    VenueQuote,
)


def _net_edge_per_unit(buy_price: float, sell_price: float, buy_fee_bps: float, sell_fee_bps: float) -> float:
    buy_cost = buy_price * (1 + buy_fee_bps / 10_000)
    sell_proceeds = sell_price * (1 - sell_fee_bps / 10_000)
    return sell_proceeds - buy_cost


def _edge_bps(net_edge: float, basis_price: float) -> float:
    if basis_price == 0:
        return 0.0
    return (net_edge / basis_price) * 10_000


def build_opportunity_space(
    quotes: Iterable[VenueQuote], config: ArbitrageConfig | None = None
) -> List[ArbitrageOpportunity]:
    """Deterministically enumerate all feasible two-leg opportunities.

    Characteristics:
    - Enumerates all buy/sell venue pairs for each symbol (buy @ ask, sell @ bid).
    - Preserves economic provenance (prices, fees, sizes used to compute edges).
    - Produces a stable ordering independent of input ordering: sorted by
      (symbol, buy_venue, sell_venue, buy_price, sell_price).
    - Applies simple feasibility filters from `ArbitrageConfig` (min_edge_bps, min_size,
      allow_same_venue).

    This builder intentionally avoids heuristics or recommendations — it is
    a deterministic generator of feasible execution options. Human decision
    remains external to this module.
    """

    cfg = config or ArbitrageConfig()

    # Collect quotes per symbol, only keep those with liquidity
    per_symbol: dict[str, list[VenueQuote]] = {}
    for q in quotes:
        if not q.has_liquidity():
            continue
        per_symbol.setdefault(q.symbol, []).append(q)

    candidates: list[Tuple[Tuple, ArbitrageOpportunity]] = []

    for symbol, symbol_quotes in per_symbol.items():
        if len(symbol_quotes) < 2:
            continue

        # For determinism, sort venue quotes by (venue, ask, bid)
        symbol_quotes_sorted = sorted(
            symbol_quotes, key=lambda q: (q.venue, float(q.ask or 0.0), float(q.bid or 0.0))
        )

        # Enumerate all buy (ask) x sell (bid) pairs
        for buy in symbol_quotes_sorted:
            for sell in symbol_quotes_sorted:
                if buy is sell:
                    # same quote object; allow same-venue pairs only if config allows
                    if not cfg.allow_same_venue:
                        continue
                if not (buy.ask and sell.bid):
                    continue
                if not cfg.allow_same_venue and buy.venue == sell.venue:
                    continue

                gross_edge = float(sell.bid) - float(buy.ask)
                if gross_edge <= 0:
                    continue

                size_candidates = [s for s in (buy.size, sell.size) if s is not None and s > 0]
                size = min(size_candidates) if size_candidates else cfg.default_size

                net_edge_per_unit = _net_edge_per_unit(
                    buy_price=buy.ask,
                    sell_price=sell.bid,
                    buy_fee_bps=buy.fees_bps or 0.0,
                    sell_fee_bps=sell.fees_bps or 0.0,
                )

                edge_bps_val = _edge_bps(net_edge_per_unit, buy.ask)

                if edge_bps_val < cfg.min_edge_bps or size < cfg.min_size:
                    continue

                buy_leg = ArbitrageLeg(
                    action="buy",
                    venue=buy.venue,
                    ccy=buy.ccy,
                    price=float(buy.ask),
                    quantity=size,
                    fees_bps=buy.fees_bps or 0.0,
                )
                sell_leg = ArbitrageLeg(
                    action="sell",
                    venue=sell.venue,
                    ccy=sell.ccy,
                    price=float(sell.bid),
                    quantity=size,
                    fees_bps=sell.fees_bps or 0.0,
                )

                notes: list[str] = []
                if cfg.max_latency_ms is not None:
                    if sell.latency_ms and sell.latency_ms > cfg.max_latency_ms:
                        notes.append(f"Latency on {sell.venue} exceeds threshold: {sell.latency_ms}ms")
                    if buy.latency_ms and buy.latency_ms > cfg.max_latency_ms:
                        notes.append(f"Latency on {buy.venue} exceeds threshold: {buy.latency_ms}ms")

                opp = ArbitrageOpportunity(
                    symbol=symbol,
                    buy=buy_leg,
                    sell=sell_leg,
                    ccy=buy.ccy,
                    gross_edge=gross_edge,
                    net_edge=net_edge_per_unit,
                    edge_bps=edge_bps_val,
                    size=size,
                    notes=notes,
                )

                sort_key = (symbol, buy.venue, sell.venue, float(buy.ask), float(sell.bid))
                candidates.append((sort_key, opp))

    # Stable, deterministic ordering by sort_key
    candidates.sort(key=lambda t: t[0])
    return [c[1] for c in candidates]


__all__ = ["build_opportunity_space"]
