# Layer: engine
# core/strategy_brain.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Callable

import pandas as pd

from .models import Position
from .payoff import payoff_position, summarize_position_pl
from .greeks import calc_position_greeks
from .strategy_detector import detect_strategy
from .risk_engine import classify_risk_level
from .scoring import score_strategy
from .strategy_warnings import get_position_warnings
from .recommendation_explanations import build_explanation_for_strategy
from .strategy_recommendations import suggest_strategies_for_goals, position_to_legs_df
from .fx_math import FxDealInput, fx_forward_payoff_curve, summarize_fx_pl

# backtest_engine הוא מודול אופציונלי, לכן נטען אותו בעדינות
try:
    from .backtest_engine import BacktestConfig, BacktestResult, run_backtest  # type: ignore

    HAS_BACKTEST = True
except Exception:  # pragma: no cover
    BacktestConfig = Any  # type: ignore
    BacktestResult = Any  # type: ignore
    run_backtest = None  # type: ignore
    HAS_BACKTEST = False


# ================================================================
# 1. Enums – דומיינים ושכבות חישוב
# ================================================================


class Domain(str, Enum):
    """דומיין חישוב: אופציות, FX או שילוב."""

    OPTIONS = "options"
    FX = "fx"
    MIXED = "mixed"


class AnalysisLayer(str, Enum):
    """שכבות החישוב שאפשר להדליק/לכבות ללקוח."""

    PAYOFF = "payoff"
    GREEKS = "greeks"
    STRATEGY_DETECTION = "strategy_detection"
    RISK = "risk"
    SCORING = "scoring"
    WARNINGS = "warnings"
    RECOMMENDATIONS = "recommendations"
    BACKTEST = "backtest"


def default_layers() -> List[AnalysisLayer]:
    """ברירת המחדל – כל השכבות מלבד Backtest (כדי לא להכביד)."""
    return [
        AnalysisLayer.PAYOFF,
        AnalysisLayer.GREEKS,
        AnalysisLayer.STRATEGY_DETECTION,
        AnalysisLayer.RISK,
        AnalysisLayer.SCORING,
        AnalysisLayer.WARNINGS,
        AnalysisLayer.RECOMMENDATIONS,
        # BACKTEST נשארת אופציונלית
    ]


# ================================================================
# 2. Data Models – קונפיג ותוצאה אחידה
# ================================================================


@dataclass
class AnalysisConfig:
    """
    קונפיג כללי לניתוח:
    - domain: איזה דומיין (אופציות / FX / Mixed)
    - enabled_layers: אילו שכבות חישוב להפעיל
    - goals: מטרות הלקוח (hedge / income / speculative וכו')
    - backtest_config: קונפיג להרצת בק-טסט אם השכבה פעילה
    """

    domain: Domain = Domain.OPTIONS
    enabled_layers: List[AnalysisLayer] = field(default_factory=default_layers)
    goals: Optional[Dict[str, Any]] = None
    backtest_config: Optional[BacktestConfig] = None
    # שדה חופשי לדגלים נוספים (למשל רמת פירוט, רגולציה לפי לקוח וכו')
    flags: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """
    אובייקט תוצאה אחיד – זה מה שהמוח מחזיר לשכבת ה-UI או ה-API.
    שימי לב שכל השדות אופציונליים (מודולרי לחלוטין).
    """

    domain: Domain

    # שכבת PAYOFF
    payoff_df: Optional[pd.DataFrame] = None
    pl_summary: Optional[Dict[str, Any]] = None

    # נתוני עקומה ותרחישים – בעיקר מה-Backtest
    curve_df: Optional[pd.DataFrame] = None
    break_even_points: Optional[List[float]] = None
    scenarios_df: Optional[pd.DataFrame] = None

    # שכבת GREEKS
    greeks: Optional[Dict[str, Any]] = None

    # שכבת STRATEGY_DETECTION
    detected_strategy: Optional[Any] = None  # יכול להיות dict / dataclass

    # שכבת RISK
    risk_profile: Optional[Dict[str, Any]] = None

    # שכבת SCORING
    score: Optional[float] = None
    score_breakdown: Optional[Dict[str, Any]] = None

    # שכבת WARNINGS
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    # שכבת RECOMMENDATIONS
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    explanation: Optional[Any] = None  # יכול להיות str או dict הסבר

    # שכבת BACKTEST – תוצאת raw מה-engine
    backtest_result: Optional[BacktestResult] = None

    # שדה כללי להרחבות עתידיות / מטא דאטה
    meta: Dict[str, Any] = field(default_factory=dict)


