from __future__ import annotations

from decimal import Decimal

from core.pricing.fx.types import FXForwardContract
from core.pricing.fx.types import FxMarketSnapshot
from core.pricing.fx.valuation_context import ValuationContext
from core.risk.portfolio_surface import compute_portfolio_surface_v1
from core.risk.reprice_harness import reprice_fx_forward_risk
from core.risk.risk_artifact import build_risk_artifact_v1
from core.risk.risk_request import RiskRequest
from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import ScenarioSpec
from core.services.advisory_input_contract_v1 import AdvisoryInputNormalizedV1
from core.services.advisory_input_contract_v1 import normalize_advisory_input_v1
from core.services.advisory_output_contract_v1 import AdvisoryDecisionV1
from core.services.exposure_adapter_v1 import build_risk_request_from_advisory_v1
from core.services.hedge_recommendation_v1 import recommend_hedge_ratio_v1
from core.services.scenario_risk_summary_v1 import summarize_scenario_risk_v1


def _current_hedge_ratio(normalized_input: AdvisoryInputNormalizedV1) -> float:
    total_notional = Decimal("0")
    hedged_notional = Decimal("0")

    for row in normalized_input.exposures:
        total_notional += row.notional
        hedged_notional += row.notional * (row.hedge_ratio if row.hedge_ratio is not None else Decimal("0"))

    if total_notional <= 0:
        return 0.0
    return float(hedged_notional / total_notional)


def _pricing_ready_contracts(
    *,
    contracts_raw: dict[str, FXForwardContract],
    base_snapshot: FxMarketSnapshot,
) -> dict[str, FXForwardContract]:
    if base_snapshot.df_domestic is None or base_snapshot.df_foreign is None:
        raise ValueError("base_snapshot must include df_domestic and df_foreign")

    forward_rate = base_snapshot.spot_rate * base_snapshot.df_foreign / base_snapshot.df_domestic

    out: dict[str, FXForwardContract] = {}
    for instrument_id, contract in contracts_raw.items():
        out[instrument_id] = FXForwardContract(
            base_currency=contract.base_currency,
            quote_currency=contract.quote_currency,
            notional=contract.notional,
            forward_date=contract.forward_date,
            forward_rate=forward_rate,
            direction=contract.direction,
        )
    return out


def run_treasury_advisory_v1(
    payload: dict,
    *,
    base_snapshot: FxMarketSnapshot,
    scenario_spec: ScenarioSpec,
    target_worst_loss_domestic: float,
) -> AdvisoryDecisionV1:
    normalized_input = normalize_advisory_input_v1(payload)
    contracts_raw, risk_request_payload = build_risk_request_from_advisory_v1(normalized_input)
    contracts = _pricing_ready_contracts(contracts_raw=contracts_raw, base_snapshot=base_snapshot)

    scenario_grid = ScenarioGrid.from_scenario_set(ScenarioSet.from_spec(scenario_spec))

    valuation_context = ValuationContext(
        as_of_ts=base_snapshot.as_of_ts,
        domestic_currency=risk_request_payload["valuation_context"]["domestic_currency"],
        strict_mode=True,
    )
    risk_request = RiskRequest(
        schema_version=1,
        valuation_context=valuation_context,
        market_snapshot_id=risk_request_payload["snapshot_id"],
        instrument_ids=risk_request_payload["instrument_ids"],
        scenario_spec=scenario_spec,
        strict=True,
    )

    risk_result = reprice_fx_forward_risk(
        request=risk_request,
        base_snapshot=base_snapshot,
        scenario_grid=scenario_grid,
        contracts_by_instrument_id=contracts,
    )
    risk_artifact = build_risk_artifact_v1(risk_request, scenario_grid, risk_result)
    portfolio_surface_artifact = compute_portfolio_surface_v1(risk_artifact)

    risk_summary = summarize_scenario_risk_v1(
        risk_artifact=risk_artifact,
        portfolio_surface_artifact=portfolio_surface_artifact,
    )
    hedge_recommendation = recommend_hedge_ratio_v1(
        risk_summary,
        current_hedge_ratio=_current_hedge_ratio(normalized_input),
        target_worst_loss_domestic=target_worst_loss_domestic,
    )

    return AdvisoryDecisionV1(
        company_id=normalized_input.company_id,
        snapshot_id=normalized_input.snapshot_id,
        scenario_template_id=normalized_input.scenario_template_id,
        risk_summary=risk_summary,
        hedge_recommendation=hedge_recommendation,
        delta_exposure_aggregate_domestic=None,
        notes=("DELTA_NOT_AVAILABLE",),
    )


__all__ = ["run_treasury_advisory_v1"]
