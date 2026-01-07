from __future__ import annotations

class MarketSnapshotNotFoundError(Exception):
    def __init__(self, snapshot_id: str) -> None:
        super().__init__(f"market snapshot {snapshot_id} not found")
        self.snapshot_id = snapshot_id



class MissingQuoteError(Exception):
    pass


class MissingFxRateError(Exception):
    pass


__all__ = [
    "MarketSnapshotNotFoundError",
    "MissingQuoteError",
    "MissingFxRateError",
]
