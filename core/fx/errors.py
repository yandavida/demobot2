from __future__ import annotations


class FxError(Exception):
    """Base FX error."""


class MissingFxRateError(FxError):
    pass


class InvalidFxRateError(FxError):
    pass


__all__ = ["FxError", "MissingFxRateError", "InvalidFxRateError"]
