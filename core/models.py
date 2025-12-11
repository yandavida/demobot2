# Layer: foundation
# core/models.py
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal, Optional, List, cast

# סוג אופציה
CP = Literal["CALL", "PUT"]

# צד הפוזיציה
Side = Literal["long", "short"]


# ============================================================
#   OptionQuote – ציטוט אופציה בודדת
# ============================================================
@dataclass(frozen=True)
class OptionQuote:
    """ציטוט אופציה בודדת מתוך השרשרת."""

    strike: float
    cp: CP  # "CALL" | "PUT"
    price: float  # מחיר mid / סימולטיבי
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None


# ============================================================
#   IronCondorInput – פרמטרים לאיירון קונדור
# ============================================================
@dataclass(frozen=True)
class IronCondorInput:
    """פרמטרים להצגת/חישוב איירון קונדור."""

    short_put_strike: float
    long_put_strike: float
    short_call_strike: float
    long_call_strike: float
    qty: int = 1
    multiplier: int = 100
    spot: float = 0.0  # לשימוש בגרף/קונטקסט


# ============================================================
#   IronCondorResult – תוצאה מלאה של חישוב איירון קונדור
# ============================================================
@dataclass(frozen=True)
class IronCondorResult:
    """תוצאת החישוב של איירון קונדור — גרסה מלאה תואמת strategies.py"""

    # ---- מחירי אופציות (לצורך חישוב) ----
    price_sp: float
    price_lp: float
    price_sc: float
    price_lc: float

    # ---- מבנה כנפיים ----
    put_wing: float
    call_wing: float
    worst_wing: float

    # ---- תוצאות פר יחידה ----
    net_credit: float
    max_profit_per_unit: float
    max_loss_per_unit: float

    # ---- תוצאות ברוטו (כל הכמויות) ----
    gross_max_profit: float
    gross_max_loss: float

    # ---- נקודות איזון ----
    lower_be: float
    upper_be: float


# ============================================================
#   Leg – רגל אחת בפוזיציה
#   Position – אוסף רגליים
#   StrategyInfo – מידע על אסטרטגיה (מזוהה/נבחרת)
# ============================================================


@dataclass
class Leg:
    """
    רגל אחת של פוזיציית אופציות כללית.
    מייצג שורה בטבלה במסך הבנייה החופשית.
    """

    side: Side  # "long" / "short"
    cp: CP  # "CALL" / "PUT"
    strike: float
    quantity: int = 1
    premium: float = 0.0  # פרמיה ליחידה אחת

    def __init__(
        self,
        *,
        side: Side | None = None,
        cp: CP | None = None,
        strike: float,
        quantity: int = 1,
        premium: float = 0.0,
        # Aliases
        kind: str | None = None,
        direction: str | None = None,
        qty: int | None = None,
    ) -> None:
        resolved_side = side or direction
        if resolved_side is None:
            raise TypeError("Leg requires either 'side' or 'direction'.")
        normalized_side = resolved_side.lower()
        if normalized_side not in ("long", "short"):
            raise ValueError(f"Invalid side/direction value: {resolved_side}")

        resolved_cp = cp or kind
        if resolved_cp is None:
            raise TypeError("Leg requires either 'cp' or 'kind'.")
        normalized_cp = resolved_cp.upper()
        if normalized_cp not in ("CALL", "PUT"):
            raise ValueError(f"Invalid cp/kind value: {resolved_cp}")

        resolved_quantity = qty if qty is not None else quantity

        self.side = cast(Side, normalized_side)
        self.cp = cast(CP, normalized_cp)
        self.strike = strike
        self.quantity = resolved_quantity
        self.premium = premium

    def copy(self) -> "Leg":
        return replace(self)

    def is_call(self) -> bool:
        return self.cp == "CALL"

    def is_put(self) -> bool:
        return self.cp == "PUT"


@dataclass
class Position:
    """
    פוזיציית אופציות – אוסף רגליים.
    זה האובייקט המרכזי לכל מנוע החישוב החדש.
    """

    legs: List[Leg]
    underlying: Optional[str] = None

    def calls(self) -> List[Leg]:
        return [leg for leg in self.legs if leg.cp == "CALL"]

    def puts(self) -> List[Leg]:
        return [leg for leg in self.legs if leg.cp == "PUT"]

    def total_quantity(self) -> int:
        return sum(leg.quantity for leg in self.legs)

    def copy(self) -> "Position":
        return Position(
            legs=[leg.copy() for leg in self.legs],
            underlying=self.underlying,
        )


@dataclass
class StrategyInfo:
    """
    מידע על אסטרטגיה – משמש גם לזיהוי אוטומטי, גם לבחירה ידנית.
    """

    name: str
    subtype: Optional[str] = None
    description: Optional[str] = None
