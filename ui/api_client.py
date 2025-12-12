# ui/api_client.py
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Mapping, TypedDict

import pandas as pd
import requests  # type: ignore[import-untyped]


# =====================================================
#  Base API Configuration
# =====================================================

from config import settings

API_BASE_URL = settings.saas_api_base_url
API_KEY = settings.saas_api_key


DEFAULT_BASE_CURRENCY = "ILS"
DEFAULT_FX_RATES: Mapping[str, float] = {"USD/ILS": 3.6, "ILS/USD": 1 / 3.6}


class ApiError(Exception):
    """שגיאה כללית בקריאת ה-SaaS API של DemoBot."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        *,
        error_type: str = "unknown",
        path: str | None = None,
        details: Any | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.error_type = error_type
        self.path = path
        self.details = details
        super().__init__(f"[{status_code}] {error_type}: {message}")

    def __str__(self) -> str:  # כשעושים str(e)
        base = self.message
        if self.status_code is not None:
            base += f" (HTTP {self.status_code})"
        if self.path:
            base += f" @ {self.path}"
        return base


class PortfolioPosition(TypedDict):
    symbol: str
    quantity: float
    price: float
    currency: str
    instrument_type: str


class PortfolioGreeks(TypedDict):
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


class PortfolioRisk(TypedDict, total=False):
    pv: float
    currency: str
    greeks: PortfolioGreeks
    margin: Dict[str, Any]
    var: Dict[str, Any]


class PortfolioValuationResponse(TypedDict, total=False):
    total_value: float
    currency: str
    portfolio_risk: PortfolioRisk | None


class PortfolioValuationRequest(TypedDict):
    positions: list[PortfolioPosition]
    fx_rates: Mapping[str, float]
    base_currency: str
    margin_rate: float
    margin_minimum: float
    var_horizon_days: int
    var_confidence: float
    var_daily_volatility: float


def _build_headers() -> Dict[str, str]:
    """Headers אחידים לכל הקריאות ל-API."""
    return {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
    }


# =====================================================
#  Generic HTTP Wrapper
# =====================================================


def _request_json(
    method: str,
    path: str,
    json: Dict[str, Any] | None = None,
    timeout: int = 30,
) -> Any:
    """
    עטיפה ל-requests שמרכזת:
    - בניית URL ו-Headers
    - טיפול בשגיאות רשת / timeout
    - מיפוי קודי HTTP לשגיאות ApiError ברורות
    """
    url = f"{API_BASE_URL.rstrip('/')}{path}"

    try:
        resp = requests.request(
            method=method.upper(),
            url=url,
            json=json,
            headers=_build_headers(),
            timeout=timeout,
        )
    except requests.exceptions.Timeout as exc:
        # חריגה מזמן – חשוב ללקוח מוסדי
        raise ApiError(
            "חריגה מזמן ההמתנה לשרת ה-API (timeout). נסי שוב בעוד מספר שניות.",
            path=path,
            error_type="timeout",
        ) from exc
    except requests.exceptions.RequestException as exc:
        # שגיאת רשת כללית (DNS / חיבור / SSL וכו')
        raise ApiError(
            f"שגיאת רשת בזמן ניסיון להתחבר ל-API: {exc}",
            path=path,
            error_type="network",
        ) from exc

    status = resp.status_code

    # אם לא 2xx – נמפה את קוד ה-HTTP לסוג שגיאה ברור
    if not (200 <= status < 300):
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text

        if status in (401, 403):
            msg = "שגיאת התחברות ל-API (401/403). בדקי API Key או הרשאות."
            err_type = "auth"
        elif status == 422:
            msg = "שגיאת ולידציה (422) בנתונים שנשלחו ל-API – כנראה שדה חסר או ערך לא תקין."
            err_type = "validation"
        elif status >= 500:
            msg = (
                "שגיאת שרת בצד המנוע (5xx). ניתן לנסות שוב, ואם זה נמשך – לפנות לתמיכה."
            )
            err_type = "server"
        else:
            msg = f"שגיאת API (HTTP {status})."
            err_type = "http"

        raise ApiError(
            msg,
            status_code=status,
            path=path,
            error_type=err_type,
            details=detail,
        )

    # נסה לפענח JSON תקין
    try:
        return resp.json()
    except Exception as e:
        raise ApiError(
            "התקבלה תשובה לא תקינה מה-API (JSON לא קריא).",
            status_code=status,
            path=path,
            error_type="decode",
            details=resp.text,
        ) from e


# =====================================================
# Helper – Options Legs
# =====================================================


def _legs_df_to_list(legs_df: pd.DataFrame) -> List[Dict[str, Any]]:
    legs_list: List[Dict[str, Any]] = []

    if legs_df is None or legs_df.empty:
        return legs_list

    for _, row in legs_df.iterrows():
        side_raw = str(row.get("side", "")).upper()
        cp_raw = str(row.get("cp", "")).upper()

        if side_raw == "BUY":
            side = "long"
        elif side_raw == "SELL":
            side = "short"
        else:
            continue

        if cp_raw == "C":
            cp = "CALL"
        elif cp_raw == "P":
            cp = "PUT"
        else:
            continue

        legs_list.append(
            {
                "side": side,
                "cp": cp,
                "strike": float(row.get("strike", 0)),
                "quantity": int(row.get("quantity", 0)),
                "premium": float(row.get("premium", 0)),
            }
        )

    return legs_list


# =====================================================
# /v1/portfolio/valuate
# =====================================================


def valuate_portfolio(
    *,
    positions: list[PortfolioPosition],
    base_currency: str = DEFAULT_BASE_CURRENCY,
    fx_rates: Mapping[str, float] | None = None,
    margin_rate: float = 0.15,
    margin_minimum: float = 0.0,
    var_horizon_days: int = 1,
    var_confidence: float = 0.99,
    var_daily_volatility: float = 0.02,
) -> PortfolioValuationResponse:
    payload: PortfolioValuationRequest = {
        "positions": positions,
        "base_currency": base_currency or DEFAULT_BASE_CURRENCY,
        "fx_rates": dict(DEFAULT_FX_RATES) if fx_rates is None else dict(fx_rates),
        "margin_rate": margin_rate,
        "margin_minimum": margin_minimum,
        "var_horizon_days": var_horizon_days,
        "var_confidence": var_confidence,
        "var_daily_volatility": var_daily_volatility,
    }

    return _request_json(
        method="POST",
        path="/v1/portfolio/valuate",
        json=dict(payload),
        timeout=30,
    )


# =====================================================
# /v1/position/price
# =====================================================


def price_position(legs_df: pd.DataFrame) -> Dict[str, Any]:
    legs_payload = _legs_df_to_list(legs_df)
    payload = {"legs": legs_payload}
    return _request_json("POST", "/v1/position/price", json=payload, timeout=20)


# =====================================================
# /v1/position/analyze
# =====================================================


def analyze_position_v1(
    legs_df: pd.DataFrame,
    *,
    spot: float,
    lower_factor: float,
    upper_factor: float,
    num_points: int,
    dte_days: int,
    iv: float,
    r: float,
    q: float,
    contract_multiplier: float,
    invested_override: float | None = None,
) -> Dict[str, Any]:
    legs_list = _legs_df_to_list(legs_df)

    invested_override_value: float | None = None
    if invested_override is not None and invested_override != 0:
        invested_override_value = float(invested_override)

    payload = {
        "legs": legs_list,
        "market": {
            "spot": float(spot),
            "lower_factor": float(lower_factor),
            "upper_factor": float(upper_factor),
            "num_points": int(num_points),
            "dte_days": int(dte_days),
            "iv": float(iv),
            "r": float(r),
            "q": float(q),
            "contract_multiplier": float(contract_multiplier),
            "invested_capital_override": invested_override_value,
        },
    }

    return _request_json("POST", "/v1/position/analyze", json=payload, timeout=30)


# =====================================================
# /v1/chain/generate
# =====================================================


def generate_chain_v1(
    symbol: str,
    expiry: date,
    spot: float,
    r: float,
    q: float,
    iv: float,
    strikes_count: int,
    step_pct: float,
) -> pd.DataFrame:
    payload = {
        "symbol": symbol,
        "expiry": expiry.isoformat(),
        "spot": float(spot),
        "r": float(r),
        "q": float(q),
        "iv": float(iv),
        "strikes_count": int(strikes_count),
        "step_pct": float(step_pct),
    }

    data = _request_json("POST", "/v1/chain/generate", json=payload, timeout=30)

    records = data.get("items", data)
    df = pd.DataFrame(records)

    if df.empty:
        raise ApiError("Empty chain received from API")

    return df


# =====================================================
# FX – /v1/fx/forward/analyze
# =====================================================
def analyze_fx_forward_v1(
    base_ccy: str,
    quote_ccy: str,
    notional: float,
    direction: str,  # "BUY" / "SELL"
    spot: float,
    forward_rate: float,
    valuation_date: date,
    maturity_date: date,
    curve_min_pct: float = -0.1,
    curve_max_pct: float = 0.1,
    curve_points: int = 101,
) -> Dict[str, Any]:
    """קריאה ל-POST /v1/fx/forward/analyze"""

    url = f"{API_BASE_URL.rstrip('/')}/v1/fx/forward/analyze"

    payload = {
        "base_ccy": base_ccy,
        "quote_ccy": quote_ccy,
        "notional": notional,
        "direction": direction,
        "spot": spot,
        "forward_rate": forward_rate,
        "valuation_date": valuation_date.isoformat(),
        "maturity_date": maturity_date.isoformat(),
        "curve_min_pct": curve_min_pct,
        "curve_max_pct": curve_max_pct,
        "curve_points": curve_points,
    }

    try:
        resp = requests.post(
            url,
            json=payload,
            headers=_build_headers(),
            timeout=10,
        )
    except requests.exceptions.Timeout as exc:
        raise ApiError(
            "חריגה מזמן ההמתנה לשרת ה-FX (timeout).",
            path="/v1/fx/forward/analyze",
            error_type="timeout",
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise ApiError(
            f"שגיאת רשת בקריאת FX API: {exc}",
            path="/v1/fx/forward/analyze",
            error_type="network",
        ) from exc

    status = resp.status_code

    if status >= 400:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text

        if status in (401, 403):
            msg = "שגיאת התחברות ל-FX API (401/403)."
            err_type = "auth"
        elif status == 422:
            msg = "שגיאת ולידציה בעסקת FX (422) – אחד הפרמטרים לא תקין."
            err_type = "validation"
        elif status >= 500:
            msg = "שגיאת שרת במנוע ה-FX (5xx)."
            err_type = "server"
        else:
            msg = f"שגיאת FX API (HTTP {status})."
            err_type = "http"

        raise ApiError(
            msg,
            status_code=status,
            path="/v1/fx/forward/analyze",
            error_type=err_type,
            details=detail,
        )

    return resp.json()


# =====================================================
# Strategy Planner – /v1/strategy/suggest
# =====================================================


def suggest_strategies_v1(
    goals: Dict[str, Any],
    market: Dict[str, Any],
) -> Dict[str, Any]:
    """
    לקוח ל-POST /v1/strategy/suggest.

    expected response:
    {
      "strategies": [
        {
          "name": "...",
          "subtype": "...",
          "legs": [...],
          "payoff_summary": {...},
          "risk_score": 0.0-1.0,
          "explanation_tokens": [...]
        },
        ...
      ]
    }
    """
    payload = {
        "goals": goals,
        "market": market,
    }

    return _request_json(
        method="POST",
        path="/v1/strategy/suggest",
        json=payload,
        timeout=30,
    )


def simulate_strategy_v1(
    *,
    symbol: str,
    spot: float,
    iv: float,
    r: float,
    q: float,
    dte: int,
    num_points: int,
    contract_multiplier: float,
) -> pd.DataFrame:
    """
    קריאת SaaS ליצירת שרשרת אופציות / סימולטור אסטרטגיה.

    הערה: נתיב ה־API כאן הוא דוגמה. כשיהיה לך endpoint אמיתי,
    נעדכן את ה-path ואת המבנה לפי מה שהשרת מחזיר.
    """
    payload: Dict[str, Any] = {
        "symbol": symbol,
        "spot": spot,
        "iv": iv,
        "r": r,
        "q": q,
        "dte_days": dte,
        "num_points": num_points,
        "contract_multiplier": contract_multiplier,
    }

    data = _request_json(
        method="POST",
        path="/v1/strategy/simulate",  # אפשר יהיה לעדכן בעתיד אם תבחרי נתיב אחר
        json=payload,
    )

    # נניח שה־API מחזיר {"chain": [...]} או רשימה ישירות
    chain_rows = data.get("chain") if isinstance(data, dict) else data
    return pd.DataFrame(chain_rows or [])


# =====================================================
# Portfolio valuation – /v1/portfolio/valuate
# =====================================================


def valuate_portfolio_raw(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke the public portfolio valuation endpoint with a prebuilt payload."""

    return _request_json(
        method="POST",
        path="/v1/portfolio/valuate",
        json=payload,
        timeout=30,
    )
