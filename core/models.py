# Layer: foundation
# core/models.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional, List

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

    def is_call(self) -> bool:
        return self.cp == "CALL"

    def is_put(self) -> bool:
        return self.cp == "PUT"
    
    def copy(self) -> "Leg":
        """Return a shallow copy of the leg."""
        return replace(self)

@dataclass
class Position:
    """
    פוזיציית אופציות – אוסף רגליים.
    זה האובייקט המרכזי לכל מנוע החישוב החדש.
    """

    legs: List[Leg]

    def calls(self) -> List[Leg]:
        return [leg for leg in self.legs if leg.cp == "CALL"]

    def puts(self) -> List[Leg]:
        return [leg for leg in self.legs if leg.cp == "PUT"]

    def total_quantity(self) -> int:
        return sum(leg.quantity for leg in self.legs)

    def copy(self) -> "Position":
        return Position(
            # כל שאר השדות כמו היום...
            legs=[leg.copy() for leg in self.legs],
        )


@dataclass
class StrategyInfo:
    """
    מידע על אסטרטגיה – משמש גם לזיהוי אוטומטי, גם לבחירה ידנית.
    """

    name: str
    subtype: Optional[str] = None
    description: Optional[str] = None
