from __future__ import annotations

from typing import Mapping, Sequence, Tuple

from .types import VolKey, VolQuote
from .errors import MissingVolError
from .provider import VolProvider


class InMemoryVolProvider(VolProvider):
    """Deterministic in-memory vol provider.

    Supports exact-key quotes (VolQuote entries) and a simple per-underlying
    default mapping {underlying: vol}.
    """

    def __init__(self, quotes: Sequence[VolQuote] | Mapping[str, float] = ()):  # type: ignore[override]
        # Normalize into a tuple of VolQuote for exact matches and a dict for defaults
        self._exact: dict[VolKey, VolQuote] = {}
        self._defaults: dict[str, float] = {}

        if isinstance(quotes, Mapping):
            for k, v in quotes.items():
                if v < 0.0:
                    raise ValueError("vol must be >= 0")
                self._defaults[str(k)] = float(v)
        else:
            for q in quotes:
                if not isinstance(q, VolQuote):
                    raise TypeError("quotes sequence must contain VolQuote")
                self._exact[q.key] = q

    def get_vol(
        self,
        *,
        underlying: str,
        expiry_t: float,
        strike: float,
        option_type: str,
        strict: bool = True,
    ) -> float:
        key = VolKey(underlying=underlying, expiry_t=float(expiry_t), strike=None if strike is None else float(strike), option_type=option_type)

        # exact match
        if key in self._exact:
            return float(self._exact[key].vol)

        # fallback: underlying default
        if underlying in self._defaults:
            return float(self._defaults[underlying])

        if strict:
            raise MissingVolError(f"missing vol for {underlying} {expiry_t} strike={strike} type={option_type}")
        # non-strict deterministic fallback
        return 0.0

    def snapshot(self) -> Tuple[VolQuote, ...]:
        # deterministic ordering: sort by underlying, expiry_t, strike (None last), option_type
        def keyfn(vq: VolQuote):
            s = vq.key.strike if vq.key.strike is not None else float("inf")
            ot = vq.key.option_type or ""
            return (vq.key.underlying, float(vq.key.expiry_t), s, ot)

        return tuple(sorted(self._exact.values(), key=keyfn))


__all__ = ["InMemoryVolProvider"]
