# Layer: services
# brokers/sim.py
# סימולטור אופציות – יוצר שרשרת מלאכותית לפי Black–Scholes
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm
from datetime import date


def black_scholes_price(cp: str, S, K, T, r, q, sigma):
    """מחיר אופציה לפי נוסחת Black-Scholes."""
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if cp.upper() == "CALL":
        price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
    return price


def black_scholes_greeks(cp: str, S, K, T, r, q, sigma):
    """חישוב Greeks בסיסיים."""
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    pdf_d1 = norm.pdf(d1)

    delta = np.exp(-q * T) * (norm.cdf(d1) if cp == "CALL" else norm.cdf(d1) - 1)
    gamma = np.exp(-q * T) * pdf_d1 / (S * sigma * np.sqrt(T))
    theta = (
        -S * pdf_d1 * sigma * np.exp(-q * T) / (2 * np.sqrt(T))
        - r * K * np.exp(-r * T) * (norm.cdf(d2) if cp == "CALL" else norm.cdf(-d2))
        + q * S * np.exp(-q * T) * (norm.cdf(d1) if cp == "CALL" else norm.cdf(-d1))
    )
    vega = S * np.exp(-q * T) * pdf_d1 * np.sqrt(T)
    rho = K * T * np.exp(-r * T) * (norm.cdf(d2) if cp == "CALL" else -norm.cdf(-d2))
    return delta, gamma, theta, vega, rho


def get_option_chain(symbol, expiry, spot, r, q, iv, strikes_count=9, step_pct=2.0):
    """יוצר שרשרת אופציות סינתטית סביב הספוט."""
    strikes_count = int(strikes_count)
    step_pct = float(step_pct) / 100.0
    iv = float(iv)
    r, q = float(r), float(q)

    # נחשב זמן לפקיעה בשנים (בקירוב)
    T = max((expiry - pd.Timestamp.today().date()).days / 365.0, 0.001)

    half = strikes_count // 2
    strikes = [spot * (1 + step_pct * (i - half)) for i in range(strikes_count)]

    rows = []
    for K in strikes:
        for cp in ["CALL", "PUT"]:
            price = black_scholes_price(cp, spot, K, T, r, q, iv)
            delta, gamma, theta, vega, rho = black_scholes_greeks(
                cp, spot, K, T, r, q, iv
            )
            rows.append(
                {
                    "symbol": symbol,
                    "expiry": expiry,
                    "strike": round(K, 2),
                    "cp": cp,
                    "price": round(price, 4),
                    "delta": round(delta, 4),
                    "gamma": round(gamma, 4),
                    "theta": round(theta, 4),
                    "vega": round(vega, 4),
                    "rho": round(rho, 4),
                }
            )

    return pd.DataFrame(rows)


def is_connected():
    """תמיד מחובר (סימולטור)."""
    return True


def connect():
    """לא נדרש חיבור אמיתי."""
    pass


class SimBroker:
    """ספק 'דמו' שמייצר שרשרת אופציות מלאכותית, בפורמט שמצופה ע"י app.py."""

    def __init__(self) -> None:
        self._connected = True

    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        self._connected = True

    def get_option_chain(
        self,
        symbol: str,
        expiry: date,
        spot: float,
        r: float,
        q: float,
        iv: float,
        strikes_count: int,
        step_pct: float,
    ) -> pd.DataFrame:
        # בניית סטרייקים סביב הספוט
        half = strikes_count // 2
        steps = np.arange(-half, half + 1)
        strikes = np.round(spot * (1 + steps * (step_pct / 100.0)), 2)

        # "תמחור" דמה: מחיר נמוך סביב ATM, עולה כשהולכים רחוק
        def fake_price(k: float) -> float:
            dist = abs(k - spot) / max(spot, 1)
            base = max(0.5, 5 * dist * spot / 1000)  # משהו סביר
            return float(np.round(base, 2))

        rows = []
        for k in strikes:
            for cp in ("CALL", "PUT"):
                rows.append(
                    {
                        "strike": float(k),
                        "cp": cp,
                        "price": fake_price(k),
                        # אפשר להרחיב בהמשך לגריקים:
                        "delta": 0.0,
                        "gamma": 0.0,
                        "theta": 0.0,
                        "vega": 0.0,
                        "rho": 0.0,
                    }
                )
        return pd.DataFrame(rows)
