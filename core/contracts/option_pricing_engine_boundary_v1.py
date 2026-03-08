from __future__ import annotations

from typing import TypeAlias

from core.contracts.option_valuation_dependency_bundle_v1 import OptionValuationDependencyBundleV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedOptionValuationInputsV1


PureOptionPricingInputV1: TypeAlias = (
    ResolvedOptionValuationInputsV1 | ResolvedFxOptionValuationInputsV1
)


def _looks_like_repository_or_loader_handle(value: object) -> bool:
    class_name = value.__class__.__name__.lower()
    if any(token in class_name for token in ("repository", "provider", "loader", "service")):
        return True

    for attr in ("get_by_id", "get_by_numeric_policy_id", "save", "list_by_valuation_run_id"):
        member = getattr(value, attr, None)
        if callable(member):
            return True

    return False


def ensure_pure_option_pricing_input_v1(value: object) -> PureOptionPricingInputV1:
    """Enforce that pricing engines only receive resolved immutable input contracts."""

    if isinstance(value, (ResolvedOptionValuationInputsV1, ResolvedFxOptionValuationInputsV1)):
        return value

    if isinstance(value, OptionValuationDependencyBundleV1):
        raise ValueError(
            "pricing engine input must be resolved inputs, not OptionValuationDependencyBundleV1"
        )

    if _looks_like_repository_or_loader_handle(value):
        raise ValueError("pricing engine input must not be a repository/provider/loader handle")

    raise ValueError(
        "pricing engine input must be ResolvedOptionValuationInputsV1 or "
        "ResolvedFxOptionValuationInputsV1"
    )


__all__ = [
    "PureOptionPricingInputV1",
    "ensure_pure_option_pricing_input_v1",
]
