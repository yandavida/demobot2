from __future__ import annotations

class MarketSnapshotNotFoundError(Exception):
    def __init__(self, snapshot_id: str):
        super().__init__(f"market snapshot {snapshot_id} not found")
        self.snapshot_id = snapshot_id
from __future__ import annotations


class MarketDataError(Exception):
    """Base class for market data related errors."""


class MissingQuoteError(MarketDataError):
    pass


class MissingFxRateError(MarketDataError):
    pass


__all__ = ["MarketDataError", "MissingQuoteError", "MissingFxRateError"]
