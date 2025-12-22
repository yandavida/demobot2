from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence, Tuple, Any

from core.portfolio.models import Currency as _CurrencyLiteral
from core.arbitrage.models import ArbitrageOpportunity


# Minimal aliases for canonical identifiers used by the portfolio layer
CanonicalKey = str
ExecutionOption = ArbitrageOpportunity
EconomicsBreakdown = Any


def _key_sort_value(key: CanonicalKey) -> str:
    # Deterministic string representation for sorting
    return str(key)


@dataclass(frozen=True)
class Position:
    """Immutable portfolio Position holding an execution option.

    Note: This Position is market-data agnostic. Any derived economics
    must be embedded in the `execution` if required.
    """

    key: CanonicalKey
    execution: ExecutionOption
    quantity: float
    tags: frozenset[str] = field(default_factory=frozenset)
    notes: str | None = None

    def __post_init__(self) -> None:  # type: ignore[override]
        if not (self.quantity > 0):
            raise ValueError(f"Position.quantity must be > 0, got {self.quantity}")

        # Lightweight best-effort identity validation: if execution exposes
        # an `opportunity_id` attribute, ensure it matches the provided key.
        exec_id = getattr(self.execution, "opportunity_id", None)
        if exec_id is not None and exec_id != self.key:
            raise ValueError("Position.key does not match execution.opportunity_id")

    def notional(self) -> float:
        try:
            return float(self.execution.buy.price * self.quantity)
        except Exception:
            return 0.0

    def economics(self) -> EconomicsBreakdown:
        econ = getattr(self.execution, "economics", None)
        if econ is None:
            raise ValueError("Execution does not contain economics breakdown")
        return econ


@dataclass(frozen=True)
class PortfolioTotals:
    position_count: int
    gross_quantity: float


@dataclass(frozen=True)
class PortfolioState:
    positions: Tuple[Position, ...]
    base_currency: _CurrencyLiteral = "USD"
    revision: int = 0
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:  # type: ignore[override]
        # Ensure deterministic ordering of positions by key
        sorted_positions = tuple(sorted(self.positions, key=lambda p: _key_sort_value(p.key)))
        object.__setattr__(self, "positions", sorted_positions)

        # Normalize metadata to deterministic tuple of pairs sorted by key
        md_pairs = tuple(sorted(dict(self.metadata).items())) if self.metadata else tuple()
        object.__setattr__(self, "metadata", md_pairs)

    @staticmethod
    def with_positions(positions: Sequence[Position], *, base_currency: _CurrencyLiteral = "USD", bump_revision: bool = True, revision: int = 0, metadata: Mapping[str, str] | None = None) -> "PortfolioState":
        rev = revision + (1 if bump_revision else 0)
        meta_pairs = tuple(sorted(metadata.items())) if metadata else tuple()
        return PortfolioState(positions=tuple(positions), base_currency=base_currency, revision=rev, metadata=meta_pairs)

    def add(self, position: Position, *, bump_revision: bool = True) -> "PortfolioState":
        # Replace any existing position with same key
        others = [p for p in self.positions if p.key != position.key]
        new_positions = tuple(others + [position])
        rev = self.revision + (1 if bump_revision else 0)
        return PortfolioState(positions=new_positions, base_currency=self.base_currency, revision=rev, metadata=self.metadata)

    def remove_by_key(self, key: CanonicalKey, *, bump_revision: bool = True) -> "PortfolioState":
        new_positions = tuple(p for p in self.positions if p.key != key)
        rev = self.revision + (1 if bump_revision else 0)
        return PortfolioState(positions=new_positions, base_currency=self.base_currency, revision=rev, metadata=self.metadata)

    def get_position(self, key: CanonicalKey) -> Position | None:
        for p in self.positions:
            if p.key == key:
                return p
        return None

    def keys(self) -> Tuple[CanonicalKey, ...]:
        return tuple(p.key for p in self.positions)


@dataclass(frozen=True)
class PortfolioSnapshot:
    state: PortfolioState
    totals: PortfolioTotals
    exposure_by_currency: Tuple[Tuple[_CurrencyLiteral, float], ...] = field(default_factory=tuple)
    fees_total: float = 0.0
    slippage_total: float = 0.0


def build_portfolio_snapshot(state: PortfolioState) -> PortfolioSnapshot:
    position_count = len(state.positions)
    gross_quantity = sum(float(p.quantity) for p in state.positions)
    totals = PortfolioTotals(position_count=position_count, gross_quantity=gross_quantity)
    # Defer to aggregators for deterministic, market-data-agnostic aggregates
    try:
        from core.portfolio.aggregators import aggregate_portfolio

        ag = aggregate_portfolio(state)
        return PortfolioSnapshot(
            state=state,
            totals=totals,
            exposure_by_currency=tuple((k, v) for k, v in ag.exposure_by_currency),
            fees_total=ag.total_fees,
            slippage_total=ag.total_slippage,
        )
    except Exception:
        # Aggregation is best-effort; fall back to minimal snapshot if anything goes wrong
        return PortfolioSnapshot(
            state=state,
            totals=totals,
            exposure_by_currency=tuple(),
            fees_total=0.0,
            slippage_total=0.0,
        )


__all__ = [
    "CanonicalKey",
    "Position",
    "PortfolioState",
    "PortfolioSnapshot",
    "PortfolioTotals",
    "build_portfolio_snapshot",
]
