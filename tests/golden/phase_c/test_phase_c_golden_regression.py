from __future__ import annotations

import datetime
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest

from core.contracts.canonical_serialization_v1 import canonical_decimal_text_v1
from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.resolved_option_valuation_inputs_v1 import NumericalPolicySnapshotV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedCurveInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxKernelScalarsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedRatePointV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedSpotInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityInputV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedVolatilityPointV1
from core.pricing.black_scholes_european_fx_engine_v1 import BlackScholesEuropeanFxEngineV1
from core.services.pricing_artifact_builder_v1 import build_option_pricing_artifact_v1


pytestmark = pytest.mark.golden

MANIFEST_PATH = Path("tests/golden/phase_c/datasets_manifest.json")
HASHES_PATH = Path("tests/golden/phase_c/expected_hashes.json")


def _sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        digest.update(handle.read())
    return digest.hexdigest()


def _parse_date(value: str) -> datetime.date:
    return datetime.date.fromisoformat(value)


def _parse_time(value: str) -> datetime.time:
    return datetime.time.fromisoformat(value)


def _parse_datetime(value: str) -> datetime.datetime:
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("valuation timestamps must be timezone-aware")
    return parsed


def _build_resolved_fx_inputs(payload: dict[str, object]) -> ResolvedFxOptionValuationInputsV1:
    contract_data = payload["fx_option_contract"]
    if not isinstance(contract_data, dict):
        raise ValueError("fx_option_contract must be an object")

    spot_data = payload["spot"]
    if not isinstance(spot_data, dict):
        raise ValueError("spot must be an object")

    domestic_curve_data = payload["domestic_curve"]
    if not isinstance(domestic_curve_data, dict):
        raise ValueError("domestic_curve must be an object")

    foreign_curve_data = payload["foreign_curve"]
    if not isinstance(foreign_curve_data, dict):
        raise ValueError("foreign_curve must be an object")

    vol_surface_data = payload["volatility_surface"]
    if not isinstance(vol_surface_data, dict):
        raise ValueError("volatility_surface must be an object")

    numeric_policy_data = payload["numerical_policy_snapshot"]
    if not isinstance(numeric_policy_data, dict):
        raise ValueError("numerical_policy_snapshot must be an object")

    scalar_data = payload["resolved_kernel_scalars"]
    if not isinstance(scalar_data, dict):
        raise ValueError("resolved_kernel_scalars must be an object")

    def _curve_points(curve_payload: dict[str, object]) -> tuple[ResolvedRatePointV1, ...]:
        points = curve_payload["points"]
        if not isinstance(points, list):
            raise ValueError("curve points must be a list")
        return tuple(
            ResolvedRatePointV1(tenor_label=point["tenor_label"], zero_rate=Decimal(str(point["zero_rate"])))
            for point in points
            if isinstance(point, dict)
        )

    def _vol_points(surface_payload: dict[str, object]) -> tuple[ResolvedVolatilityPointV1, ...]:
        points = surface_payload["points"]
        if not isinstance(points, list):
            raise ValueError("volatility points must be a list")
        return tuple(
            ResolvedVolatilityPointV1(
                tenor_label=point["tenor_label"],
                strike=Decimal(str(point["strike"])),
                implied_vol=Decimal(str(point["implied_vol"])),
            )
            for point in points
            if isinstance(point, dict)
        )

    return ResolvedFxOptionValuationInputsV1(
        fx_option_contract=FxOptionRuntimeContractV1(
            contract_id=contract_data["contract_id"],
            currency_pair_orientation=contract_data["currency_pair_orientation"],
            base_currency=contract_data["base_currency"],
            quote_currency=contract_data["quote_currency"],
            option_type=contract_data["option_type"],
            exercise_style=contract_data["exercise_style"],
            strike=Decimal(str(contract_data["strike"])),
            expiry_date=_parse_date(contract_data["expiry_date"]),
            expiry_cutoff_time=_parse_time(contract_data["expiry_cutoff_time"]),
            expiry_cutoff_timezone=contract_data["expiry_cutoff_timezone"],
            notional=Decimal(str(contract_data["notional"])),
            notional_currency_semantics=contract_data["notional_currency_semantics"],
            premium_currency=contract_data["premium_currency"],
            premium_payment_date=_parse_date(contract_data["premium_payment_date"]),
            settlement_style=contract_data["settlement_style"],
            settlement_date=_parse_date(contract_data["settlement_date"]),
            settlement_calendar_refs=tuple(contract_data["settlement_calendar_refs"]),
            fixing_source=contract_data["fixing_source"],
            fixing_date=_parse_date(contract_data["fixing_date"]),
            domestic_curve_id=contract_data["domestic_curve_id"],
            foreign_curve_id=contract_data["foreign_curve_id"],
            volatility_surface_quote_convention=contract_data["volatility_surface_quote_convention"],
        ),
        valuation_timestamp=_parse_datetime(str(payload["valuation_timestamp"])),
        spot=ResolvedSpotInputV1(
            underlying_instrument_ref=spot_data["underlying_instrument_ref"],
            spot=Decimal(str(spot_data["spot"])),
        ),
        domestic_curve=ResolvedCurveInputV1(
            curve_id=domestic_curve_data["curve_id"],
            quote_convention=domestic_curve_data["quote_convention"],
            interpolation_method=domestic_curve_data["interpolation_method"],
            extrapolation_policy=domestic_curve_data["extrapolation_policy"],
            basis_timestamp=_parse_datetime(domestic_curve_data["basis_timestamp"]),
            source_lineage_ref=domestic_curve_data["source_lineage_ref"],
            points=_curve_points(domestic_curve_data),
        ),
        foreign_curve=ResolvedCurveInputV1(
            curve_id=foreign_curve_data["curve_id"],
            quote_convention=foreign_curve_data["quote_convention"],
            interpolation_method=foreign_curve_data["interpolation_method"],
            extrapolation_policy=foreign_curve_data["extrapolation_policy"],
            basis_timestamp=_parse_datetime(foreign_curve_data["basis_timestamp"]),
            source_lineage_ref=foreign_curve_data["source_lineage_ref"],
            points=_curve_points(foreign_curve_data),
        ),
        volatility_surface=ResolvedVolatilityInputV1(
            surface_id=vol_surface_data["surface_id"],
            quote_convention=vol_surface_data["quote_convention"],
            interpolation_method=vol_surface_data["interpolation_method"],
            extrapolation_policy=vol_surface_data["extrapolation_policy"],
            basis_timestamp=_parse_datetime(vol_surface_data["basis_timestamp"]),
            source_lineage_ref=vol_surface_data["source_lineage_ref"],
            points=_vol_points(vol_surface_data),
        ),
        day_count_basis=str(payload["day_count_basis"]),
        calendar_set=tuple(payload["calendar_set"]),
        settlement_conventions=tuple(payload["settlement_conventions"]),
        premium_conventions=tuple(payload["premium_conventions"]),
        numerical_policy_snapshot=NumericalPolicySnapshotV1(
            numeric_policy_id=numeric_policy_data["numeric_policy_id"],
            tolerance=Decimal(str(numeric_policy_data["tolerance"])),
            max_iterations=int(numeric_policy_data["max_iterations"]),
            rounding_decimals=int(numeric_policy_data["rounding_decimals"]),
        ),
        resolved_kernel_scalars=ResolvedFxKernelScalarsV1(
            domestic_rate=Decimal(str(scalar_data["domestic_rate"])),
            foreign_rate=Decimal(str(scalar_data["foreign_rate"])),
            volatility=Decimal(str(scalar_data["volatility"])),
            time_to_expiry_years=Decimal(str(scalar_data["time_to_expiry_years"])),
        ),
        resolved_basis_hash=str(payload["resolved_basis_hash"]),
    )


