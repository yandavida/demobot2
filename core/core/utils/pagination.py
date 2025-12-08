# Layer: utils
from __future__ import annotations
import numpy as np
import pandas as pd


def paginate_df(
    df: pd.DataFrame, page_size: int, page_index: int
) -> tuple[pd.DataFrame, int]:
    total = len(df)
    if total == 0:
        return df, 0
    total_pages = int(np.ceil(total / page_size))
    page_index = max(0, min(page_index, total_pages - 1))
    start = page_index * page_size
    end = start + page_size
    return df.iloc[start:end].reset_index(drop=True), total_pages