# ================================================================
# 3. פרוטוקול Engine לדומיין – מאפשר מודולריות מלאה
# ================================================================


class DomainEngine(Protocol):
    """
    חוזה שכל Engine דומייני (אופציות / FX) צריך לממש.
    כך אפשר להוסיף FX, Fixed Income וכו' בלי לגעת ב-StrategyBrain.
    """

    domain: Domain

    def analyze(self, position: Position, config: AnalysisConfig) -> AnalysisResult: ...


# ================================================================
# 4. OptionsEngine – מימוש מלא לדומיין אופציות
# ================================================================


class OptionsEngine:
    """
    שכבת מוח לדומיין אופציות.
    משתמשת בכל המודולים הקיימים (payoff, greeks, risk_engine וכו').
    """

    domain: Domain = Domain.OPTIONS

    def __init__(
        self,
        backtest_runner: Optional[
            Callable[[Position, BacktestConfig], BacktestResult]
        ] = None,
    ) -> None:
        # אפשר להזריק פונקציית בק-טסט חיצונית כדי לשמור על מודולריות
        self._backtest_runner = backtest_runner or run_backtest

    def analyze(self, position: Position, config: AnalysisConfig) -> AnalysisResult:
        result = AnalysisResult(domain=self.domain)

        # --------------------------------------------------------
        # PAYOFF
        # --------------------------------------------------------
        if AnalysisLayer.PAYOFF in config.enabled_layers:
            payoff_df = payoff_position(position)
            pl_summary = summarize_position_pl(payoff_df)
            result.payoff_df = payoff_df
            result.pl_summary = pl_summary

        # --------------------------------------------------------
        # GREEKS
        # --------------------------------------------------------
        if AnalysisLayer.GREEKS in config.enabled_layers:
            greeks = calc_position_greeks(position)
            result.greeks = greeks

        # --------------------------------------------------------
        # STRATEGY DETECTION
        # --------------------------------------------------------
        if AnalysisLayer.STRATEGY_DETECTION in config.enabled_layers:
            detected = detect_strategy(position)
            result.detected_strategy = detected

        # --------------------------------------------------------
        # RISK
        # --------------------------------------------------------
        if AnalysisLayer.RISK in config.enabled_layers:
            risk_profile = classify_risk_level(
                position=position,
                greeks=result.greeks,
                pl_summary=result.pl_summary,
                detected_strategy=result.detected_strategy,
            )
            result.risk_profile = risk_profile

        # --------------------------------------------------------
        # SCORING
        # --------------------------------------------------------
        if AnalysisLayer.SCORING in config.enabled_layers:
            score_value, breakdown = score_strategy(
                position=position,
                risk_profile=result.risk_profile,
                detected_strategy=result.detected_strategy,
                greeks=result.greeks,
                pl_summary=result.pl_summary,
            )
            result.score = score_value
            result.score_breakdown = breakdown

        # --------------------------------------------------------
        # WARNINGS
        # --------------------------------------------------------
        if AnalysisLayer.WARNINGS in config.enabled_layers:
            warnings = get_position_warnings(
                position=position,
                greeks=result.greeks,
                pl_summary=result.pl_summary,
                detected_strategy=result.detected_strategy,
                risk_profile=result.risk_profile,
            )
            result.warnings = warnings

        # --------------------------------------------------------
        # RECOMMENDATIONS
        # --------------------------------------------------------
        if AnalysisLayer.RECOMMENDATIONS in config.enabled_layers:
            legs_df = position_to_legs_df(position)
            recommendations = suggest_strategies_for_goals(
                position_df=legs_df,
                goals=config.goals or {},
                risk_profile=result.risk_profile,
                detected_strategy=result.detected_strategy,
            )
            result.recommendations = recommendations

            explanation = build_explanation_for_strategy(
                position=position,
                detected_strategy=result.detected_strategy,
                risk_profile=result.risk_profile,
                score=result.score,
                goals=config.goals or {},
                recommendations=recommendations,
            )
            result.explanation = explanation

        # --------------------------------------------------------
        # BACKTEST (אופציונלי)
        # --------------------------------------------------------
        if (
            AnalysisLayer.BACKTEST in config.enabled_layers
            and config.backtest_config is not None
            and self._backtest_runner is not None
            and HAS_BACKTEST
        ):
            try:
                bt_result = self._backtest_runner(position, config.backtest_config)
                result.backtest_result = bt_result

                # ניסיון למפות שדות backtest לתוצאה האחידה
                if isinstance(bt_result, dict):
                    curve_df = bt_result.get("curve_df")
                    be_points = bt_result.get("break_even_points")
                    scenarios_df = bt_result.get("scenarios_df")
                    pl_summary_bt = bt_result.get("pl_summary")
                    greeks_bt = bt_result.get("greeks")
                    risk_bt = bt_result.get("risk")
                else:
                    curve_df = getattr(bt_result, "curve_df", None)
                    be_points = getattr(bt_result, "break_even_points", None)
                    scenarios_df = getattr(bt_result, "scenarios_df", None)
                    pl_summary_bt = getattr(bt_result, "pl_summary", None)
                    greeks_bt = getattr(bt_result, "greeks", None)
                    risk_bt = getattr(bt_result, "risk", None)

                if curve_df is not None:
                    result.curve_df = curve_df
                if be_points is not None:
                    result.break_even_points = be_points
                if scenarios_df is not None:
                    result.scenarios_df = scenarios_df

                if pl_summary_bt is not None and result.pl_summary is None:
                    result.pl_summary = pl_summary_bt
                if greeks_bt is not None and result.greeks is None:
                    result.greeks = greeks_bt
                if risk_bt is not None and result.risk_profile is None:
                    result.risk_profile = risk_bt

            except Exception as exc:  # pragma: no cover
                # נשמור הודעת שגיאה במטא, לא נשבור ללקוח את האפליקציה
                result.meta.setdefault("backtest_error", str(exc))

        return result


