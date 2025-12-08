# Layer: services
# services/chain_service.py
from __future__ import annotations

from datetime import date

import pandas as pd

from brokers import get_broker


def generate_chain(
    symbol: str,
    expiry: date,
    spot: float,
    r: float,
    q: float,
    iv: float,
    strikes_count: int,
    step_pct: float,
    broker_name: str = "sim",
) -> pd.DataFrame:
    """
    מייצר שרשרת אופציות דרך הברוקר שנבחר ומחזיר DataFrame.
    """

    broker = get_broker(broker_name)

    if not broker.is_connected():
        broker.connect()

    chain = broker.get_option_chain(
        symbol=symbol,
        expiry=expiry,
        spot=spot,
        r=r,
        q=q,
        iv=iv,
        strikes_count=strikes_count,
        step_pct=step_pct,
    )

    if not isinstance(chain, pd.DataFrame) or chain.empty:
        raise ValueError("השרשרת ריקה או בפורמט לא צפוי.")

    return chain
