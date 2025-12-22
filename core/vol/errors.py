from __future__ import annotations


class VolError(Exception):
    pass


class MissingVolError(VolError):
    pass


class InvalidVolError(VolError):
    pass


__all__ = ["VolError", "MissingVolError", "InvalidVolError"]
