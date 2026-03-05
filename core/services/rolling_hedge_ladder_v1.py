from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields
from dataclasses import is_dataclass
import datetime
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any
from typing import Literal

from core.numeric_policy import DEFAULT_TOLERANCES
from core.numeric_policy import MetricClass
from core.services.advisory_output_contract_v1 import AdvisoryDecisionV1
from core.services.advisory_read_model_v1 import run_treasury_advisory_v1
from core.services.hedge_policy_constraints_v1 import HedgePolicyV1
from core.services.hedge_policy_constraints_v1 import PolicyApplicationResultV1
from core.services.hedge_policy_constraints_v1 import apply_hedge_policy_v1
from core.services.hedge_recommendation_v1 import HedgeRecommendationV1
from core.services.scenario_risk_summary_v1 import ScenarioRiskSummaryV1


@dataclass(frozen=True)
class RollingHedgeLadderConfigV1:
    contract_version: Literal["v1"] = "v1"
    buckets_days: tuple[int, ...] = ()
    roll_frequency_days: int = 0
    target_worst_loss_total_domestic: float = 0.0
    allocation_rule: Literal["PROPORTIONAL_TO_UNHEDGED_LOSS"] = "PROPORTIONAL_TO_UNHEDGED_LOSS"
    as_of_date: str = ""
    policy: HedgePolicyV1 | None = None

    def __post_init__(self) -> None:
        if self.contract_version != "v1":
            raise ValueError("contract_version must be v1")
        if not self.buckets_days:
            raise ValueError("buckets_days must be non-empty")
        if any(day <= 0 for day in self.buckets_days):
            raise ValueError("buckets_days must contain positive integers")
        if tuple(sorted(self.buckets_days)) != tuple(self.buckets_days):
            raise ValueError("buckets_days must be sorted ascending")
        if self.roll_frequency_days <= 0:
            raise ValueError("roll_frequency_days must be > 0")
        if self.target_worst_loss_total_domestic < 0:
            raise ValueError("target_worst_loss_total_domestic must be >= 0")
        if self.allocation_rule != "PROPORTIONAL_TO_UNHEDGED_LOSS":
            raise ValueError("unsupported allocation_rule")
        if not isinstance(self.as_of_date, str) or not self.as_of_date.strip():
            raise ValueError("as_of_date is required")
        datetime.date.fromisoformat(self.as_of_date)


@dataclass(frozen=True)
class BucketRowV1:
    bucket_label: str
    bucket_day_max: int
    exposures_count: int
    current_hedge_ratio_effective: float
    risk_summary: ScenarioRiskSummaryV1
    hedge_recommendation: HedgeRecommendationV1
    policy_result: PolicyApplicationResultV1 | None
    recommended_forward_notional: float | None


@dataclass(frozen=True)
class LadderTotalsV1:
    total_exposures: int
    total_recommended_forward_notional: float | None
    total_expected_worst_loss_domestic: float


@dataclass(frozen=True)
class RollingHedgeLadderResultV1:
    contract_version: Literal["v1"]
    company_id: str
    snapshot_id: str
    scenario_template_id: str
    buckets: tuple[BucketRowV1, ...]
    totals: LadderTotalsV1
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "company_id": self.company_id,
            "snapshot_id": self.snapshot_id,
            "scenario_template_id": self.scenario_template_id,
            "buckets": _serialize(self.buckets),
            "totals": _serialize(self.totals),
            "notes": list(self.notes),
        }


def _serialize(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    if is_dataclass(value):
        out: dict[str, Any] = {}
        for item in fields(value):
            out[item.name] = _serialize(getattr(value, item.name))
        return out
    if isinstance(value, tuple):
        return [_serialize(v) for v in value]
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    return value


def _to_decimal(value: Any) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"invalid decimal: {value!r}") from exc
    if not parsed.is_finite():
        raise ValueError(f"non-finite decimal: {value!r}")
    return parsed


def _tiny_guard() -> Decimal:
    tol = DEFAULT_TOLERANCES[MetricClass.PNL]
    return Decimal(str(tol.abs or 0.0))


def _rounding_unit() -> Decimal:
    # Deterministic nearest-unit rounding for allocated targets.
    return Decimal("1")


def _bucket_label(prev_max: int, current_max: int) -> str:
    lower = 0 if prev_max == 0 else prev_max + 1
    return f"{lower}-{current_max}"


