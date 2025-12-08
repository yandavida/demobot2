# core/strategies_registry.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import pandas as pd


@dataclass
class StrategyDefinition:
    """
    מייצג אסטרטגיה ב־UI:
    - name  : שם פנימי (id)
    - label : מה שיופיע ב־selectbox
    - render: פונקציה שמקבלת df_view ומציירת את כל ה־UI של האסטרטגיה
    """

    name: str
    label: str
    render: Callable[[pd.DataFrame], None]


def get_strategies() -> Sequence[StrategyDefinition]:
    """
    מחזיר רשימת אסטרטגיות זמינות.
    שימי לב: ה־import ל־render_ic_sandbox נעשה בתוך הפונקציה
    כדי למנוע imports מעגליים.
    """
    from sandbox.ic_sandbox import render_ic_sandbox

    strategies: list[StrategyDefinition] = [
        StrategyDefinition(
            name="iron_condor_quick",
            label="Iron Condor (quick sandbox)",
            render=render_ic_sandbox,
        ),
        # פה בעתיד נוסיף אסטרטגיות נוספות
        # StrategyDefinition(...),
    ]

    return strategies


# core/strategies.py

from typing import Tuple
import numpy as np

from core.models import IronCondorResult


def _mid_price(df_view: pd.DataFrame, strike: float, cp: str) -> float:
    """
    מחזיר mid-price של אופציה לפי strike ו-type (CALL/PUT).
    אם לא נמצאה אופציה מתאימה – נזרקת שגיאה.
    """
    mask = (df_view["strike"] == strike) & (df_view["cp"].str.upper() == cp.upper())
    row = df_view.loc[mask].head(1)

    if row.empty:
        raise ValueError(f"לא נמצאה אופציה עבור strike={strike}, cp={cp}")

    bid = float(row["bid"].iloc[0]) if "bid" in row else float(row["price"].iloc[0])
    ask = float(row["ask"].iloc[0]) if "ask" in row else float(row["price"].iloc[0])

    # אם אין bid/ask – נשתמש ב-"price" כ-mid
    if "bid" not in row or "ask" not in row:
        return float(row["price"].iloc[0])

    return 0.5 * (bid + ask)


def _validate_prices(*prices: float) -> None:
    """
    מוודא שאין None במחירים.
    """
    for p in prices:
        if p is None:
            raise ValueError("חסר מחיר עבור אחת הרגליים של האיירון קונדור.")


def iron_condor_metrics(
    df_view: pd.DataFrame,
    sp: float,  # short put  strike
    lp: float,  # long  put  strike
    sc: float,  # short call strike
    lc: float,  # long  call strike
    qty: int,
    mult: int,
    spot: float,
) -> Tuple[IronCondorResult, pd.DataFrame]:
    """
    מחשב את המטריקות של Iron Condor ומחזיר:
    (IronCondorResult, Payoff DataFrame עם עמודות ['S','P/L']).
    """

    # --- prices ---
    price_sp = _mid_price(df_view, sp, "PUT")  # short -> credit
    price_lp = _mid_price(df_view, lp, "PUT")  # long  -> debit
    price_sc = _mid_price(df_view, sc, "CALL")  # short -> credit
    price_lc = _mid_price(df_view, lc, "CALL")  # long  -> debit
    _validate_prices(price_sp, price_lp, price_sc, price_lc)

    # --- structure: wings ---
    put_wing = abs(sp - lp)
    call_wing = abs(lc - sc)
    worst_wing = max(put_wing, call_wing)

    # --- credit & per-unit P/L ---
    net_credit = (price_sp + price_sc) - (price_lp + price_lc)
    max_profit_per_unit = net_credit
    max_loss_per_unit = max(0.0, worst_wing - net_credit)  # חיובי

    # --- totals ---
    gross_max_profit = max_profit_per_unit * qty * mult
    gross_max_loss = max_loss_per_unit * qty * mult  # חיובי

    # --- breakevens ---
    lower_be = sp - net_credit
    upper_be = sc + net_credit

    # --- payoff curve (expiry) ---
    s_min = min(lp, sp, sc, lc, spot) * 0.9
    s_max = max(lp, sp, sc, lc, spot) * 1.1
    S = np.linspace(s_min, s_max, 300)

    def payoff_put(k: float, price: float, short: bool = True) -> np.ndarray:
        intrinsic = np.maximum(k - S, 0.0)
        return (price - intrinsic) if short else (intrinsic - price)

    def payoff_call(k: float, price: float, short: bool = True) -> np.ndarray:
        intrinsic = np.maximum(S - k, 0.0)
        return (price - intrinsic) if short else (intrinsic - price)

    pl = (
        (
            payoff_put(sp, price_sp, short=True)  # short put
            + payoff_put(lp, price_lp, short=False)  # long  put
            + payoff_call(sc, price_sc, short=True)  # short call
            + payoff_call(lc, price_lc, short=False)  # long  call
        )
        * qty
        * mult
    )

    df_pay = pd.DataFrame({"S": S, "P/L": pl})

    result = IronCondorResult(
        price_sp=price_sp,
        price_lp=price_lp,
        price_sc=price_sc,
        price_lc=price_lc,
        put_wing=put_wing,
        call_wing=call_wing,
        worst_wing=worst_wing,
        net_credit=net_credit,
        max_profit_per_unit=max_profit_per_unit,
        max_loss_per_unit=max_loss_per_unit,
        gross_max_profit=gross_max_profit,
        gross_max_loss=gross_max_loss,
        lower_be=lower_be,
        upper_be=upper_be,
    )

    return result, df_pay


