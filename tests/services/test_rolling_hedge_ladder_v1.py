from __future__ import annotations

import datetime
import math
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any

from core.numeric_policy import DEFAULT_TOLERANCES
from core.numeric_policy import MetricClass
from core.pricing.fx.types import FxMarketSnapshot
from core.risk.scenario_spec import ScenarioSpec
from core.services.advisory_read_model_v1 import run_treasury_advisory_v1
from core.services.hedge_policy_constraints_v1 import apply_hedge_policy_v1
from core.services.hedge_policy_constraints_v1 import HedgePolicyV1
from core.services.rolling_hedge_ladder_v1 import RollingHedgeLadderConfigV1
from core.services.rolling_hedge_ladder_v1 import compute_rolling_hedge_ladder_v1


def _close(a: float, b: float) -> bool:
    tol = DEFAULT_TOLERANCES[MetricClass.PNL]
    return math.isclose(a, b, rel_tol=float(tol.rel or 0.0), abs_tol=float(tol.abs or 0.0))


def _to_decimal(value: Any) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"invalid decimal: {value!r}") from exc
    if not parsed.is_finite():
        raise ValueError(f"non-finite decimal: {value!r}")
    return parsed


def _weighted_current_ratio(payload: dict[str, Any]) -> float:
    total = Decimal("0")
    hedged = Decimal("0")
    for row in payload["exposures"]:
        notional = _to_decimal(row["notional"])
        hedge = _to_decimal(row.get("hedge_ratio", "0")) if row.get("hedge_ratio") is not None else Decimal("0")
        total += notional
        hedged += notional * hedge
    if total <= 0:
        return 0.0
    return float(hedged / total)


def _bucket_label(days_to_maturity: int, buckets_days: tuple[int, ...]) -> str:
    prev = 0
    for day_max in buckets_days:
        if days_to_maturity <= day_max:
            lower = 0 if prev == 0 else prev + 1
            return f"{lower}-{day_max}"
        prev = day_max
    return f">{buckets_days[-1]}"


def _bucket_total_notionals(payload: dict[str, Any], *, as_of_date: str, buckets_days: tuple[int, ...]) -> dict[str, Decimal]:
    as_of = datetime.date.fromisoformat(as_of_date)
    out: dict[str, Decimal] = {}
    for row in payload["exposures"]:
        maturity = datetime.date.fromisoformat(str(row["maturity_date"]))
        days = (maturity - as_of).days
        label = _bucket_label(days, buckets_days)
        out[label] = out.get(label, Decimal("0")) + _to_decimal(row["notional"])
    return out


def _global_additional_notional(
    *,
    payload: dict[str, Any],
    base_snapshot: FxMarketSnapshot,
    scenario_spec: ScenarioSpec,
    target_worst_loss_total_domestic: float,
    policy: HedgePolicyV1,
) -> float:
    current_ratio = _weighted_current_ratio(payload)
    total_notional = float(sum(_to_decimal(row["notional"]) for row in payload["exposures"]))

    decision = run_treasury_advisory_v1(
        payload,
        base_snapshot=base_snapshot,
        scenario_spec=scenario_spec,
        target_worst_loss_domestic=target_worst_loss_total_domestic,
    )
    policy_result = apply_hedge_policy_v1(
        policy=policy,
        recommended_hedge_ratio=decision.hedge_recommendation.recommended_hedge_ratio,
    )
    return max(0.0, total_notional * (policy_result.output_hedge_ratio - current_ratio))


