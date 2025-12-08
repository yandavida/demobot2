# ui/analysis_mapper.py
from __future__ import annotations

import pandas as pd
from typing import Any, Dict


class AnalysisViewModel:
    """
    עטיפה שמדמה את האובייקט הישן שה-UI קיבל,
    אבל מבוססת על ה-dict שחוזר מתוך ה-API.
    """

    def __init__(self, raw: Dict[str, Any]):
        self.raw = raw

        # נותן גישה נוחה לשדות:
        self.pl_summary = raw.get("pl_summary", {})
        self.greeks = raw.get("greeks", {})
        self.risk_profile = raw.get("risk_level")
        self.strategy_info = {
            "name": raw.get("strategy_name"),
            "tags": raw.get("strategy_tags", []),
        }
        self.risk_warnings = raw.get("warnings", [])
        self.score = raw.get("score")
        self.explanation = raw.get("explanation")

        # שדות מתקדמים יותר – אם תרצי להוסיף בהמשך
        self.curve_df = self._build_curve_df()
        self.be_points = self._extract_be_points()
        self.scenarios_df = self._build_scenarios_df()

        # credits if exists
        self.net_credit = self.pl_summary.get("net_credit")
        self.total_credit = self.pl_summary.get("total_credit")

    # ------------------------------------------------------------------

    def _build_curve_df(self) -> pd.DataFrame:
        curve = self.pl_summary.get("curve")
        if curve:
            return pd.DataFrame(curve)
        return pd.DataFrame()

    def _extract_be_points(self):
        return self.pl_summary.get("break_even_points", [])

    def _build_scenarios_df(self) -> pd.DataFrame:
        scenarios = self.pl_summary.get("scenarios")
        if scenarios:
            return pd.DataFrame(scenarios)
        return pd.DataFrame()