def _exposure_sort_key(exposure: dict[str, Any]) -> tuple[str, str, str, str, str]:
    pair = str(exposure.get("currency_pair", "")).upper()
    maturity = str(exposure.get("maturity_date", ""))
    direction = str(exposure.get("direction", "")).lower()
    notional = str(_to_decimal(exposure.get("notional", "0")))
    hedge = exposure.get("hedge_ratio")
    hedge_str = "" if hedge is None else str(_to_decimal(hedge))
    return (pair, maturity, direction, notional, hedge_str)


def _days_to_maturity(exposure: dict[str, Any], as_of: datetime.date) -> int:
    maturity = datetime.date.fromisoformat(str(exposure["maturity_date"]))
    return (maturity - as_of).days


def _assign_bucket(days_to_maturity: int, buckets_days: tuple[int, ...]) -> tuple[str, int]:
    prev = 0
    for day_max in buckets_days:
        if days_to_maturity <= day_max:
            return _bucket_label(prev, day_max), day_max
        prev = day_max
    return f">{buckets_days[-1]}", -1


def _weighted_current_hedge_ratio(exposures: list[dict[str, Any]]) -> float:
    total = Decimal("0")
    hedged = Decimal("0")
    for row in exposures:
        notional = _to_decimal(row["notional"])
        hedge = _to_decimal(row.get("hedge_ratio", "0")) if row.get("hedge_ratio") is not None else Decimal("0")
        total += notional
        hedged += notional * hedge
    if total <= 0:
        return 0.0
    return float(hedged / total)


def _total_notional(exposures: list[dict[str, Any]]) -> Decimal:
    total = Decimal("0")
    for row in exposures:
        total += _to_decimal(row["notional"])
    return total


def _bucket_payload(payload: dict[str, Any], exposures: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "contract_version": payload["contract_version"],
        "company_id": payload["company_id"],
        "snapshot_id": payload["snapshot_id"],
        "scenario_template_id": payload["scenario_template_id"],
        "exposures": [dict(row) for row in exposures],
    }


