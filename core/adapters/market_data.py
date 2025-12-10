from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Dict, Iterable, TYPE_CHECKING

from core.adapters.contracts import MarketDataAdapter
from core.portfolio.models import MarketSnapshot

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from core.portfolio.models import Currency
else:
    Currency = str  # type: ignore[misc, assignment]


@dataclass
class InMemoryMarketDataAdapter(MarketDataAdapter):
    prices: Dict[str, float]
    vols: Dict[str, float] | None = None
    fx: Dict[tuple[Currency, Currency], float] | None = None
    base_ccy: Currency = "ILS"

    def get_snapshot(self, symbols: Iterable[str] | None = None) -> MarketSnapshot:
        """
        Returns a MarketSnapshot filtered by ``symbols`` when provided.
        If ``symbols`` is ``None`` all available data is returned.
        """
        if symbols is None:
            prices = self.prices
            vols = self.vols or {}
        else:
            symbol_set = set(symbols)
            prices = {s: p for s, p in self.prices.items() if s in symbol_set}
            vols = {s: v for s, v in (self.vols or {}).items() if s in symbol_set}

        snapshot_kwargs: Dict[str, object] = {"prices": prices}

        # Add optional fields only if the target dataclass defines them.
        available_fields = {f.name for f in fields(MarketSnapshot)}
        if "vols" in available_fields:
            snapshot_kwargs["vols"] = vols
        if "fx" in available_fields:
            snapshot_kwargs["fx"] = self.fx or {}
        if "base_ccy" in available_fields:
            snapshot_kwargs["base_ccy"] = self.base_ccy

        return MarketSnapshot(**snapshot_kwargs)  # type: ignore[arg-type]
