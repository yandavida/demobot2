from __future__ import annotations


class MarketDataError(Exception):
    """Base class for market data related errors."""


class MissingQuoteError(MarketDataError):
    pass


class MissingFxRateError(MarketDataError):
    pass


__all__ = ["MarketDataError", "MissingQuoteError", "MissingFxRateError"]
