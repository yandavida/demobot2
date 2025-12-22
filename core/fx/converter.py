from __future__ import annotations

from typing import Mapping, Sequence, Dict, Any, cast

from core.market_data.types import FxRateQuote
from core.portfolio.models import Currency
from core.fx.errors import MissingFxRateError, InvalidFxRateError


class FxConverter:
    def __init__(
        self,
        fx_rates: Sequence[FxRateQuote] | Mapping[str, Any] | None = None,
        *,
        provider: object | None = None,
        base_ccy: Currency | None = None,
    ) -> None:
        """Compatibility constructor supporting new and legacy call-sites.

        Args:
            fx_rates: sequence of `FxRateQuote` or mapping pair->FxRateQuote or pair->float
            provider: legacy provider object exposing `.rates` mapping or `.to_mapping()` method
            base_ccy: legacy convenience base currency
        """
        rates: Dict[str, float] = {}

        # 1) If explicit fx_rates mapping/sequence provided, prefer it
        if fx_rates is not None:
            if isinstance(fx_rates, Mapping):
                for k, v in fx_rates.items():
                    # v may be FxRateQuote or float
                    if isinstance(v, FxRateQuote):
                        rate = float(v.rate)
                    else:
                        rate = float(v)
                    if not (rate > 0):
                        raise InvalidFxRateError(f"fx rate for {k} must be > 0")
                    rates[str(k)] = rate
            else:
                for v in fx_rates:
                    if not (v.rate > 0):
                        raise InvalidFxRateError(f"fx rate for {v.pair} must be > 0")
                    rates[str(v.pair)] = float(v.rate)

        # 2) Else try legacy provider if given
        elif provider is not None:
            prov_rates = None
            # prefer attribute `.rates`
            if hasattr(provider, "rates"):
                prov_rates = getattr(provider, "rates")
            # else try to call a to_mapping() helper
            elif hasattr(provider, "to_mapping"):
                try:
                    prov_rates = provider.to_mapping()
                except Exception:
                    prov_rates = None

            if not isinstance(prov_rates, Mapping):
                raise TypeError("legacy provider must expose a mapping of pair->rate via `.rates` or `.to_mapping()`")

            prov_rates_map = cast(Mapping[str, float], prov_rates)
            for k, v in prov_rates_map.items():
                rate = float(v)
                if not (rate > 0):
                    raise InvalidFxRateError(f"fx rate for {k} must be > 0")
                rates[str(k)] = rate

        # store simple mapping pair->float
        self._rates: Dict[str, float] = dict(rates)
        self._base_ccy = base_ccy

    def convert(self, amount: float, from_ccy: Currency, to_ccy: Currency, *, strict: bool = True) -> float:
        if from_ccy == to_ccy:
            return float(amount)

        pair = f"{from_ccy}/{to_ccy}"
        inv = f"{to_ccy}/{from_ccy}"

        if pair in self._rates:
            rate = float(self._rates[pair])
            return float(amount) * rate

        if inv in self._rates:
            rate = float(self._rates[inv])
            if rate == 0:
                raise InvalidFxRateError(f"inverse rate for {inv} is zero")
            return float(amount) / rate

        if strict:
            raise MissingFxRateError(f"missing fx rate for {from_ccy}->{to_ccy}")

        # non-strict: return unconverted amount
        return float(amount)

    @property
    def base_ccy(self) -> Currency:
        if self._base_ccy is None:
            raise ValueError("FxConverter.base_ccy is not set")
        return self._base_ccy

    def to_base(self, amount: float | object, from_ccy: Currency | None = None, *, strict: bool = True):
        # Support legacy call-sites which pass a Money object or (amount, from_ccy).
        from core.portfolio.models import Money

        # If caller passed a Money-like object as first positional arg
        if isinstance(amount, Money):
            money = amount
            amt = money.amount
            frm = money.ccy
        else:
            if from_ccy is None:
                raise TypeError("from_ccy must be provided when passing numeric amount to to_base()")
            from typing import cast

            amt = float(cast(float, amount))
            frm = cast(Currency, from_ccy)

        converted = self.convert(amt, frm, self.base_ccy, strict=strict)
        return Money(amount=converted, ccy=self.base_ccy)


__all__ = ["FxConverter"]
