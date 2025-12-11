from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Mapping, MutableMapping, Optional, Sequence, cast


# ---------------------------------------------------------------------------
# Currency literal
# ---------------------------------------------------------------------------

Currency = Literal["ILS", "USD"]


def _normalize_currency(
    value: Currency | str | None,
    *,
    field_name: str = "currency",
) -> Currency:
    """
    Normalize an incoming currency value (Literal/str/None) to the Currency
    literal type ("ILS" / "USD"), with validation.

    This helper is intentionally a bit permissive at the boundary, so that
    public APIs can accept both raw strings and the Currency literal, but it
    always returns a normalized Currency.
    """
    if value is None:
        raise TypeError(f"{field_name} must not be None")

    if isinstance(value, str):
        normalized = value.upper()
    else:
        normalized = value

    if normalized not in ("ILS", "USD"):
        raise ValueError(f"Unsupported {field_name} {value!r}; expected 'ILS' or 'USD'.")

    return cast(Currency, normalized)


# ---------------------------------------------------------------------------
# Money
# ---------------------------------------------------------------------------

@dataclass(frozen=True, init=False)
class Money:
    amount: float
    ccy: Currency

    def __init__(
        self,
        amount: float,
        ccy: Currency | str | None = None,
        currency: Currency | str | None = None,
    ) -> None:
        # לא מאפשרים להעביר גם ccy וגם currency
        if ccy is not None and currency is not None:
            raise TypeError("Specify only one of 'ccy' or 'currency'.")
        if ccy is None and currency is None:
            raise TypeError("Either 'ccy' or 'currency' must be provided.")

        raw_value: Currency | str | None = ccy if ccy is not None else currency
        resolved_ccy = _normalize_currency(raw_value, field_name="Money.currency")

        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "ccy", resolved_ccy)

    def __str__(self) -> str:
        return f"{self.amount} {self.ccy}"

    @property
    def currency(self) -> Currency:
        return self.ccy

    @classmethod
    def zero(cls, ccy: Currency | str) -> "Money":
        resolved_ccy = _normalize_currency(ccy, field_name="Money.zero.ccy")
        return cls(amount=0.0, ccy=resolved_ccy)


# ---------------------------------------------------------------------------
# Market snapshot / Position
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MarketSnapshot:
    prices: Mapping[str, float]
    as_of: Optional[datetime] = None

    def get_price(self, symbol: str) -> Optional[float]:
        return self.prices.get(symbol)


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    instrument_type: str = "equity"
    metadata: Mapping[str, object] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Portfolio:
    positions: Sequence[Position] = field(default_factory=list)

    # מאפשרים גם Currency וגם str כלפי חוץ,
    # אבל פנימית תמיד מנרמלים ל-Currency עם _normalize_currency
    base_currency: Currency | str = "USD"

    # מאזנים נשמרים כבר אחרי נרמול, עם מפתח מסוג Currency
    cash_balances: MutableMapping[Currency, float] = field(default_factory=dict)

    def with_position(self, position: Position) -> "Portfolio":
        positions = list(self.positions) + [position]
        return Portfolio(
            positions=positions,
            base_currency=self.base_currency,
            cash_balances=dict(self.cash_balances),
        )

    def normalized_base_currency(self) -> Currency:
        return _normalize_currency(
            self.base_currency,
            field_name="Portfolio.base_currency",
        )

    def normalized_cash_balances(self) -> MutableMapping[Currency, float]:
        # מחזירים העתק רדוד כדי לא לחשוף את המילון הפנימי
        return dict(self.cash_balances)
