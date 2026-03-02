from __future__ import annotations

from pathlib import Path

import pytest

from core.pricing.fx import forward_mtm
from tests.f8._support.f8_r1_loader import canonical_sha256
from tests.f8._support.f8_r1_loader import load_external_forward_cases


DATASET_PATH = Path(__file__).resolve().parent / "_data" / "f8_r1_forward_cases.json"
CASES = load_external_forward_cases(DATASET_PATH)


def _case_id(case) -> str:
    return case.case_id


def test_r1_dataset_has_minimum_forward_cases():
    assert len(CASES) >= 5


@pytest.mark.parametrize("case", CASES, ids=_case_id)
def test_r1_external_reference_forward_mtm(case):
    result = forward_mtm.price_fx_forward_ctx(
        context=case.context,
        contract=case.contract,
        market_snapshot=case.market_snapshot,
        conventions=None,
    )

    assert result.currency == case.expected_currency
    assert result.currency == case.context.domestic_currency
    assert result.metric_class == case.expected_metric_class
    assert case.expected_metric_class_raw == "MTM"
    assert abs(result.pv - case.expected_pv) <= case.tolerance_abs
    assert canonical_sha256(case.artifact) == case.sha256
