from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from core.services.hedge_policy_constraints_v1 import HedgePolicyV1
from core.services.rolling_hedge_ladder_v1 import RollingHedgeLadderConfigV1


@dataclass(frozen=True)
class PolicyTemplateV1:
    template_id: str
    label: str
    hedge_policy: HedgePolicyV1
    ladder_config: RollingHedgeLadderConfigV1
    scenario_template_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "template_id": self.template_id,
            "label": self.label,
            "hedge_policy": {
                "contract_version": self.hedge_policy.contract_version,
                "policy_id": self.hedge_policy.policy_id,
                "min_hedge_ratio": self.hedge_policy.min_hedge_ratio,
                "max_hedge_ratio": self.hedge_policy.max_hedge_ratio,
                "rounding_lot_notional": self.hedge_policy.rounding_lot_notional,
                "allow_overhedge": self.hedge_policy.allow_overhedge,
            },
            "ladder_config": {
                "contract_version": self.ladder_config.contract_version,
                "buckets_days": list(self.ladder_config.buckets_days),
                "roll_frequency_days": self.ladder_config.roll_frequency_days,
                "target_worst_loss_total_domestic": self.ladder_config.target_worst_loss_total_domestic,
                "allocation_rule": self.ladder_config.allocation_rule,
                "as_of_date": self.ladder_config.as_of_date,
                "policy": {
                    "contract_version": self.ladder_config.policy.contract_version,
                    "policy_id": self.ladder_config.policy.policy_id,
                    "min_hedge_ratio": self.ladder_config.policy.min_hedge_ratio,
                    "max_hedge_ratio": self.ladder_config.policy.max_hedge_ratio,
                    "rounding_lot_notional": self.ladder_config.policy.rounding_lot_notional,
                    "allow_overhedge": self.ladder_config.policy.allow_overhedge,
                }
                if self.ladder_config.policy is not None
                else None,
            },
            "scenario_template_id": self.scenario_template_id,
        }


def _build_template(*, template_id: str, label: str, max_hedge_ratio: float, scenario_template_id: str) -> PolicyTemplateV1:
    policy = HedgePolicyV1(
        policy_id=template_id,
        min_hedge_ratio=0.0,
        max_hedge_ratio=max_hedge_ratio,
        rounding_lot_notional=50000.0,
        allow_overhedge=False,
    )
    ladder = RollingHedgeLadderConfigV1(
        buckets_days=(30, 60, 90, 180),
        roll_frequency_days=30,
        target_worst_loss_total_domestic=0.0,
        as_of_date="2000-01-01",
        policy=policy,
    )
    return PolicyTemplateV1(
        template_id=template_id,
        label=label,
        hedge_policy=policy,
        ladder_config=ladder,
        scenario_template_id=scenario_template_id,
    )


POLICY_TEMPLATES_V1: dict[str, PolicyTemplateV1] = {
    "TREASURY_STANDARD_70": _build_template(
        template_id="TREASURY_STANDARD_70",
        label="Treasury Standard 70%",
        max_hedge_ratio=0.70,
        scenario_template_id="USDILS_SPOT_PM7_BASELINE",
    ),
    "TREASURY_CONSERVATIVE_50": _build_template(
        template_id="TREASURY_CONSERVATIVE_50",
        label="Treasury Conservative 50%",
        max_hedge_ratio=0.50,
        scenario_template_id="USDILS_SPOT_PM7_BASELINE",
    ),
}


def get_policy_template_v1(template_id: str) -> PolicyTemplateV1:
    if not isinstance(template_id, str) or not template_id.strip():
        raise ValueError("template_id must be a non-empty string")
    key = template_id.strip()
    try:
        return POLICY_TEMPLATES_V1[key]
    except KeyError as exc:
        known = ", ".join(POLICY_TEMPLATES_V1.keys())
        raise KeyError(f"unknown policy template_id: {template_id!r}; known templates: {known}") from exc


def compute_requires_approval_v1(*, binding_constraints: Sequence[str], unmet_target_reason: str | None) -> bool:
    if unmet_target_reason is None:
        reason_present = False
    else:
        reason_present = bool(str(unmet_target_reason).strip())
    return bool(tuple(binding_constraints)) or reason_present


__all__ = [
    "PolicyTemplateV1",
    "POLICY_TEMPLATES_V1",
    "get_policy_template_v1",
    "compute_requires_approval_v1",
]
