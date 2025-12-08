# Layer: strategies
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
    - label : טקסט שמופיע ב־selectbox
    - render: פונקציה שמקבלת df_view ומציירת את כל ה־UI של האסטרטגיה
    """

    name: str
    label: str
    render: Callable[[pd.DataFrame], None]


def get_strategies() -> Sequence[StrategyDefinition]:
    """
    מחזיר רשימת אסטרטגיות זמינות.
    עושים import *פנימי* כדי לא ליצור import מעגלי.
    """
    from sandbox.ic_sandbox import render_ic_sandbox
    from core.vertical_spread import render_vertical_spread
    from core.straddle import render_straddle
    from core.butterfly import render_butterfly
    from core.short_straddle import render_short_straddle
    from core.short_butterfly import render_short_butterfly

    strategies: list[StrategyDefinition] = [
        StrategyDefinition(
            name="iron_condor_quick",
            label="Iron Condor (quick sandbox)",
            render=render_ic_sandbox,
        ),
        StrategyDefinition(
            name="vertical_spread_basic",
            label="Vertical Spread (basic)",
            render=render_vertical_spread,
        ),
        StrategyDefinition(
            name="straddle_long",
            label="Long Straddle",
            render=render_straddle,
        ),
        StrategyDefinition(
            name="butterfly_long",
            label="Long Butterfly (1:-2:1)",
            render=render_butterfly,
        ),
        StrategyDefinition(
            name="straddle_short",
            label="Short Straddle",
            render=render_short_straddle,
        ),
        StrategyDefinition(
            name="butterfly_short",
            label="Short Butterfly (short 1:2:1)",
            render=render_short_butterfly,
        ),
    ]

    return strategies
