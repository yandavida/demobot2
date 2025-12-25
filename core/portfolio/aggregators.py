from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Tuple, Any, Dict, Hashable, TypeVar
K = TypeVar("K", bound=Hashable)

from core.portfolio.portfolio_models import PortfolioState
from core.portfolio.models import Currency


def _econ_mapping(econ: object, field: str) -> Mapping[Any, float]:
    # Accept mapping-like or object with attribute; missing -> empty
    if econ is None:
        return {}
    if isinstance(econ, Mapping):
        val = econ.get(field)
        if isinstance(val, Mapping):
            return {k: float(v) for k, v in val.items()}
        return {}
    # object-like
    val = getattr(econ, field, None)
    if isinstance(val, Mapping):
        return {k: float(v) for k, v in val.items()}
    return {}


def _econ_float(econ: object, field: str) -> float:
    if econ is None:
        return 0.0
    if isinstance(econ, Mapping):
        v = econ.get(field, 0.0)
        try:
            return float(v)
        except Exception:
            return 0.0
    v = getattr(econ, field, 0.0)
    try:
        return float(v)
    except Exception:
        return 0.0


def _merge_numeric_maps(maps: Sequence[Mapping[K, float]]) -> Dict[K, float]:
    result: Dict[K, float] = {}
    for m in maps:
        for k, v in m.items():
            result[k] = result.get(k, 0.0) + float(v)
    return result


def _sorted_pairs(mapping: Mapping[K, float]) -> Tuple[Tuple[K, float], ...]:
    # Deterministic ordering by string(key)
    items = list(mapping.items())
    items.sort(key=lambda kv: str(kv[0]))
    return tuple((k, float(v)) for k, v in items)


@dataclass(frozen=True)
class PortfolioAggregates:
    position_count: int
    gross_quantity: float
    total_fees: float
    total_slippage: float
    total_notional: float
    cash_usage_by_currency: Tuple[Tuple[Currency, float], ...]
    exposure_by_currency: Tuple[Tuple[Currency, float], ...]
    exposure_by_asset: Tuple[Tuple[str, float], ...]


def aggregate_portfolio(state: PortfolioState) -> PortfolioAggregates:
    position_count = len(state.positions)
    gross_quantity = sum(float(p.quantity) for p in state.positions)

    fees_acc: float = 0.0
    slip_acc: float = 0.0
    notional_acc: float = 0.0

    cash_maps: list[Mapping[Currency, float]] = []
    exposure_ccy_maps: list[Mapping[Currency, float]] = []
    exposure_asset_maps: list[Mapping[str, float]] = []

    for p in state.positions:
        try:
            econ = p.economics()
        except Exception:
            econ = None

        fees_acc += _econ_float(econ, "fees")
        slip_acc += _econ_float(econ, "slippage")
        notional_acc += _econ_float(econ, "notional")

        cash_maps.append(_econ_mapping(econ, "cash_usage") or {})
        exposure_ccy_maps.append(_econ_mapping(econ, "exposure_by_currency") or {})
        exposure_asset_maps.append(_econ_mapping(econ, "exposure_by_asset") or {})

    merged_cash = _merge_numeric_maps(cash_maps)
    merged_exposure_ccy = _merge_numeric_maps(exposure_ccy_maps)
    merged_exposure_asset = _merge_numeric_maps(exposure_asset_maps)

    return PortfolioAggregates(
        position_count=position_count,
        gross_quantity=gross_quantity,
        total_fees=float(fees_acc),
        total_slippage=float(slip_acc),
        total_notional=float(notional_acc),
        cash_usage_by_currency=_sorted_pairs(merged_cash),
        exposure_by_currency=_sorted_pairs(merged_exposure_ccy),
        exposure_by_asset=_sorted_pairs(merged_exposure_asset),
    )


def validate_portfolio_economics_present(state: PortfolioState) -> tuple[bool, int]:
    missing = 0
    for p in state.positions:
        try:
            _ = p.economics()
        except Exception:
            missing += 1
    return (missing == 0, missing)


__all__ = ["PortfolioAggregates", "aggregate_portfolio", "validate_portfolio_economics_present"]
