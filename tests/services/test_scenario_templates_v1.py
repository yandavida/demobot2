from __future__ import annotations

from core.services.scenario_templates_v1 import SCENARIO_TEMPLATES_V1
from core.services.scenario_templates_v1 import get_scenario_template_v1


def test_catalog_contains_templates() -> None:
    assert "STANDARD_7" in SCENARIO_TEMPLATES_V1
    assert "STRESS_10" in SCENARIO_TEMPLATES_V1
    assert "CRISIS_15" in SCENARIO_TEMPLATES_V1


def test_lookup_returns_template() -> None:
    template = get_scenario_template_v1("STANDARD_7")
    assert template.shocks_pct == (-0.07, 0.0, 0.07)


def test_lookup_unknown_raises() -> None:
    try:
        get_scenario_template_v1("UNKNOWN")
    except ValueError as exc:
        assert "UNKNOWN_SCENARIO_TEMPLATE" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown template id")


def test_templates_are_deterministic() -> None:
    t1 = get_scenario_template_v1("CRISIS_15")
    t2 = get_scenario_template_v1("CRISIS_15")

    assert t1.to_dict() == t2.to_dict()


def test_shocks_are_sorted_and_include_zero() -> None:
    for template in SCENARIO_TEMPLATES_V1.values():
        assert tuple(sorted(template.shocks_pct)) == template.shocks_pct
        assert 0.0 in template.shocks_pct
