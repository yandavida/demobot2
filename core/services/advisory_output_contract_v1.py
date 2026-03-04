from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields
from dataclasses import is_dataclass
from typing import Any
from typing import Literal

from core.services.hedge_recommendation_v1 import HedgeRecommendationV1
from core.services.scenario_risk_summary_v1 import ScenarioRiskSummaryV1


def _serialize(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()

    if is_dataclass(value):
        out: dict[str, Any] = {}
        for item in fields(value):
            out[item.name] = _serialize(getattr(value, item.name))
        return out

    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    return value


@dataclass(frozen=True)
class AdvisoryDecisionV1:
    contract_version: Literal["v1"] = "v1"
    company_id: str = ""
    snapshot_id: str = ""
    scenario_template_id: str = ""
    risk_summary: ScenarioRiskSummaryV1 | None = None
    hedge_recommendation: HedgeRecommendationV1 | None = None
    delta_exposure_aggregate_domestic: float | None = None
    notes: tuple[str, ...] | list[str] = ()

    def __post_init__(self) -> None:
        if self.contract_version != "v1":
            raise ValueError("contract_version must be v1")
        if not isinstance(self.company_id, str) or not self.company_id.strip():
            raise ValueError("company_id must be non-empty")
        if not isinstance(self.snapshot_id, str) or not self.snapshot_id.strip():
            raise ValueError("snapshot_id must be non-empty")
        if not isinstance(self.scenario_template_id, str) or not self.scenario_template_id.strip():
            raise ValueError("scenario_template_id must be non-empty")
        if not isinstance(self.risk_summary, ScenarioRiskSummaryV1):
            raise ValueError("risk_summary must be ScenarioRiskSummaryV1")
        if not isinstance(self.hedge_recommendation, HedgeRecommendationV1):
            raise ValueError("hedge_recommendation must be HedgeRecommendationV1")

        notes_tuple = tuple(str(note) for note in self.notes)
        object.__setattr__(self, "notes", notes_tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "company_id": self.company_id,
            "snapshot_id": self.snapshot_id,
            "scenario_template_id": self.scenario_template_id,
            "risk_summary": _serialize(self.risk_summary),
            "hedge_recommendation": _serialize(self.hedge_recommendation),
            "delta_exposure_aggregate_domestic": self.delta_exposure_aggregate_domestic,
            "notes": list(self.notes),
        }


__all__ = ["AdvisoryDecisionV1"]