def _artifact_payload(dataset_id: str, version: int, resolved_payload: dict[str, object]) -> dict[str, object]:
    resolved_inputs = _build_resolved_fx_inputs(resolved_payload)
    valuation_result = BlackScholesEuropeanFxEngineV1().value(resolved_inputs)
    artifact = build_option_pricing_artifact_v1(valuation_result=valuation_result)

    return {
        "dataset_id": dataset_id,
        "version": version,
        "artifact_contract_name": artifact.artifact_contract_name,
        "artifact_contract_version": artifact.artifact_contract_version,
        "canonical_payload_hash": artifact.canonical_payload_hash,
        "valuation_result": {
            "engine_name": valuation_result.engine_name,
            "engine_version": valuation_result.engine_version,
            "model_name": valuation_result.model_name,
            "model_version": valuation_result.model_version,
            "resolved_input_contract_name": valuation_result.resolved_input_contract_name,
            "resolved_input_contract_version": valuation_result.resolved_input_contract_version,
            "resolved_input_reference": valuation_result.resolved_input_reference,
            "valuation_measures": [
                {
                    "measure_name": measure.measure_name.value,
                    "value": canonical_decimal_text_v1(measure.value),
                }
                for measure in valuation_result.valuation_measures
            ],
        },
    }


def test_phase_c_expected_files_match_expected_hashes() -> None:
    data = json.loads(HASHES_PATH.read_text(encoding="utf-8"))
    for relative_path, expected_hash in data.items():
        file_path = Path(relative_path)
        assert file_path.exists(), f"expected file missing: {file_path}"
        assert _sha256_hex(file_path) == expected_hash, f"hash mismatch for {file_path}"


def test_phase_c_replay_manifest_driven_regression() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(manifest, list) and manifest, "phase_c datasets_manifest must be a non-empty array"

    for entry in manifest:
        dataset_id = entry["dataset_id"]
        version = entry["version"]
        input_file = Path(entry["input_file"])
        expected_file = Path(entry["expected_file"])

        assert input_file.exists(), f"input file missing: {input_file}"
        assert expected_file.exists(), f"expected file missing: {expected_file}"

        assert _sha256_hex(input_file) == entry["input_sha256"], f"input sha mismatch for {dataset_id}"
        assert _sha256_hex(expected_file) == entry["expected_sha256"], f"expected sha mismatch for {dataset_id}"

        payload = json.loads(input_file.read_text(encoding="utf-8"))
        expected = json.loads(expected_file.read_text(encoding="utf-8"))

        actual = _artifact_payload(dataset_id, version, payload["resolved_inputs"])
        assert actual == expected