from __future__ import annotations

import json

import pytest

from core.services.policy_templates_v1 import POLICY_TEMPLATES_V1
from core.services.policy_templates_v1 import compute_requires_approval_v1
from core.services.policy_templates_v1 import get_policy_template_v1


def test_catalog_contains_expected_templates() -> None:
    assert "TREASURY_STANDARD_70" in POLICY_TEMPLATES_V1
    assert "TREASURY_CONSERVATIVE_50" in POLICY_TEMPLATES_V1
    assert list(POLICY_TEMPLATES_V1.keys()) == [
        "TREASURY_STANDARD_70",
        "TREASURY_CONSERVATIVE_50",
    ]


def test_get_policy_template_unknown_raises() -> None:
    with pytest.raises(KeyError, match="unknown policy template_id"):
        get_policy_template_v1("DOES_NOT_EXIST")


def test_template_objects_are_deterministic_to_dict() -> None:
    template_a = get_policy_template_v1("TREASURY_STANDARD_70")
    template_b = get_policy_template_v1("TREASURY_STANDARD_70")

    json_a = json.dumps(template_a.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    json_b = json.dumps(template_b.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    assert template_a.to_dict() == template_b.to_dict()
    assert json_a == json_b


def test_requires_approval_logic() -> None:
    assert compute_requires_approval_v1(binding_constraints=(), unmet_target_reason=None) is False
    assert compute_requires_approval_v1(binding_constraints=("MAX_HEDGE_RATIO",), unmet_target_reason=None) is True
    assert compute_requires_approval_v1(binding_constraints=(), unmet_target_reason="MAX_HEDGE_CAP") is True
