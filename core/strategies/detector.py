# Layer: strategies
# core/strategies/detector.py
from __future__ import annotations


from core.models import Position, StrategyInfo


def _is_vertical_spread(position: Position) -> bool:
    if len(position.legs) != 2:
        return False

    leg1, leg2 = position.legs

    # אותו סוג אופציה (CALL/PUT)
    if leg1.cp != leg2.cp:
        return False

    # צדדים הפוכים (לונג/שורט)
    if leg1.side == leg2.side:
        return False

    # אותה כמות
    if leg1.quantity != leg2.quantity:
        return False

    # סטרייקים שונים
    if leg1.strike == leg2.strike:
        return False

    return True


def _is_straddle(position: Position) -> bool:
    if len(position.legs) != 2:
        return False

    calls = [l for l in position.legs if l.cp == "CALL"]
    puts = [l for l in position.legs if l.cp == "PUT"]

    if len(calls) != 1 or len(puts) != 1:
        return False

    c = calls[0]
    p = puts[0]

    # אותו סטרייק, אותו צד, אותה כמות
    if c.strike != p.strike:
        return False
    if c.side != p.side:
        return False
    if c.quantity != p.quantity:
        return False

    return True


def _is_strangle(position: Position) -> bool:
    if len(position.legs) != 2:
        return False

    calls = [l for l in position.legs if l.cp == "CALL"]
    puts = [l for l in position.legs if l.cp == "PUT"]

    if len(calls) != 1 or len(puts) != 1:
        return False

    c = calls[0]
    p = puts[0]

    # אותו צד (לונג/לונג או שורט/שורט), סטרייקים שונים, אותה כמות
    if c.side != p.side:
        return False
    if c.strike == p.strike:
        return False
    if c.quantity != p.quantity:
        return False

    return True


def _is_iron_condor(position: Position) -> bool:
    if len(position.legs) != 4:
        return False

    calls = [l for l in position.legs if l.cp == "CALL"]
    puts = [l for l in position.legs if l.cp == "PUT"]

    if len(calls) != 2 or len(puts) != 2:
        return False

    calls_sorted = sorted(calls, key=lambda l: l.strike)
    puts_sorted = sorted(puts, key=lambda l: l.strike)

    put_low, put_high = puts_sorted[0], puts_sorted[1]
    call_low, call_high = calls_sorted[0], calls_sorted[1]

    # put_low < put_high < call_low < call_high
    if not (put_low.strike < put_high.strike < call_low.strike < call_high.strike):
        return False

    # פוט – long ב־low, short ב־high
    cond_puts = put_low.side == "long" and put_high.side == "short"

    # קול – short ב־low, long ב־high
    cond_calls = call_low.side == "short" and call_high.side == "long"

    if not (cond_puts and cond_calls):
        return False

    # כל הרגליים באותה כמות
    qtys = {l.quantity for l in position.legs}
    if len(qtys) != 1:
        return False

    return True


def detect_strategy(position: Position) -> StrategyInfo:
    """
    זיהוי אסטרטגיה לפי מבנה הרגליים בלבד.
    במקרה שלא מצליחים – StrategyInfo כללי.
    """
    if position.is_empty():
        return StrategyInfo(
            name="אין פוזיציה",
            description="לא קיימות רגליים בפוזיציה.",
        )

    # Iron Condor
    if _is_iron_condor(position):
        return StrategyInfo(
            name="Iron Condor",
            subtype="Credit",
            description="קונדור קלאסי – שורט תנודתיות, רווח מקסימלי בין שני הסטרייקים האמצעיים.",
        )

    # Vertical Spread
    if _is_vertical_spread(position):
        leg1, _ = position.legs
        name = "Vertical Call Spread" if leg1.cp == "CALL" else "Vertical Put Spread"
        return StrategyInfo(
            name=name,
            description="ספרד דו-רגלי באותו סוג אופציה (CALL/PUT) עם סטרייקים שונים.",
        )

    # Straddle
    if _is_straddle(position):
        leg = position.legs[0]
        subtype = "Long" if leg.side == "long" else "Short"
        return StrategyInfo(
            name=f"{subtype} Straddle",
            description="קנייה/מכירה סימטרית של CALL ו-PUT באותו סטרייק.",
        )

    # Strangle
    if _is_strangle(position):
        leg = position.legs[0]
        subtype = "Long" if leg.side == "long" else "Short"
        return StrategyInfo(
            name=f"{subtype} Strangle",
            description="קנייה/מכירה של CALL ו-PUT בסטרייקים שונים, אותה כמות.",
        )

    # ברירת מחדל – לא זוהתה אסטרטגיה סטנדרטית
    return StrategyInfo(
        name="פוזיציה מורכבת / לא מזוהה",
        description="לא זוהתה אסטרטגיה סטנדרטית, אבל ניתן לחשב P/L וגרפים כרגיל.",
    )
