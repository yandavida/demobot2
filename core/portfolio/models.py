from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Mapping, MutableMapping, Optional, Sequence, cast


# מטבע נתמך בשכבת V2
Currency = Literal["ILS", "USD"]


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
        """
        מייצג סכום במטבע נתון.

        אפשר להעביר:
        - ccy="USD" / "ILS"
        - או currency="USD" / "ILS"
        (לא שניהם ביחד ולא להשאיר את שניהם None)
        """
        if ccy is None and currency is None:
            raise TypeError("Either ccy or currency must be provided.")
        if ccy is not None and currency is not None:
            raise TypeError("Specify only one of ccy or currency.")

        raw = ccy if ccy is not None else currency
        assert raw is not None

        # נרמול: אם הגיע מחרוזת -> אותיות גדולות, ואז cast ל-Currency
        if isinstance(raw, str):
            normalized = raw.upper()
        else:
            normalized = raw

        resolved_currency = cast(Currency, normalized)

        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "ccy", resolved_currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.ccy}"

    @property
    def currency(self) -> Currency:
        return self.ccy

    @classmethod
    def zero(cls, ccy: Currency | str) -> "Money":
        """
        מחזיר Money עם סכום 0 במטבע נתון.
        מאפשר גם מחרוזת ("usd"/"USD"/"ils" וכו') וגם Currency.
        """
        if isinstance(ccy, str):
            normalized = cast(Currency, ccy.upper())
        else:
            normalized = ccy
        return cls(amount=0.0, ccy=normalized)


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


@dataclass(frozen=True)
class Portfolio:
    positions: Sequence[Position] = field(default_factory=list)
    # כרגע נשארים עם str כ-base currency כלפי חוץ (פשוט "USD"/"ILS")
    base_currency: str = "USD"
    cash_balances: MutableMapping[str, float] = field(default_factory=dict)

    def with_position(self, position: Position) -> "Portfolio":
        """
        מחזיר פורטפוליו חדש עם הפוזיציה החדשה,
        בלי לשנות את האובייקט הנוכחי (איממוטביליות לוגית).
        """
        positions = list(self.positions) + [position]
        return Portfolio(
            positions=positions,
            base_currency=self.base_currency,
            cash_balances=dict(self.cash_balances),
        )
