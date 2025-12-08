"""Client utilities for calling the SaaS API from the UI layer."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd
import requests

DEFAULT_BASE_URL = "http://localhost:8000"
ENV_BASE_URL = "OPTIONS_API_BASE_URL"
ENV_API_KEY = "OPTIONS_API_KEY"


@dataclass
class ApiError(Exception):
    """Domain-specific API error with categorization for UI handling."""

    message: str
    error_type: str = "unknown"
    status_code: Optional[int] = None
    detail: Any | None = None

    def __str__(self) -> str:
        prefix = f"[{self.error_type}] " if self.error_type else ""
        suffix = f" (status={self.status_code})" if self.status_code else ""
        return f"{prefix}{self.message}{suffix}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "error_type": self.error_type,
            "status_code": self.status_code,
            "detail": self.detail,
        }


def _get_base_url() -> str:
    """Resolve the base URL for the SaaS API from environment."""

    return os.getenv(ENV_BASE_URL, DEFAULT_BASE_URL).rstrip("/")


def _build_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv(ENV_API_KEY)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _post_json(path: str, payload: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """POST JSON payload to the SaaS API with robust error mapping."""

    url = f"{_get_base_url()}{path}"

    try:
        resp = requests.post(url, json=payload, headers=_build_headers(), timeout=timeout)
    except requests.Timeout as exc:  # type: ignore[misc]
        raise ApiError("API request timed out", error_type="timeout") from exc
    except requests.RequestException as exc:  # type: ignore[misc]
        raise ApiError("API request failed", error_type="network") from exc

    if resp.status_code == 204:
        return {}

    try:
        data = resp.json()
    except ValueError:
        data = None

    if resp.status_code >= 400:
        error_type = "server" if resp.status_code >= 500 else "validation"
        if resp.status_code in (401, 403):
            error_type = "auth"
        elif resp.status_code == 408:
            error_type = "timeout"

        message: str
        if isinstance(data, dict) and "message" in data:
            message = str(data.get("message"))
        else:
            message = f"API request failed with status {resp.status_code}"

        raise ApiError(
            message=message,
            error_type=error_type,
            status_code=resp.status_code,
            detail=data,
        )

    if not isinstance(data, dict):
        raise ApiError(
            message="Unexpected API response format",
            error_type="server",
            status_code=resp.status_code,
            detail=data,
        )

    return data


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
    """Invoke the SaaS builder analysis endpoint (v1)."""

    if legs_df is None or legs_df.empty:
        raise ApiError("No position legs provided", error_type="validation")

    legs_payload = legs_df.to_dict(orient="records")

    payload: Dict[str, Any] = {
        "spot": spot,
        "lower_factor": lower_factor,
        "upper_factor": upper_factor,
        "num_points": num_points,
        "dte_days": dte_days,
        "iv": iv,
        "r": r,
        "q": q,
        "contract_multiplier": contract_multiplier,
        "legs": legs_payload,
    }

    if invested_override is not None:
        payload["invested_override"] = invested_override

    response = _post_json(
        "/api/v1/strategy/analyze",
        payload,
        timeout=15,
    )

    # רוב השירותים מחזירים את הנתונים תחת מפתח "data"; אם לא – נחזיר את הכל.
    return response.get("data", response)
