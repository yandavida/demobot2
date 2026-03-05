from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioTemplateV1:
    template_id: str
    label: str
    shocks_pct: tuple[float, ...]
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.template_id, str) or not self.template_id.strip():
            raise ValueError("template_id must be non-empty")
        if not self.shocks_pct:
            raise ValueError("shocks_pct must be non-empty")
        if tuple(sorted(self.shocks_pct)) != self.shocks_pct:
            raise ValueError("shocks_pct must be sorted ascending")
        if 0.0 not in self.shocks_pct:
            raise ValueError("shocks_pct must include 0.0")

    def to_dict(self) -> dict[str, object]:
        return {
            "template_id": self.template_id,
            "label": self.label,
            "shocks_pct": list(self.shocks_pct),
            "description": self.description,
        }


SCENARIO_TEMPLATES_V1: dict[str, ScenarioTemplateV1] = {
    "STANDARD_7": ScenarioTemplateV1(
        template_id="STANDARD_7",
        label="Standard +/-7% shock set",
        shocks_pct=(-0.07, 0.0, 0.07),
        description="Baseline symmetric three-point stress grid.",
    ),
    "STRESS_10": ScenarioTemplateV1(
        template_id="STRESS_10",
        label="Stress +/-10% shock set",
        shocks_pct=(-0.10, 0.0, 0.10),
        description="Higher-volatility symmetric three-point stress grid.",
    ),
    "CRISIS_15": ScenarioTemplateV1(
        template_id="CRISIS_15",
        label="Crisis +/-15% five-point shock set",
        shocks_pct=(-0.15, -0.07, 0.0, 0.07, 0.15),
        description="Crisis envelope with inner and outer stress points.",
    ),
}


def get_scenario_template_v1(template_id: str) -> ScenarioTemplateV1:
    if not isinstance(template_id, str) or not template_id.strip():
        raise ValueError(f"UNKNOWN_SCENARIO_TEMPLATE: {template_id}")
    key = template_id.strip()
    template = SCENARIO_TEMPLATES_V1.get(key)
    if template is None:
        raise ValueError(f"UNKNOWN_SCENARIO_TEMPLATE: {template_id}")
    return template


def scenario_template_ids_v1() -> tuple[str, ...]:
    return tuple(SCENARIO_TEMPLATES_V1.keys())


__all__ = [
    "ScenarioTemplateV1",
    "SCENARIO_TEMPLATES_V1",
    "get_scenario_template_v1",
    "scenario_template_ids_v1",
]
