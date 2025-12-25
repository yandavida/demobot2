from __future__ import annotations

from typing import cast, Iterable, Mapping

from core.adapters.market_data import InMemoryMarketDataAdapter
from core.contracts.risk_types import Greeks
from core.fx.converter import FxConverter
from core.portfolio.models import Money, Position
from core.portfolio.risk_models import PositionGreeks
from core.risk.portfolio import PortfolioRiskSnapshot
from core.services.portfolio_valuation import _StaticPricingAdapter


def _value_position(position: Position, fx: FxConverter) -> Money:
    price = position.metadata.get("price")
    if price is None:
        raise ValueError(f"Missing market price for {position.symbol}")

    market = InMemoryMarketDataAdapter(prices={position.symbol: float(cast(float, price))}).get_snapshot()
    adapter = _StaticPricingAdapter()
    return adapter.price(position, market, fx_converter=fx)


def _extract_greeks(metadata: Mapping[str, object]) -> PositionGreeks:
    greeks = metadata.get("greeks")
    if isinstance(greeks, Mapping):
        return PositionGreeks.from_mapping(greeks)
    return PositionGreeks()


def aggregate_portfolio_risk(
    positions: Iterable[Position],
    fx: FxConverter,
) -> PortfolioRiskSnapshot:
    """
    Aggregate PV and Greeks for a collection of positions.

    Each position is priced using the existing pricing adapter flow, the PV is
    converted to the FX converter's base currency, and Greeks are coerced into
    ``PositionGreeks`` before being summed into a portfolio snapshot.
    """

    total_value = Money.zero(fx.base_ccy)
    total_greeks = PositionGreeks()

    for position in positions:
        pv_base = fx.to_base(_value_position(position, fx))
        total_value = Money(amount=total_value.amount + pv_base.amount, ccy=fx.base_ccy)
        total_greeks = total_greeks + _extract_greeks(position.metadata)

    total_value_amount: float = float(total_value.amount)

    greeks = Greeks(
        delta=float(total_greeks.delta),
        gamma=float(total_greeks.gamma),
        vega=float(total_greeks.vega),
        theta=float(total_greeks.theta),
        rho=float(total_greeks.rho),
    )
    return PortfolioRiskSnapshot(total_pv=total_value_amount, currency=fx.base_ccy, greeks=greeks, positions=tuple())
