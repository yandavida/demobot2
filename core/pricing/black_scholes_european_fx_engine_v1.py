from __future__ import annotations

from dataclasses import dataclass

from core.contracts.option_pricing_engine_boundary_v1 import ensure_pure_option_pricing_input_v1
from core.contracts.option_valuation_result_v1 import OptionValuationResultV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.pricing.black_scholes_fx_kernel_v1 import black_scholes_fx_measures_v1


ENGINE_NAME_V1 = "black_scholes_european_fx_engine"
ENGINE_VERSION_V1 = "1.0.0"
MODEL_NAME_V1 = "garman_kohlhagen"
MODEL_VERSION_V1 = "1.0.0"
RESOLVED_INPUT_CONTRACT_NAME_V1 = "ResolvedFxOptionValuationInputsV1"
RESOLVED_INPUT_CONTRACT_VERSION_V1 = "1.0.0"


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _extract_kernel_inputs_v1(resolved_inputs: ResolvedFxOptionValuationInputsV1):
    if resolved_inputs.fx_option_contract.exercise_style != "european":
        raise ValueError("fx_option_contract.exercise_style must be european for BlackScholesEuropeanFxEngineV1")
    scalars = resolved_inputs.resolved_kernel_scalars

    return (
        resolved_inputs.fx_option_contract.option_type,
        resolved_inputs.spot.spot,
        resolved_inputs.fx_option_contract.strike,
        scalars.domestic_rate,
        scalars.foreign_rate,
        scalars.volatility,
        scalars.time_to_expiry_years,
    )


@dataclass(frozen=True)
class BlackScholesEuropeanFxEngineV1:
    """Pure PR-5 wrapper from resolved FX inputs to governed OptionValuationResultV1."""

    engine_name: str = ENGINE_NAME_V1
    engine_version: str = ENGINE_VERSION_V1
    model_name: str = MODEL_NAME_V1
    model_version: str = MODEL_VERSION_V1

    def value(self, resolved_inputs: ResolvedFxOptionValuationInputsV1) -> OptionValuationResultV1:
        engine_input = ensure_pure_option_pricing_input_v1(resolved_inputs)
        if not isinstance(engine_input, ResolvedFxOptionValuationInputsV1):
            raise ValueError("BlackScholesEuropeanFxEngineV1 requires ResolvedFxOptionValuationInputsV1")

        _require_non_empty_string(engine_input.resolved_basis_hash, "resolved_basis_hash")

        (
            option_type,
            spot,
            strike,
            domestic_rate,
            foreign_rate,
            volatility,
            time_to_expiry_years,
        ) = _extract_kernel_inputs_v1(engine_input)

        valuation_measures = black_scholes_fx_measures_v1(
            option_type=option_type,
            spot=spot,
            strike=strike,
            domestic_rate=domestic_rate,
            foreign_rate=foreign_rate,
            volatility=volatility,
            time_to_expiry_years=time_to_expiry_years,
        )

        return OptionValuationResultV1(
            engine_name=_require_non_empty_string(self.engine_name, "engine_name"),
            engine_version=_require_non_empty_string(self.engine_version, "engine_version"),
            model_name=_require_non_empty_string(self.model_name, "model_name"),
            model_version=_require_non_empty_string(self.model_version, "model_version"),
            resolved_input_contract_name=RESOLVED_INPUT_CONTRACT_NAME_V1,
            resolved_input_contract_version=RESOLVED_INPUT_CONTRACT_VERSION_V1,
            resolved_input_reference=engine_input.resolved_basis_hash,
            valuation_measures=valuation_measures,
        )


__all__ = [
    "BlackScholesEuropeanFxEngineV1",
    "ENGINE_NAME_V1",
    "ENGINE_VERSION_V1",
    "MODEL_NAME_V1",
    "MODEL_VERSION_V1",
    "RESOLVED_INPUT_CONTRACT_NAME_V1",
    "RESOLVED_INPUT_CONTRACT_VERSION_V1",
]
