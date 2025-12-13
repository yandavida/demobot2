from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from core.arbitrage.execution.models import ExecutionConstraints, ExecutionDecision
from core.arbitrage.execution import reasons


def _normalize_now(now: datetime) -> datetime:
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now


def _get_quote_ts(q: Mapping[str, Any]) -> datetime | None:
    ts = q.get("ts")
    return ts if isinstance(ts, datetime) else None


def _get_bid_ask(q: Mapping[str, Any]) -> tuple[float | None, float | None]:
    bid = q.get("bid")
    ask = q.get("ask")
    bid_f = float(bid) if isinstance(bid, (int, float)) else None
    ask_f = float(ask) if isinstance(ask, (int, float)) else None
    return bid_f, ask_f


def _spread_bps(bid: float, ask: float) -> float:
    mid = (bid + ask) / 2.0
    if mid <= 0:
        return float("inf")
    return ((ask - bid) / mid) * 10_000.0


def evaluate_execution_readiness(
    opportunity: Mapping[str, Any],
    quotes: Mapping[str, Any],
    constraints: ExecutionConstraints,
    now: datetime,
) -> ExecutionDecision:
    """
    Deterministic, fail-fast, conservative-by-default execution gate.

    Minimal expected inputs:
      - opportunity: {"edge_bps": float, "quantity": float, "venue": str?, "latency_ms": float?}
      - quotes: {<key>: {"bid": float, "ask": float, "ts": datetime}, ...}

    Returns ExecutionDecision with:
      - can_execute
      - reason_codes (string constants)
      - metrics (edge_bps, worst_spread_bps, age_ms, notional, recommended_qty)
      - recommended_qty
      - ts
    """
    now_n = _normalize_now(now)

    # --- Fail-fast: missing quotes
    if not quotes:
        return ExecutionDecision(
            can_execute=False,
            reason_codes=[reasons.MISSING_QUOTES],
            metrics={},
            recommended_qty=0.0,
            ts=now_n,
        )

    # --- Fail-fast: edge required
    edge_raw = opportunity.get("edge_bps")
    if not isinstance(edge_raw, (int, float)):
        return ExecutionDecision(
            can_execute=False,
            reason_codes=[reasons.INTERNAL_ERROR],
            metrics={},
            recommended_qty=0.0,
            ts=now_n,
        )

    edge_bps = float(edge_raw)
    metrics: dict[str, float] = {"edge_bps": edge_bps}

    if edge_bps < constraints.min_edge_bps:
        return ExecutionDecision(
            can_execute=False,
            reason_codes=[reasons.EDGE_TOO_SMALL],
            metrics=metrics,
            recommended_qty=0.0,
            ts=now_n,
        )

    # --- Worst-case spread + age across all valid quotes (conservative)
    worst_spread = 0.0
    worst_age_ms = 0.0
    any_valid = False
    anchor_mid: float | None = None

    for q_any in quotes.values():
        if not isinstance(q_any, Mapping):
            continue
        bid, ask = _get_bid_ask(q_any)
        ts = _get_quote_ts(q_any)
        if bid is None or ask is None or ts is None:
            continue

        any_valid = True
        worst_spread = max(worst_spread, _spread_bps(bid, ask))

        ts_n = ts if ts.tzinfo is not None else ts.replace(tzinfo=timezone.utc)
        age_ms = (now_n - ts_n).total_seconds() * 1000.0
        worst_age_ms = max(worst_age_ms, age_ms)

        if anchor_mid is None:
            anchor_mid = (bid + ask) / 2.0

    if not any_valid:
        return ExecutionDecision(
            can_execute=False,
            reason_codes=[reasons.MISSING_QUOTES],
            metrics=metrics,
            recommended_qty=0.0,
            ts=now_n,
        )

    metrics["worst_spread_bps"] = worst_spread
    metrics["age_ms"] = worst_age_ms

    if worst_age_ms > constraints.max_age_ms:
        return ExecutionDecision(
            can_execute=False,
            reason_codes=[reasons.QUOTE_TOO_OLD],
            metrics=metrics,
            recommended_qty=0.0,
            ts=now_n,
        )

    if worst_spread > constraints.max_spread_bps:
        return ExecutionDecision(
            can_execute=False,
            reason_codes=[reasons.SPREAD_TOO_WIDE],
            metrics=metrics,
            recommended_qty=0.0,
            ts=now_n,
        )

    # --- Venue allowlist (optional)
    venue = opportunity.get("venue")
    if constraints.allowed_venues is not None and isinstance(venue, str):
        if venue not in constraints.allowed_venues:
            return ExecutionDecision(
                can_execute=False,
                reason_codes=[reasons.VENUE_NOT_ALLOWED],
                metrics=metrics,
                recommended_qty=0.0,
                ts=now_n,
            )

    # --- Latency budget (optional)
    lat_raw = opportunity.get("latency_ms")
    if isinstance(lat_raw, (int, float)):
        latency_ms = float(lat_raw)
        metrics["latency_ms"] = latency_ms
        if latency_ms > constraints.max_latency_ms:
            return ExecutionDecision(
                can_execute=False,
                reason_codes=[reasons.LATENCY_TOO_HIGH],
                metrics=metrics,
                recommended_qty=0.0,
                ts=now_n,
            )

    # --- Quantity / Notional checks
    qty_raw = opportunity.get("quantity", 0.0)
    if not isinstance(qty_raw, (int, float)):
        return ExecutionDecision(
            can_execute=False,
            reason_codes=[reasons.INTERNAL_ERROR],
            metrics=metrics,
            recommended_qty=0.0,
            ts=now_n,
        )

    qty_abs = abs(float(qty_raw))

    if anchor_mid is None or anchor_mid <= 0.0:
        return ExecutionDecision(
            can_execute=False,
            reason_codes=[reasons.INTERNAL_ERROR],
            metrics=metrics,
            recommended_qty=0.0,
            ts=now_n,
        )

    notional = qty_abs * anchor_mid
    metrics["notional"] = notional

    if qty_abs > constraints.max_quantity:
        return ExecutionDecision(
            can_execute=False,
            reason_codes=[reasons.QTY_TOO_LARGE],
            metrics=metrics,
            recommended_qty=0.0,
            ts=now_n,
        )

    if notional > constraints.max_notional:
        return ExecutionDecision(
            can_execute=False,
            reason_codes=[reasons.NOTIONAL_TOO_LARGE],
            metrics=metrics,
            recommended_qty=0.0,
            ts=now_n,
        )

    # Recommended qty: clipped by max_quantity and max_notional
    qty_by_notional = constraints.max_notional / anchor_mid
    recommended_qty = min(qty_abs, constraints.max_quantity, qty_by_notional)
    metrics["recommended_qty"] = recommended_qty

    return ExecutionDecision(
        can_execute=True,
        reason_codes=[],
        metrics=metrics,
        recommended_qty=recommended_qty,
        ts=now_n,
    )
