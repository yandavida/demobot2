from __future__ import annotations

import datetime
from typing import Iterable

import pytest

from core import numeric_policy
from core.pricing.fx import forward_mtm
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext
from tests.f8._support.f8_r1_loader import canonical_sha256


PRICE_TOL = numeric_policy.DEFAULT_TOLERANCES[numeric_policy.MetricClass.PRICE]
ABS_TOL = PRICE_TOL.abs or 1e-8


def _as_of_ts() -> datetime.datetime:
    return datetime.datetime(2026, 3, 2, 12, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))


def _context() -> ValuationContext:
    return ValuationContext(
        as_of_ts=_as_of_ts(),
        domestic_currency="ILS",
        strict_mode=True,
    )


def _contract(case: dict) -> fx_types.FXForwardContract:
    return fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="ILS",
        notional=float(case["notional"]),
        forward_date=datetime.date(2026, 4, 2),
        forward_rate=float(case["strike"]),
        direction=case["direction"],
    )


def _snapshot(case: dict) -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=_as_of_ts(),
        spot_rate=float(case["spot"]),
        df_domestic=float(case["dfd"]),
        df_foreign=float(case["dff"]),
    )


def _price(case: dict) -> fx_types.PricingResult:
    return forward_mtm.price_fx_forward_ctx(
        context=_context(),
        contract=_contract(case),
        market_snapshot=_snapshot(case),
        conventions=None,
    )


def _build_valuation_artifact(
    *,
    case_id: str,
    context: ValuationContext,
    contract: fx_types.FXForwardContract,
    snapshot_repr: dict,
    result: fx_types.PricingResult,
) -> dict:
    return {
        "case_id": case_id,
        "as_of_ts": context.as_of_ts.isoformat(),
        "reporting_currency": context.domestic_currency,
        "contract": {
            "base_currency": contract.base_currency,
            "quote_currency": contract.quote_currency,
            "notional": contract.notional,
            "forward_date": contract.forward_date.isoformat(),
            "forward_rate": contract.forward_rate,
            "direction": contract.direction,
        },
        "market_snapshot": snapshot_repr,
        "valuation": {
            "pv": result.pv,
            "currency": result.currency,
            "metric_class": result.metric_class.value if result.metric_class is not None else None,
            "details": result.details,
        },
    }


def _snapshot_repr_from_object(snapshot: fx_types.FxMarketSnapshot) -> dict:
    return {
        "as_of_ts": snapshot.as_of_ts.isoformat(),
        "spot_rate": snapshot.spot_rate,
        "df_domestic": snapshot.df_domestic,
        "df_foreign": snapshot.df_foreign,
    }


def _fixed_cases() -> list[dict]:
    return [
        {"case_id": "c01", "notional": "1000000", "spot": "3.6400", "strike": "3.6500", "dfd": "0.9950", "dff": "0.9982", "direction": "receive_foreign_pay_domestic"},
        {"case_id": "c02", "notional": "1200000", "spot": "3.7000", "strike": "3.5500", "dfd": "0.9850", "dff": "0.9930", "direction": "receive_foreign_pay_domestic"},
        {"case_id": "c03", "notional": "900000", "spot": "3.6800", "strike": "3.9500", "dfd": "0.9865", "dff": "0.9925", "direction": "receive_foreign_pay_domestic"},
        {"case_id": "c04", "notional": "1500000", "spot": "3.7600", "strike": "3.8200", "dfd": "0.9350", "dff": "0.9550", "direction": "pay_foreign_receive_domestic"},
        {"case_id": "c05", "notional": "800000", "spot": "3.6400", "strike": "3.6405", "dfd": "0.9999", "dff": "0.99995", "direction": "pay_foreign_receive_domestic"},
        {"case_id": "c06", "notional": "950000", "spot": "3.6100", "strike": "3.6000", "dfd": "0.9970", "dff": "0.9989", "direction": "receive_foreign_pay_domestic"},
        {"case_id": "c07", "notional": "1050000", "spot": "3.6700", "strike": "3.7000", "dfd": "0.9920", "dff": "0.9960", "direction": "pay_foreign_receive_domestic"},
        {"case_id": "c08", "notional": "1300000", "spot": "3.7500", "strike": "3.7300", "dfd": "0.9800", "dff": "0.9890", "direction": "receive_foreign_pay_domestic"},
        {"case_id": "c09", "notional": "1700000", "spot": "3.5800", "strike": "3.6200", "dfd": "0.9900", "dff": "0.9950", "direction": "pay_foreign_receive_domestic"},
        {"case_id": "c10", "notional": "2100000", "spot": "3.6600", "strike": "3.6100", "dfd": "0.9870", "dff": "0.9940", "direction": "receive_foreign_pay_domestic"},
    ]


def _sum_pv(cases: Iterable[dict]) -> float:
    return sum(_price(case).pv for case in cases)


def _manifest_hash_from_artifact_hashes(artifact_hashes: Iterable[str]) -> str:
    # Freeze policy: Option A — manifest is canonical sha256 over lexicographically sorted artifact sha256 list.
    return canonical_sha256({"artifact_sha256_sorted": sorted(artifact_hashes)})


