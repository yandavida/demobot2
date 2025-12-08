"""UI-only helpers for strategy visualizations."""

from __future__ import annotations

from typing import Any, Iterable, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def make_builder_figures(
    *,
    curve_df: pd.DataFrame,
    be_points: Iterable[float] | None,
    spot: float,
    max_profit: float | None = None,
) -> Tuple[go.Figure | None, go.Figure | None]:
    """Create builder P/L figures for the overview tab.

    Returns a tuple of (full_range, zoomed) figures. The zoomed figure is
    currently not used, so we return None for it to keep the call signature
    forward-compatible.
    """

    if curve_df is None or curve_df.empty:
        return None, None

    if "spot" in curve_df.columns:
        x_col = "spot"
    else:
        # fallback to first numeric column
        x_col = curve_df.select_dtypes(include=["number"]).columns[0]

    y_col = "pl" if "pl" in curve_df.columns else curve_df.columns[-1]

    fig = px.line(curve_df, x=x_col, y=y_col, markers=False)
    fig.update_layout(
        title="P/L across underlying prices",
        xaxis_title="Underlying price",
        yaxis_title="P/L",
    )

    # Mark the current spot and BE points for quick orientation
    fig.add_vline(x=spot, line_dash="dot", line_color="orange", annotation_text="Spot")

    if be_points:
        for be in be_points:
            fig.add_vline(x=be, line_dash="dash", line_color="gray")

    if max_profit is not None:
        fig.add_hline(y=max_profit, line_dash="dash", line_color="green")

    return fig, None
