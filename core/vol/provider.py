from __future__ import annotations

from typing import Protocol


class VolProvider(Protocol):
    def get_vol(
        self,
        *,
        underlying: str,
        expiry_t: float,
        strike: float,
        option_type: str,
        strict: bool = True,
    ) -> float:
        ...


__all__ = ["VolProvider"]
