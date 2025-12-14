from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CanonicalKey:
    symbol: str
    buy_venue: str
    sell_venue: str
    pricing_mode: str
    qty_rule: str
    fee_model: str

    def as_tuple(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.symbol,
            self.buy_venue,
            self.sell_venue,
            self.pricing_mode,
            self.qty_rule,
            self.fee_model,
        )


@dataclass(frozen=True)
class Provenance:
    as_of: datetime
    quote_refs: dict[str, str]
    fx_refs: dict[str, str] | None
    notes: list[str]


@dataclass(frozen=True)
class EconomicsBreakdown:
    buy_price: float
    sell_price: float
    quantity: float
    gross_edge: float
    fees_total: float
    net_edge: float
    notional: float
    profit: float
    edge_bps: float

    @staticmethod
    def from_prices(
        *,
        buy_price: float,
        sell_price: float,
        quantity: float,
        fees_total: float,
    ) -> "EconomicsBreakdown":
        gross_edge = sell_price - buy_price
        notional = quantity * buy_price
        profit = quantity * gross_edge - fees_total
        net_edge = profit / quantity if quantity > 0 else 0.0
        edge_bps = (net_edge / buy_price) * 10000 if buy_price > 0 else 0.0

        return EconomicsBreakdown(
            buy_price=buy_price,
            sell_price=sell_price,
            quantity=quantity,
            gross_edge=gross_edge,
            fees_total=fees_total,
            net_edge=net_edge,
            notional=notional,
            profit=profit,
            edge_bps=edge_bps,
        )


@dataclass(frozen=True)
class ExecutionOption:
    key: CanonicalKey
    opportunity_id: str
    economics: EconomicsBreakdown
    validation: dict[str, object] | None
    readiness: dict[str, object] | None
    provenance: Provenance

    def sort_key(self) -> tuple[str, str, str, str, str, str]:
        return self.key.as_tuple()