def compute_rolling_hedge_ladder_v1(
    payload: dict,
    *,
    base_snapshot,
    scenario_spec,
    config: RollingHedgeLadderConfigV1,
) -> RollingHedgeLadderResultV1:
    if not isinstance(payload, dict):
        raise ValueError("payload must be dict")
    if not isinstance(config, RollingHedgeLadderConfigV1):
        raise ValueError("config must be RollingHedgeLadderConfigV1")

    as_of = datetime.date.fromisoformat(config.as_of_date)
    exposures_raw = payload.get("exposures")
    if not isinstance(exposures_raw, list):
        raise ValueError("payload.exposures must be list")

    buckets_map: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in exposures_raw:
        if not isinstance(row, dict):
            raise ValueError("each exposure must be dict")
        days = _days_to_maturity(row, as_of)
        label, day_max = _assign_bucket(days, config.buckets_days)
        buckets_map.setdefault((label, day_max), []).append(dict(row))

    ordered_bucket_keys: list[tuple[str, int]] = []
    prev = 0
    for day_max in config.buckets_days:
        key = (_bucket_label(prev, day_max), day_max)
        if key in buckets_map:
            ordered_bucket_keys.append(key)
        prev = day_max
    overflow_key = (f">{config.buckets_days[-1]}", -1)
    if overflow_key in buckets_map:
        ordered_bucket_keys.append(overflow_key)

    for key in ordered_bucket_keys:
        buckets_map[key] = sorted(buckets_map[key], key=_exposure_sort_key)

    pre_bucket_decisions: list[AdvisoryDecisionV1] = []
    bucket_current_ratios: list[float] = []
    bucket_unhedged_losses: list[Decimal] = []

    tiny = _tiny_guard()
    total_target = Decimal(str(config.target_worst_loss_total_domestic))
    for key in ordered_bucket_keys:
        exposures = buckets_map[key]
        decision = run_treasury_advisory_v1(
            _bucket_payload(payload, exposures),
            base_snapshot=base_snapshot,
            scenario_spec=scenario_spec,
            target_worst_loss_domestic=float(total_target),
        )
        pre_bucket_decisions.append(decision)

        current_ratio = _weighted_current_hedge_ratio(exposures)
        bucket_current_ratios.append(current_ratio)

        current_worst_loss = Decimal(str(abs(decision.risk_summary.worst_loss_domestic)))
        unhedged_fraction = max(Decimal("1") - Decimal(str(current_ratio)), tiny)
        bucket_unhedged_losses.append(current_worst_loss / unhedged_fraction)

    total_unhedged = sum(bucket_unhedged_losses, Decimal("0"))
    unit = _rounding_unit()
    bucket_targets: list[Decimal] = []
    if total_unhedged <= tiny:
        bucket_targets = [Decimal("0") for _ in ordered_bucket_keys]
    else:
        for idx, unhedged_loss in enumerate(bucket_unhedged_losses):
            if idx < len(bucket_unhedged_losses) - 1:
                raw = total_target * (unhedged_loss / total_unhedged)
                rounded = (raw / unit).to_integral_value() * unit
                bucket_targets.append(rounded)
            else:
                bucket_targets.append(total_target - sum(bucket_targets, Decimal("0")))

    bucket_rows: list[BucketRowV1] = []
    for idx, key in enumerate(ordered_bucket_keys):
        label, day_max = key
        exposures = buckets_map[key]
        target_for_bucket = float(bucket_targets[idx])
        decision = run_treasury_advisory_v1(
            _bucket_payload(payload, exposures),
            base_snapshot=base_snapshot,
            scenario_spec=scenario_spec,
            target_worst_loss_domestic=target_for_bucket,
        )

        hedge_recommendation = decision.hedge_recommendation
        policy_result = None

        if config.policy is not None:
            policy_result = apply_hedge_policy_v1(
                policy=config.policy,
                recommended_hedge_ratio=hedge_recommendation.recommended_hedge_ratio,
            )
            output_ratio = policy_result.output_hedge_ratio
            expected_worst = hedge_recommendation.implied_worst_loss_unhedged_domestic * max(0.0, 1.0 - output_ratio)
            hedge_recommendation = HedgeRecommendationV1(
                contract_version=hedge_recommendation.contract_version,
                current_hedge_ratio=hedge_recommendation.current_hedge_ratio,
                target_worst_loss_domestic=hedge_recommendation.target_worst_loss_domestic,
                implied_worst_loss_unhedged_domestic=hedge_recommendation.implied_worst_loss_unhedged_domestic,
                recommended_hedge_ratio=output_ratio,
                expected_worst_loss_domestic=expected_worst,
            )

        total_notional = _total_notional(exposures)
        recommended_notional = float(total_notional * Decimal(str(hedge_recommendation.recommended_hedge_ratio)))

        bucket_rows.append(
            BucketRowV1(
                bucket_label=label,
                bucket_day_max=day_max,
                exposures_count=len(exposures),
                current_hedge_ratio_effective=_weighted_current_hedge_ratio(exposures),
                risk_summary=decision.risk_summary,
                hedge_recommendation=hedge_recommendation,
                policy_result=policy_result,
                recommended_forward_notional=recommended_notional,
            )
        )

    total_recommended_notional = sum(
        (Decimal(str(row.recommended_forward_notional)) for row in bucket_rows if row.recommended_forward_notional is not None),
        Decimal("0"),
    )
    total_expected_worst = sum(
        (Decimal(str(row.hedge_recommendation.expected_worst_loss_domestic)) for row in bucket_rows),
        Decimal("0"),
    )

    notes: list[str] = []
    if config.policy is not None:
        notes.append("POLICY_APPLIED")
    if overflow_key in buckets_map:
        notes.append("OVERFLOW_BUCKET_INCLUDED")

    return RollingHedgeLadderResultV1(
        contract_version="v1",
        company_id=str(payload.get("company_id", "")),
        snapshot_id=str(payload.get("snapshot_id", "")),
        scenario_template_id=str(payload.get("scenario_template_id", "")),
        buckets=tuple(bucket_rows),
        totals=LadderTotalsV1(
            total_exposures=len(exposures_raw),
            total_recommended_forward_notional=float(total_recommended_notional),
            total_expected_worst_loss_domestic=float(total_expected_worst),
        ),
        notes=tuple(notes),
    )


__all__ = [
    "BucketRowV1",
    "LadderTotalsV1",
    "RollingHedgeLadderConfigV1",
    "RollingHedgeLadderResultV1",
    "compute_rolling_hedge_ladder_v1",
]
