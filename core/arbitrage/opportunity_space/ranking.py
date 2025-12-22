from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from core.arbitrage.models import ArbitrageOpportunity

Direction = Literal = ""  # type: ignore
try:
    from typing import Literal as _Literal
    Direction = _Literal["max", "min"]  # type: ignore
except Exception:  # pragma: no cover
    Direction = str  # fallback


@dataclass(frozen=True)
class ParetoDim:
    name: str
    direction: "Direction"
    weight: float = 1.0


@dataclass(frozen=True)
class RankingConfig:
    max_results: int = 20
    pareto_dimensions: Tuple[ParetoDim, ...] = (
        ParetoDim("edge_bps", "max", 1.0),
        ParetoDim("latency_ms", "min", 1.0),
        ParetoDim("edge_bps", "min", 1.0),
    )
    tie_break: Tuple[str, ...] = ("edge_bps", "latency_ms", "notional")
    epsilon: Mapping[str, float] = None


def _get_dim_value(opt: ArbitrageOpportunity, name: str) -> Optional[float]:
    # Supported names
    if name == "edge_bps":
        return float(getattr(opt, "edge_bps", None) or 0.0)
    if name == "latency_ms":
        # no latency on opportunity; derive from legs if present
        return None
    if name == "spread_bps":
        return float(getattr(opt, "edge_bps", None) or 0.0)
    if name in ("notional", "max_fill_notional"):
        try:
            return float(opt.buy.price * opt.size)
        except Exception:
            return None
    if name == "fees_bps":
        return float(getattr(opt.buy, "fees_bps", 0.0) + getattr(opt.sell, "fees_bps", 0.0))
    if name == "slippage_bps":
        return None
    # fallback: try attribute
    val = getattr(opt, name, None)
    return float(val) if isinstance(val, (int, float)) else None


def _compare_vals(a: Optional[float], b: Optional[float], direction: str, eps: float) -> int:
    """Compare a and b for direction.

    Returns: 1 if a better than b, 0 if equal within eps, -1 if worse.
    """
    # treat None as worst
    if a is None and b is None:
        return 0
    if a is None:
        return -1
    if b is None:
        return 1

    diff = a - b
    if abs(diff) <= eps:
        return 0
    if direction == "max":
        return 1 if diff > 0 else -1
    return 1 if diff < 0 else -1


def dominates(a: ArbitrageOpportunity, b: ArbitrageOpportunity, cfg: RankingConfig) -> bool:
    eps_map = cfg.epsilon or {}
    strictly_better = False
    for dim in cfg.pareto_dimensions:
        eps = float(eps_map.get(dim.name, 0.0)) if eps_map else 0.0
        av = _get_dim_value(a, dim.name)
        bv = _get_dim_value(b, dim.name)
        cmp = _compare_vals(av, bv, dim.direction, eps)
        if cmp == -1:
            return False
        if cmp == 1:
            strictly_better = True

    return strictly_better


def pareto_frontier(options: Sequence[ArbitrageOpportunity], cfg: RankingConfig) -> List[ArbitrageOpportunity]:
    frontier: List[ArbitrageOpportunity] = []
    for opt in options:
        dominated = False
        to_remove: List[ArbitrageOpportunity] = []
        for f in frontier:
            if dominates(f, opt, cfg):
                dominated = True
                break
            if dominates(opt, f, cfg):
                to_remove.append(f)
        if dominated:
            continue
        for r in to_remove:
            frontier.remove(r)
        frontier.append(opt)
    return frontier


def _tie_break_score(opt: ArbitrageOpportunity, cfg: RankingConfig) -> Tuple:
    vals = []
    eps_map = cfg.epsilon or {}
    for key in cfg.tie_break:
        v = _get_dim_value(opt, key)
        if v is None:
            # worst value placeholder
            vals.append(float("-inf") if key in ("edge_bps", "notional") else float("inf"))
        else:
            vals.append(v)
    return tuple(vals)


def rank_execution_options(options: Sequence[ArbitrageOpportunity], cfg: RankingConfig) -> List[ArbitrageOpportunity]:
    # Compute frontier
    frontier = pareto_frontier(options, cfg)

    # sort frontier by tie-break descending for max dims and ascending for min dims
    # we'll use _tie_break_score and stable sort with original index
    indexed = list(enumerate(frontier))
    def key_fn(item):
        idx, opt = item
        score = _tie_break_score(opt, cfg)
        # include original index to ensure stability
        return (*score, idx)

    sorted_frontier = [opt for _, opt in sorted(indexed, key=key_fn, reverse=True)]

    # Rank remaining options similarly
    remaining = [o for o in options if o not in frontier]
    indexed_rem = list(enumerate(remaining))
    sorted_remaining = [opt for _, opt in sorted(indexed_rem, key=lambda it: (*_tie_break_score(it[1], cfg), it[0]), reverse=True)]

    ordered = sorted_frontier + sorted_remaining
    # truncate to max_results
    return ordered[: cfg.max_results]


def explain_ranking(options: Sequence[ArbitrageOpportunity], cfg: RankingConfig) -> Dict[str, Any]:
    frontier = pareto_frontier(options, cfg)
    ranked = rank_execution_options(options, cfg)

    frontier_ids = [o.opportunity_id or f"{o.symbol}:{o.buy.venue}->{o.sell.venue}" for o in frontier]
    ranked_ids = [o.opportunity_id or f"{o.symbol}:{o.buy.venue}->{o.sell.venue}" for o in ranked]

    dominance_reasons: Dict[str, Dict[str, Any]] = {}
    for opt in options:
        if opt in frontier:
            continue
        # find a frontier item that dominates it
        dom_found = None
        dom_dims: List[str] = []
        for f in frontier:
            if dominates(f, opt, cfg):
                dom_found = f
                # which dims f is strictly better on?
                for dim in cfg.pareto_dimensions:
                    eps = float((cfg.epsilon or {}).get(dim.name, 0.0))
                    av = _get_dim_value(f, dim.name)
                    bv = _get_dim_value(opt, dim.name)
                    cmp = _compare_vals(av, bv, dim.direction, eps)
                    if cmp == 1:
                        dom_dims.append(dim.name)
                break
        key = opt.opportunity_id or f"{opt.symbol}:{opt.buy.venue}->{opt.sell.venue}"
        if dom_found is not None:
            dominance_reasons[key] = {
                "dominated_by": dom_found.opportunity_id or f"{dom_found.symbol}:{dom_found.buy.venue}->{dom_found.sell.venue}",
                "dimensions": dom_dims,
            }

    return {
        "frontier_ids": frontier_ids,
        "ranked_ids": ranked_ids,
        "dominance_reasons": dominance_reasons,
    }


__all__ = ["RankingConfig", "ParetoDim", "pareto_frontier", "dominates", "rank_execution_options", "explain_ranking"]