# ==========================================
# Vertical Spread Strategy
# ==========================================

from dataclasses import dataclass


@dataclass(frozen=True)
class VerticalSpreadInput:
    short_strike: float
    long_strike: float
    cp: str  # CALL or PUT
    qty: int = 1
    multiplier: int = 100


class VerticalSpreadStrategy:
    name = "Vertical Spread"

    def build_sidebar(self, df_view: pd.DataFrame) -> VerticalSpreadInput:
        st.subheader("Vertical Spread Parameters")

        strikes = sorted(df_view["strike"].unique().tolist())

        short = st.selectbox("Short strike", strikes, key="vs_short")
        long = st.selectbox("Long strike", strikes, key="vs_long")
        cp = st.radio("Type", ["CALL", "PUT"], key="vs_cp")

        return VerticalSpreadInput(
            short_strike=float(short),
            long_strike=float(long),
            cp=cp,
            qty=1,
            multiplier=100,
        )

    def compute(self, inp: VerticalSpreadInput, df_view: pd.DataFrame):
        """מחשב רווח/הפסד נקודתי לפי מחיר נכס"""

        if inp.cp == "CALL":
            # רווח מקסימלי
            max_profit = (inp.long_strike - inp.short_strike) * inp.multiplier * inp.qty
        else:
            # לרוב אותו דבר בספראד על PUT
            max_profit = (inp.short_strike - inp.long_strike) * inp.multiplier * inp.qty

        # פה אין חישוב פרמיום – נניח שהוא 0 בדוגמה הבסיסית
        net_credit = 0.0

        max_loss = -max_profit

        # Break-even (במקרה סימטרי)
        be = (inp.short_strike + inp.long_strike) / 2

        # payoff גרפי
        S = np.linspace(min(df_view["strike"]) - 50, max(df_view["strike"]) + 50, 200)

        if inp.cp == "CALL":
            payoff = np.where(
                S > inp.short_strike, (S - inp.short_strike), 0
            ) - np.where(S > inp.long_strike, (S - inp.long_strike), 0)
        else:
            payoff = np.where(
                S < inp.short_strike, (inp.short_strike - S), 0
            ) - np.where(S < inp.long_strike, (inp.long_strike - S), 0)

        payoff *= inp.multiplier * inp.qty

        df_pay = pd.DataFrame({"S": S, "P/L": payoff})

        return {
            "net_credit": net_credit,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "break_even": be,
            "df_pay": df_pay,
        }

    def render(self, df_view: pd.DataFrame):
        st.subheader("Vertical Spread Strategy")

        inp = self.build_sidebar(df_view)
        result = self.compute(inp, df_view)

        st.write("### Results")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Max profit", f"{result['max_profit']:.2f}")
        c2.metric("Max loss", f"{result['max_loss']:.2f}")
        c3.metric("Net credit", f"{result['net_credit']:.2f}")
        c4.metric("Break-even", f"{result['break_even']:.2f}")

        st.write("### Payoff chart")
        fig = px.line(result["df_pay"], x="S", y="P/L")
        st.plotly_chart(fig, use_container_width=True)