# ================================================================
# 5. FxEngine – שלד ראשוני לדומיין FX
# ================================================================


class FxEngine:
    """
    Engine ל-FX בלבד.

    ⚠️ חשוב:
    - כרגע מניחים שמועבר אובייקט מסוג FxDealInput או dict שמתאים לשדות שלו.
    - אין תלות ב-Position של אופציות – זה מאפשר מודולריות מלאה.
    - מחזיר AnalysisResult עם:
      - payoff_df (curve_df של FX)
      - pl_summary בסיסי
      - risk_profile פשוט לפי גודל הנומינלי
    """

    domain: Domain = Domain.FX

    def _parse_input(self, position: Any) -> FxDealInput | None:
        """
        ממפה את הקלט לעסקת FX אחת.
        בשלב זה:
        - FxDealInput (כבר מוכן)
        - dict עם אותם שדות
        בעתיד: אפשר להוסיף תמיכה ברשימות/פורטפוליו.
        """
        if isinstance(position, FxDealInput):
            return position
        if isinstance(position, dict):
            try:
                return FxDealInput(**position)
            except Exception:
                return None
        # אפשר להרחיב לתצורות נוספות בעתיד
        return None

    def _basic_risk_profile(
        self, deal: FxDealInput, summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        סיווג סיכון גס לפי notional_value_quote.
        זה שלד בלבד – לא רגולטורי / לא מוסדי.
        """
        notional_value = float(summary.get("notional_value_quote", 0.0))

        if notional_value <= 100_000:
            level = "low"
            comment = "חשיפה קטנה יחסית, מתאימה לרוב הלקוחות הקמעונאיים."
        elif notional_value <= 1_000_000:
            level = "medium"
            comment = "חשיפה בינונית, דורשת ניהול סיכונים בסיסי."
        else:
            level = "high"
            comment = "חשיפה גדולה, מתאימה ללקוחות מקצועיים / מוסדיים."

        return {
            "level": level,
            "comment": comment,
            "notional_value_quote": notional_value,
            "pair": deal.pair,
        }

    def analyze(self, position: Any, config: AnalysisConfig) -> AnalysisResult:
        result = AnalysisResult(domain=self.domain)

        deal = self._parse_input(position)
        if deal is None:
            result.meta["error"] = (
                "FxEngine expects FxDealInput or dict with keys: "
                "pair, notional, direction, forward_rate, spot_today, maturity_days"
            )
            return result

        # --------------------------------------------------------
        # PAYOFF (FX Forward – עקומת P/L)
        # --------------------------------------------------------
        if AnalysisLayer.PAYOFF in config.enabled_layers:
            curve_df = fx_forward_payoff_curve(deal)
            summary = summarize_fx_pl(deal, curve_df)

            result.payoff_df = curve_df
            # בשביל אחידות עם Options – נמפה גם ל-curve_df/break_even/scenarios
            result.curve_df = curve_df.rename(
                columns={"spot": "price", "pl_quote": "pl"}
            )
            result.break_even_points = []  # בהמשך אפשר לחשב BE מדויק אם נרצה
            result.scenarios_df = curve_df[["move_pct", "spot", "pl_quote"]].copy()
            result.pl_summary = summary

        # --------------------------------------------------------
        # RISK – סיווג בסיסי בלבד
        # --------------------------------------------------------
        if (
            AnalysisLayer.RISK in config.enabled_layers
            and result.pl_summary is not None
        ):
            risk_profile = self._basic_risk_profile(deal, result.pl_summary)
            result.risk_profile = risk_profile

        # שכבות נוספות (SCORING / WARNINGS / RECOMMENDATIONS) אפשר להוסיף בהמשך
        # כרגע נשאיר meta כדי שלא "נבטיח" משהו ללקוח.
        if AnalysisLayer.SCORING in config.enabled_layers:
            result.meta.setdefault("fx_scoring_note", "FX scoring not implemented yet")

        if AnalysisLayer.WARNINGS in config.enabled_layers:
            result.meta.setdefault(
                "fx_warnings_note", "FX warnings not implemented yet"
            )

        if AnalysisLayer.RECOMMENDATIONS in config.enabled_layers:
            result.meta.setdefault(
                "fx_reco_note", "FX recommendations not implemented yet"
            )

        return result


# ================================================================
# 6. StrategyBrain – המוח העליון שמנהל דומיינים ושכבות
# ================================================================


class StrategyBrain:
    """
    זהו 'המוח' של המערכת:
    - מנהל Engines לפי Domain (options / fx / mixed).
    - מאפשר ללקוח לבחור איזה דומיין ואילו שכבות חישוב להפעיל.
    - מחזיר תמיד AnalysisResult אחיד לשכבת ה-UI / API.
    """

    def __init__(
        self,
        options_engine: Optional[DomainEngine] = None,
        fx_engine: Optional[DomainEngine] = None,
    ) -> None:
        # מאפשר להזריק Engines מותאמים אישית, אבל גם נותן ברירת מחדל.
        self._engines: Dict[Domain, DomainEngine] = {}

        self._engines[Domain.OPTIONS] = options_engine or OptionsEngine()
        self._engines[Domain.FX] = fx_engine or FxEngine()
        # Domain.MIXED נטפל בו באופן מיוחד – שילוב של כמה Engines

    # ------------------------------------------------------------
    # API עיקרי לשימוש חיצוני
    # ------------------------------------------------------------
    def analyze_position(
        self,
        position: Position,
        config: Optional[AnalysisConfig] = None,
    ) -> AnalysisResult:
        """
        נקודת כניסה אחת 'חיצונית' – זאת הפונקציה שה-UI או ה-API יקראו לה.

        1. בוחר Engine לפי domain
        2. מריץ את הניתוח
        3. מחזיר AnalysisResult אחיד
        """
        if config is None:
            config = AnalysisConfig()

        if config.domain == Domain.MIXED:
            return self._analyze_mixed(position, config)

        engine = self._engines.get(config.domain)
        if engine is None:
            # fallback: נחזיר אובייקט ריק עם meta
            result = AnalysisResult(domain=config.domain)
            result.meta["error"] = f"No engine registered for domain={config.domain}"
            return result

        return engine.analyze(position, config)

    # ------------------------------------------------------------
    # תמיכה בדומיין MIXED – שילוב בין Engines שונים
    # ------------------------------------------------------------
    def _analyze_mixed(
        self, position: Position, config: AnalysisConfig
    ) -> AnalysisResult:
        """
        מצב שבו הלקוח רוצה לשלב FX + אופציות באותה תצוגה.
        כרגע: מריצים קודם OPTIONS, אחר כך FX, וממזגים meta.
        בעתיד אפשר לממש לוגיקה חכמה יותר (cross-risk וכו').
        """
        options_cfg = AnalysisConfig(
            domain=Domain.OPTIONS,
            enabled_layers=config.enabled_layers,
            goals=config.goals,
            backtest_config=config.backtest_config,
            flags=config.flags.copy(),
        )
        fx_cfg = AnalysisConfig(
            domain=Domain.FX,
            enabled_layers=config.enabled_layers,
            goals=config.goals,
            backtest_config=config.backtest_config,
            flags=config.flags.copy(),
        )

        opt_result = self._engines[Domain.OPTIONS].analyze(position, options_cfg)
        fx_result = self._engines[Domain.FX].analyze(position, fx_cfg)

        # כרגע – נחזיר את תוצאת האופציות ונצרף meta של FX
        mixed = opt_result
        mixed.domain = Domain.MIXED
        mixed.meta["fx_result"] = {
            "warnings": fx_result.warnings,
            "risk_profile": fx_result.risk_profile,
            "score": fx_result.score,
            "meta": fx_result.meta,
        }
        return mixed