def test_rolling_hedge_ladder_end_to_end_deterministic() -> None:
    payload = {
        "contract_version": "v1",
        "company_id": "treasury-demo",
        "snapshot_id": "snap-usdils-20260304",
        "scenario_template_id": "usdils_spot_pm5",
        "exposures": [
            {
                "currency_pair": "USD/ILS",
                "direction": "receivable",
                "notional": "1000000",
                "maturity_date": "2026-03-24",
                "hedge_ratio": "0.60",
            },
            {
                "currency_pair": "USD/ILS",
                "direction": "receivable",
                "notional": "1500000",
                "maturity_date": "2026-04-23",
                "hedge_ratio": "0.50",
            },
            {
                "currency_pair": "USD/ILS",
                "direction": "receivable",
                "notional": "2000000",
                "maturity_date": "2026-05-23",
                "hedge_ratio": "0.40",
            },
        ],
    }

    base_snapshot = FxMarketSnapshot(
        as_of_ts=datetime.datetime(
            2026,
            3,
            4,
            12,
            0,
            0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
        ),
        spot_rate=3.70,
        df_domestic=0.997,
        df_foreign=0.996,
        domestic_currency="ILS",
    )
    scenario_spec = ScenarioSpec(
        schema_version=1,
        spot_shocks=(Decimal("-0.05"), Decimal("0.0"), Decimal("0.05")),
        df_domestic_shocks=(Decimal("0.0"),),
        df_foreign_shocks=(Decimal("0.0"),),
    )
    config = RollingHedgeLadderConfigV1(
        buckets_days=(30, 60, 90),
        roll_frequency_days=30,
        target_worst_loss_total_domestic=200000.0,
        as_of_date="2026-03-04",
        policy=HedgePolicyV1(
            policy_id="treasury-policy-1",
            min_hedge_ratio=0.5,
            max_hedge_ratio=0.9,
            rounding_lot_notional=50000.0,
            allow_overhedge=False,
        ),
    )

    out_a = compute_rolling_hedge_ladder_v1(
        payload,
        base_snapshot=base_snapshot,
        scenario_spec=scenario_spec,
        config=config,
    )
    out_b = compute_rolling_hedge_ladder_v1(
        payload,
        base_snapshot=base_snapshot,
        scenario_spec=scenario_spec,
        config=config,
    )

    assert out_a.to_dict() == out_b.to_dict()

    assert [row.exposures_count for row in out_a.buckets] == [1, 1, 1]
    assert [row.bucket_label for row in out_a.buckets] == ["0-30", "31-60", "61-90"]

    allocated_total = sum(row.hedge_recommendation.target_worst_loss_domestic for row in out_a.buckets)
    assert _close(allocated_total, config.target_worst_loss_total_domestic)

    for row in out_a.buckets:
        assert row.risk_summary.contract_version == "v1"
        assert row.hedge_recommendation.contract_version == "v1"
        assert row.policy_result is not None


def test_importer_bucket_recommendations_are_risk_driven_and_align_with_global_additional() -> None:
    payload = {
        "contract_version": "v1",
        "company_id": "g11-sim1-usdils-importer",
        "snapshot_id": "snap-usdils-20260305",
        "scenario_template_id": "usdils_spot_custom_5pt",
        "exposures": [
            {
                "currency_pair": "USD/ILS",
                "direction": "payable",
                "notional": "4200000",
                "maturity_date": "2026-03-25",
                "hedge_ratio": "0.35",
            },
            {
                "currency_pair": "USD/ILS",
                "direction": "payable",
                "notional": "3000000",
                "maturity_date": "2026-04-29",
                "hedge_ratio": "0.35",
            },
            {
                "currency_pair": "USD/ILS",
                "direction": "payable",
                "notional": "1800000",
                "maturity_date": "2026-07-03",
                "hedge_ratio": "0.35",
            },
        ],
    }

    base_snapshot = FxMarketSnapshot(
        as_of_ts=datetime.datetime(
            2026,
            3,
            5,
            12,
            0,
            0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
        ),
        spot_rate=3.70,
        df_domestic=0.997,
        df_foreign=0.996,
        domestic_currency="ILS",
    )
    scenario_spec = ScenarioSpec(
        schema_version=1,
        spot_shocks=(Decimal("-0.05"), Decimal("0.0"), Decimal("0.05")),
        df_domestic_shocks=(Decimal("0.0"),),
        df_foreign_shocks=(Decimal("0.0"),),
    )
    policy = HedgePolicyV1(
        policy_id="sim1-policy",
        min_hedge_ratio=0.20,
        max_hedge_ratio=0.70,
        rounding_lot_notional=10000.0,
        allow_overhedge=False,
    )
    config = RollingHedgeLadderConfigV1(
        buckets_days=(30, 60, 90, 180),
        roll_frequency_days=30,
        target_worst_loss_total_domestic=250000.0,
        as_of_date="2026-03-05",
        policy=policy,
    )

    out_a = compute_rolling_hedge_ladder_v1(payload, base_snapshot=base_snapshot, scenario_spec=scenario_spec, config=config)
    out_b = compute_rolling_hedge_ladder_v1(payload, base_snapshot=base_snapshot, scenario_spec=scenario_spec, config=config)
    assert out_a.to_dict() == out_b.to_dict()

    current_ratio = _weighted_current_ratio(payload)
    bucket_notionals = _bucket_total_notionals(payload, as_of_date=config.as_of_date, buckets_days=config.buckets_days)

    non_empty_bucket_rows = [row for row in out_a.buckets if row.exposures_count > 0]
    assert any(row.hedge_recommendation.recommended_hedge_ratio > current_ratio for row in non_empty_bucket_rows)

    bucket_additional = 0.0
    assert non_empty_bucket_rows
    for row in non_empty_bucket_rows:
        bucket_total = float(bucket_notionals[row.bucket_label])
        current_notional = bucket_total * current_ratio
        recommended_notional = bucket_total * row.hedge_recommendation.recommended_hedge_ratio
        additional = max(0.0, recommended_notional - current_notional)
        bucket_additional += additional
    assert bucket_additional > 0.0

    global_additional = _global_additional_notional(
        payload=payload,
        base_snapshot=base_snapshot,
        scenario_spec=scenario_spec,
        target_worst_loss_total_domestic=config.target_worst_loss_total_domestic,
        policy=policy,
    )
    assert global_additional > 0.0
    diff = abs(bucket_additional - global_additional)
    rel = diff / max(global_additional, 1.0)
    lot = float(policy.rounding_lot_notional or 0.0)
    assert diff <= max(lot * 2.0, global_additional * 0.01)
    assert rel <= 0.02