def test_r5_t1_artifact_repeatability_determinism():
    case = _fixed_cases()[0]
    context = _context()
    contract = _contract(case)
    snapshot = _snapshot(case)
    result = _price(case)

    artifact_1 = _build_valuation_artifact(
        case_id=case["case_id"],
        context=context,
        contract=contract,
        snapshot_repr=_snapshot_repr_from_object(snapshot),
        result=result,
    )
    artifact_2 = _build_valuation_artifact(
        case_id=case["case_id"],
        context=context,
        contract=contract,
        snapshot_repr=_snapshot_repr_from_object(snapshot),
        result=result,
    )

    assert artifact_1 == artifact_2
    assert canonical_sha256(artifact_1) == canonical_sha256(artifact_2)


def test_r5_t2_dict_insertion_order_invariance():
    case = _fixed_cases()[1]
    context = _context()
    contract = _contract(case)
    result = _price(case)

    snapshot_order_a = {
        "as_of_ts": _as_of_ts().isoformat(),
        "spot_rate": float(case["spot"]),
        "df_domestic": float(case["dfd"]),
        "df_foreign": float(case["dff"]),
    }
    snapshot_order_b = {
        "df_foreign": float(case["dff"]),
        "df_domestic": float(case["dfd"]),
        "spot_rate": float(case["spot"]),
        "as_of_ts": _as_of_ts().isoformat(),
    }

    artifact_a = _build_valuation_artifact(
        case_id=case["case_id"],
        context=context,
        contract=contract,
        snapshot_repr=snapshot_order_a,
        result=result,
    )
    artifact_b = _build_valuation_artifact(
        case_id=case["case_id"],
        context=context,
        contract=contract,
        snapshot_repr=snapshot_order_b,
        result=result,
    )

    assert canonical_sha256(artifact_a) == canonical_sha256(artifact_b)


def test_r5_t3_snapshot_key_ordering_invariance():
    case = _fixed_cases()[2]
    context = _context()
    contract = _contract(case)
    result = _price(case)

    snapshot_repr_1 = {
        "as_of_ts": _as_of_ts().isoformat(),
        "spot_rate": float(case["spot"]),
        "df_domestic": float(case["dfd"]),
        "df_foreign": float(case["dff"]),
    }
    snapshot_repr_2 = {
        "spot_rate": float(case["spot"]),
        "as_of_ts": _as_of_ts().isoformat(),
        "df_foreign": float(case["dff"]),
        "df_domestic": float(case["dfd"]),
    }

    artifact_1 = _build_valuation_artifact(
        case_id=case["case_id"],
        context=context,
        contract=contract,
        snapshot_repr=snapshot_repr_1,
        result=result,
    )
    artifact_2 = _build_valuation_artifact(
        case_id=case["case_id"],
        context=context,
        contract=contract,
        snapshot_repr=snapshot_repr_2,
        result=result,
    )

    assert canonical_sha256(artifact_1) == canonical_sha256(artifact_2)


def test_r5_t4_aggregation_sum_pv_permutation_invariance():
    cases = _fixed_cases()
    assert len(cases) >= 10

    total_original = _sum_pv(cases)
    total_reversed = _sum_pv(reversed(cases))

    permutation = (3, 0, 9, 1, 6, 4, 8, 2, 7, 5)
    total_permuted = _sum_pv(cases[index] for index in permutation)

    assert abs(total_original - total_reversed) <= ABS_TOL
    assert abs(total_original - total_permuted) <= ABS_TOL


def test_r5_t5_manifest_hash_permutation_invariance():
    cases = _fixed_cases()

    def artifact_hashes(ordered_cases: Iterable[dict]) -> list[str]:
        output: list[str] = []
        context = _context()
        for case in ordered_cases:
            contract = _contract(case)
            snapshot = _snapshot(case)
            result = _price(case)
            artifact = _build_valuation_artifact(
                case_id=case["case_id"],
                context=context,
                contract=contract,
                snapshot_repr=_snapshot_repr_from_object(snapshot),
                result=result,
            )
            output.append(canonical_sha256(artifact))
        return output

    hashes_original = artifact_hashes(cases)
    hashes_reversed = artifact_hashes(reversed(cases))

    permutation = (3, 0, 9, 1, 6, 4, 8, 2, 7, 5)
    hashes_permuted = artifact_hashes(cases[index] for index in permutation)

    manifest_original = _manifest_hash_from_artifact_hashes(hashes_original)
    manifest_reversed = _manifest_hash_from_artifact_hashes(hashes_reversed)
    manifest_permuted = _manifest_hash_from_artifact_hashes(hashes_permuted)

    assert manifest_original == manifest_reversed
    assert manifest_original == manifest_permuted


@pytest.mark.skip(reason="Optional T6 not enabled: parallel scheduling can introduce CI variability across environments")
def test_r5_t6_parallel_consistency_optional_only_if_ci_safe():
    assert True
