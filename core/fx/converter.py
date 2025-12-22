from __future__ import annotations

from typing import Mapping, Sequence, Dict

from core.market_data.types import FxRateQuote
from core.portfolio.models import Currency
from core.fx.errors import MissingFxRateError, InvalidFxRateError


class FxConverter:
    def __init__(self, fx_rates: Mapping[str, FxRateQuote] | Sequence[FxRateQuote] = ()):  # type: ignore[override]
        rates: Dict[str, FxRateQuote] = {}
        if isinstance(fx_rates, Mapping):
            for k, v in fx_rates.items():
                if not (v.rate > 0):
                    raise InvalidFxRateError(f"fx rate for {k} must be > 0")
                rates[str(k)] = v
        else:
            for v in fx_rates:
                if not (v.rate > 0):
                    raise InvalidFxRateError(f"fx rate for {v.pair} must be > 0")
                rates[str(v.pair)] = v

        # internal dict keyed by pair string
        self._rates: Dict[str, FxRateQuote] = dict(rates)

    def convert(self, amount: float, from_ccy: Currency, to_ccy: Currency, *, strict: bool = True) -> float:
        if from_ccy == to_ccy:
            return float(amount)

        pair = f"{from_ccy}/{to_ccy}"
        inv = f"{to_ccy}/{from_ccy}"

        if pair in self._rates:
            rate = float(self._rates[pair].rate)
            return float(amount) * rate

        if inv in self._rates:
            rate = float(self._rates[inv].rate)
            if rate == 0:
                raise InvalidFxRateError(f"inverse rate for {inv} is zero")
            return float(amount) / rate

        if strict:
            raise MissingFxRateError(f"missing fx rate for {from_ccy}->{to_ccy}")

        # non-strict: return unconverted amount
        return float(amount)


__all__ = ["FxConverter"]