def test_exporter_bucket_recommendations_are_risk_driven_and_align_with_global_additional() -> None:
    payload = {
        "contract_version": "v1",
        "company_id": "g11-sim2-eurils-exporter",
        "snapshot_id": "snap-eurils-20260305",
        "scenario_template_id": "eurils_spot_tail_7pt",
        "exposures": [
            {
                "currency_pair": "EUR/ILS",
                "direction": "receivable",
                "notional": "1500000",
                "maturity_date": "2026-03-15",
                "hedge_ratio": "0.10",
            },
            {
                "currency_pair": "EUR/ILS",
                "direction": "receivable",
                "notional": "2000000",
                "maturity_date": "2026-04-14",
                "hedge_ratio": "0.10",
            },
            {
                "currency_pair": "EUR/ILS",
                "direction": "receivable",
                "notional": "2500000",
                "maturity_date": "2026-05-19",
                "hedge_ratio": "0.10",
            },
            {
                "currency_pair": "EUR/ILS",
                "direction": "receivable",
                "notional": "3000000",
                "maturity_date": "2026-08-12",
                "hedge_ratio": "0.10",
            },
        ],
    }

    base_snapshot = FxMarketSnapshot(
        as_of_ts=datetime.datetime(
            2026,
            3,
            5,
            12,
            0,
            0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
        ),
        spot_rate=4.02,
        df_domestic=0.997,
        df_foreign=0.996,
        domestic_currency="ILS",
    )
    scenario_spec = ScenarioSpec(
        schema_version=1,
        spot_shocks=(Decimal("-0.05"), Decimal("0.0"), Decimal("0.05")),
        df_domestic_shocks=(Decimal("0.0"),),
        df_foreign_shocks=(Decimal("0.0"),),
    )
    policy = HedgePolicyV1(
        policy_id="sim2-policy",
        min_hedge_ratio=0.00,
        max_hedge_ratio=0.90,
        rounding_lot_notional=25000.0,
        allow_overhedge=False,
    )
    config = RollingHedgeLadderConfigV1(
        buckets_days=(30, 60, 90, 180),
        roll_frequency_days=30,
        target_worst_loss_total_domestic=120000.0,
        as_of_date="2026-03-05",
        policy=policy,
    )

    out_a = compute_rolling_hedge_ladder_v1(payload, base_snapshot=base_snapshot, scenario_spec=scenario_spec, config=config)
    out_b = compute_rolling_hedge_ladder_v1(payload, base_snapshot=base_snapshot, scenario_spec=scenario_spec, config=config)
    assert out_a.to_dict() == out_b.to_dict()

    current_ratio = _weighted_current_ratio(payload)
    bucket_notionals = _bucket_total_notionals(payload, as_of_date=config.as_of_date, buckets_days=config.buckets_days)

    non_empty_bucket_rows = [row for row in out_a.buckets if row.exposures_count > 0]
    assert any(row.hedge_recommendation.recommended_hedge_ratio > current_ratio for row in non_empty_bucket_rows)

    bucket_additional = 0.0
    assert non_empty_bucket_rows
    for row in non_empty_bucket_rows:
        bucket_total = float(bucket_notionals[row.bucket_label])
        current_notional = bucket_total * current_ratio
        recommended_notional = bucket_total * row.hedge_recommendation.recommended_hedge_ratio
        additional = max(0.0, recommended_notional - current_notional)
        bucket_additional += additional
    assert bucket_additional > 0.0

    global_additional = _global_additional_notional(
        payload=payload,
        base_snapshot=base_snapshot,
        scenario_spec=scenario_spec,
        target_worst_loss_total_domestic=config.target_worst_loss_total_domestic,
        policy=policy,
    )
    assert global_additional > 0.0
    diff = abs(bucket_additional - global_additional)
    rel = diff / max(global_additional, 1.0)
    lot = float(policy.rounding_lot_notional or 0.0)
    assert diff <= max(lot * 2.0, global_additional * 0.01)
    assert rel <= 0.02
