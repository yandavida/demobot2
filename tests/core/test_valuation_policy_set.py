from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError

import pytest

from core.contracts.valuation_policy_set import ValuationPolicySet


def _valuation_policy_set(**overrides) -> ValuationPolicySet:
    payload = {
        "valuation_policy_id": "vps-fx-options-core",
        "model_family": "black_scholes_crr",
        "pricing_engine_policy": "engine.policy.v1",
        "numeric_policy_id": "numeric.policy.v1",
        "tolerance_policy_id": "tol.policy.v1",
        "calibration_recipe_id": "cal.recipe.v1",
        "approval_status": "approved",
        "policy_version": "v1",
        "policy_owner": "treasury_risk_committee",
        "created_timestamp": datetime.datetime(2026, 3, 8, 12, 0, 0, tzinfo=datetime.timezone.utc),
    }
    payload.update(overrides)
    return ValuationPolicySet(**payload)


def test_valuation_policy_set_construction() -> None:
    policy = _valuation_policy_set()

    assert policy.valuation_policy_id == "vps-fx-options-core"
    assert policy.policy_version == "v1"
    assert policy.approval_status == "approved"


def test_valuation_policy_set_is_immutable() -> None:
    policy = _valuation_policy_set()

    with pytest.raises(FrozenInstanceError):
        policy.approval_status = "retired"


def test_valuation_policy_set_requires_all_fields() -> None:
    with pytest.raises(TypeError):
        ValuationPolicySet(
            valuation_policy_id="vps-fx-options-core",
            model_family="black_scholes_crr",
            pricing_engine_policy="engine.policy.v1",
            numeric_policy_id="numeric.policy.v1",
            tolerance_policy_id="tol.policy.v1",
            calibration_recipe_id="cal.recipe.v1",
            approval_status="approved",
            policy_version="v1",
            created_timestamp=datetime.datetime(
                2026,
                3,
                8,
                12,
                0,
                0,
                tzinfo=datetime.timezone.utc,
            ),
        )
