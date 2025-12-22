from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Sequence

from core.portfolio.portfolio_models import CanonicalKey, PortfolioState
from core.pricing.types import PriceResult, PricingError
from core.pricing.engine import PricingEngine
from core.market_data.types import MarketSnapshot
from core.fx.converter import FxConverter
from core.pricing.context import PricingContext


@dataclass(frozen=True)
class Greeks:
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


@dataclass(frozen=True)
class PositionRisk:
    key: CanonicalKey
    pv: float
    currency: str
    greeks: Greeks
    breakdown: Tuple[Tuple[str, float], ...] = tuple()


@dataclass(frozen=True)
class PortfolioRiskSnapshot:
    total_pv: float
    currency: str
    greeks: Greeks
    positions: Tuple[PositionRisk, ...]


def extract_greeks(price_result: PriceResult) -> Greeks:
    b = price_result.breakdown or {}
    def get(k: str) -> float:
        return float(b.get(k, 0.0))

    return Greeks(delta=get("delta"), gamma=get("gamma"), vega=get("vega"), theta=get("theta"), rho=get("rho"))


def scale_greeks(g: Greeks, factor: float) -> Greeks:
    return Greeks(delta=g.delta * factor, gamma=g.gamma * factor, vega=g.vega * factor, theta=g.theta * factor, rho=g.rho * factor)


def add_greeks(a: Greeks, b: Greeks) -> Greeks:
    return Greeks(delta=a.delta + b.delta, gamma=a.gamma + b.gamma, vega=a.vega + b.vega, theta=a.theta + b.theta, rho=a.rho + b.rho)


def _build_fx_conv(snapshot: MarketSnapshot) -> FxConverter | None:
    try:
        fx_rates = tuple(snapshot.fx_rates) if snapshot.fx_rates else tuple()
    except Exception:
        fx_rates = tuple()
    if fx_rates:
        return FxConverter(fx_rates=fx_rates)
    return None


def normalize_money(amount: float, from_ccy: str, to_ccy: str, snapshot: MarketSnapshot, *, strict: bool = True) -> float:
    if from_ccy == to_ccy:
        return float(amount)
    conv = _build_fx_conv(snapshot)
    if conv is None:
        if strict:
            raise PricingError(f"missing fx rates for conversion {from_ccy}->{to_ccy}")
        return float(amount)
    return float(conv.convert(amount, from_ccy, to_ccy, strict=strict))


def valuate_and_risk_positions(
    state: PortfolioState,
    pricing_engine: PricingEngine,
    snapshot: MarketSnapshot,
    *,
    base_currency: str = "USD",
    context: "PricingContext" | None = None,
) -> Tuple[PositionRisk, ...]:
    """Valuate positions and compute Greeks for a given market snapshot.

    If `context` is provided it will be used for pricing (this allows callers
    to pass a pre-built `PricingContext` containing e.g. a shocked market and
    a shocked `vol_provider`). Otherwise a context will be constructed from
    the supplied snapshot.
    """
    conv = _build_fx_conv(snapshot)
    positions: list[PositionRisk] = []

    for p in state.positions:
        # build context with converter if available unless caller supplied one
        from core.pricing.context import PricingContext

        ctx = context
        if ctx is None:
            ctx = PricingContext(market=snapshot, base_currency=base_currency, fx_converter=conv)

        pr: PriceResult
        try:
            pr = pricing_engine.price_execution(p.execution, ctx)
        except Exception:
            raise

        pv_unit = float(pr.pv)
        pv_pos = pv_unit * float(p.quantity)

        # normalize PV to base currency if needed
        if pr.currency != base_currency:
            if conv is None:
                raise PricingError(f"missing FxConverter for {pr.currency}->{base_currency}")
            fx_factor = float(conv.convert(1.0, pr.currency, base_currency, strict=True))
            pv_pos = pv_pos * fx_factor
        else:
            fx_factor = 1.0

        greeks_unit = extract_greeks(pr)
        greeks_pos = scale_greeks(greeks_unit, float(p.quantity) * fx_factor)

        # deterministic breakdown: sorted pairs from breakdown
        bd = tuple(sorted(((k, float(v)) for k, v in (pr.breakdown or {}).items()), key=lambda kv: kv[0]))

        positions.append(PositionRisk(key=p.key, pv=float(pv_pos), currency=base_currency, greeks=greeks_pos, breakdown=bd))

    # sort positions deterministically by key
    positions.sort(key=lambda r: str(r.key))
    return tuple(positions)


def aggregate_portfolio_risk(positions: Sequence[PositionRisk], *, base_currency: str = "USD") -> PortfolioRiskSnapshot:
    total_pv = sum(float(p.pv) for p in positions)
    total_greeks = Greeks(0.0, 0.0, 0.0, 0.0, 0.0)
    for p in positions:
        total_greeks = add_greeks(total_greeks, p.greeks)

    return PortfolioRiskSnapshot(total_pv=float(total_pv), currency=base_currency, greeks=total_greeks, positions=tuple(positions))


__all__ = [
    "Greeks",
    "PositionRisk",
    "PortfolioRiskSnapshot",
    "extract_greeks",
    "scale_greeks",
    "add_greeks",
    "normalize_money",
    "valuate_and_risk_positions",
    "aggregate_portfolio_risk",
]
