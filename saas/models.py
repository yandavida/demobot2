# saas/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class Customer:
    """ייצוג לקוח במערכת ה-SaaS."""

    id: str  # למשל: "cust_demo_1"
    name: str  # שם הלקוח / בית השקעות
    plan: PlanTier = PlanTier.FREE
    is_active: bool = True


@dataclass
class CustomerConfig:
    """
    קונפיגורציה פר-לקוח:
    מגבלות, פיצ'רים, פרמטרים למנועי סיכון וכו'.
    """

    customer_id: str
    display_name: str

    # דוגמאות לקונפיגורציה "פיננסית":
    default_underlying: str | None = None
    max_open_positions: int = 50
    max_notional_exposure: float | None = None  # אפשר להשאיר None בשלב זה

    # פיצ'רים / flags
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    risk_profile: str = "standard"  # "conservative" / "aggressive" וכו'

    # מקום להרחבות עתידיות
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApiKey:
    """API key פר-לקוח (או פר-אינטגרציה)."""

    key: str
    customer_id: str
    is_active: bool = True
