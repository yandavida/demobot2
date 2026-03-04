"""Gate G9.3/G10.4: Deterministic repricing harness (FX forwards + EU options).

Pure structural repricing harness:
- Inputs: RiskRequest + validated market snapshot + ScenarioGrid
- Output: RiskResult (non-artifact, structural)

No pricing math is reimplemented here. Repricing calls the F8 SSOT forward
entrypoint through an explicit seam callable.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Mapping

from core.contracts.option_contract_v1 import OptionContractV1
from core.market_data.df_lookup_v0 import DfLookupError
from core.market_data.df_lookup_v0 import get_pair_dfs_v0
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.market_snapshot_payload_v0 import VolLookupError
from core.market_data.market_snapshot_payload_v0 import get_vol
from core.pricing.fx import forward_mtm
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext
from core.pricing.bs_ssot_v1 import TIME_FRACTION_POLICY_ACT_365F
from core.pricing.bs_ssot_v1 import price_european_option_bs_v1
from core.risk.risk_request import RiskRequest
from core.risk.risk_request import RiskValidationError
from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_grid import ScenarioKey
from core.risk.scenario_set import ScenarioSet
from core.vol.types import VolKey
from core.validation.error_taxonomy import make_error


SUPPORTED_SCHEMA_VERSION: int = 1


PriceForwardCallable = Callable[
    [fx_types.FXForwardContract, ValuationContext, fx_types.FxMarketSnapshot],
    fx_types.PricingResult,
]


def _reject(code: str, details: dict[str, str]) -> None:
    raise RiskValidationError(make_error(code, details))


def _default_price_forward(
    contract: fx_types.FXForwardContract,
    valuation_context,
    market_snapshot: fx_types.FxMarketSnapshot,
) -> fx_types.PricingResult:
    return forward_mtm.price_fx_forward_ctx(
        context=valuation_context,
        contract=contract,
        market_snapshot=market_snapshot,
        conventions=None,
    )


def _to_decimal(value: float) -> Decimal:
    return Decimal(str(value))


def _compute_ttm_years_act_365f(*, as_of_ts: datetime.datetime, expiry: datetime.datetime) -> float:
    if as_of_ts.tzinfo is None:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "valuation_context.as_of_ts",
                "reason": "must be timezone-aware",
            },
        )
    if expiry.tzinfo is None:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "option_contract.expiry",
                "reason": "must be timezone-aware",
            },
        )

    delta_seconds = (expiry - as_of_ts).total_seconds()
    ttm_years = delta_seconds / (365.0 * 24.0 * 60.0 * 60.0)
    if ttm_years < 0.0:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "option_contract.expiry",
                "reason": "must be >= valuation_context.as_of_ts",
            },
        )
    return ttm_years


def _apply_shock_snapshot(
    base_snapshot: fx_types.FxMarketSnapshot,
    scenario: ScenarioKey,
) -> fx_types.FxMarketSnapshot:
    if base_snapshot.df_domestic is None or base_snapshot.df_foreign is None:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "base_snapshot.df",
                "reason": "df_domestic and df_foreign are required for FX forward repricing",
            },
        )

    base_spot = _to_decimal(base_snapshot.spot_rate)
    base_df_d = _to_decimal(base_snapshot.df_domestic)
    base_df_f = _to_decimal(base_snapshot.df_foreign)

    factor_spot = Decimal("1") + scenario.spot_shock
    factor_df_d = Decimal("1") + scenario.df_domestic_shock
    factor_df_f = Decimal("1") + scenario.df_foreign_shock

    if factor_spot <= 0:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "spot_shock",
                "reason": "(1 + spot_shock) must be > 0",
            },
        )
    if factor_df_d <= 0:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "df_domestic_shock",
                "reason": "(1 + df_domestic_shock) must be > 0",
            },
        )
    if factor_df_f <= 0:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "df_foreign_shock",
                "reason": "(1 + df_foreign_shock) must be > 0",
            },
        )

    shocked_spot = base_spot * factor_spot
    shocked_df_d = base_df_d * factor_df_d
    shocked_df_f = base_df_f * factor_df_f

    if shocked_df_d <= 0:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "df_domestic",
                "reason": "shocked df_domestic must be > 0",
            },
        )
    if shocked_df_f <= 0:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "df_foreign",
                "reason": "shocked df_foreign must be > 0",
            },
        )

    return fx_types.FxMarketSnapshot(
        as_of_ts=base_snapshot.as_of_ts,
        spot_rate=float(shocked_spot),
        conventions=base_snapshot.conventions,
        df_domestic=float(shocked_df_d),
        df_foreign=float(shocked_df_f),
        domestic_currency=base_snapshot.domestic_currency,
    )


@dataclass(frozen=True)
class InstrumentScenarioPV:
    instrument_id: str
    scenario_id: str
    pv_domestic: Decimal
    currency: str
    metric_class: str


@dataclass(frozen=True)
class InstrumentRiskCube:
    instrument_id: str
    base_pv: Decimal
    scenario_pvs: tuple[InstrumentScenarioPV, ...]


@dataclass(frozen=True)
class RiskResult:
    schema_version: int
    market_snapshot_id: str
    scenario_set_id: str
    results: tuple[InstrumentRiskCube, ...]


def reprice_fx_forward_risk(
    request: RiskRequest,
    base_snapshot: fx_types.FxMarketSnapshot,
    scenario_grid: ScenarioGrid,
    contracts_by_instrument_id: Mapping[str, object],
    *,
    price_forward: PriceForwardCallable | None = None,
    market_snapshot_payload: MarketSnapshotPayloadV0 | None = None,
    schema_version: int = SUPPORTED_SCHEMA_VERSION,
) -> RiskResult:
    if schema_version is None:
        _reject("MISSING_SCHEMA_VERSION", {"field": "schema_version"})
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        _reject(
            "UNSUPPORTED_SCHEMA_VERSION",
            {
                "given": str(schema_version),
                "supported": str(SUPPORTED_SCHEMA_VERSION),
            },
        )

    expected_set_id = ScenarioSet.from_spec(request.scenario_spec).scenario_set_id
    if scenario_grid.scenario_set_id != expected_set_id:
        _reject(
            "VALIDATION_ERROR",
            {
                "field": "scenario_set_id",
                "reason": "scenario_grid.scenario_set_id must match request.scenario_spec",
            },
        )

    run_price_forward = price_forward or _default_price_forward

    cubes: list[InstrumentRiskCube] = []
    for instrument_id in request.instrument_ids:
        contract = contracts_by_instrument_id.get(instrument_id)
        if contract is None:
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "contracts_by_instrument_id",
                    "reason": f"missing contract for instrument_id={instrument_id}",
                },
            )

        scenario_pvs: list[InstrumentScenarioPV] = []

        if isinstance(contract, fx_types.FXForwardContract):
            if base_snapshot.df_domestic is None or base_snapshot.df_foreign is None:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "base_snapshot.df",
                        "reason": "df_domestic and df_foreign are required",
                    },
                )
            if base_snapshot.df_domestic <= 0:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "base_snapshot.df_domestic",
                        "reason": "must be > 0",
                    },
                )
            if base_snapshot.df_foreign <= 0:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "base_snapshot.df_foreign",
                        "reason": "must be > 0",
                    },
                )

            base_result = run_price_forward(contract, request.valuation_context, base_snapshot)
            if base_result.currency != request.valuation_context.domestic_currency:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "currency",
                        "reason": "pricing currency must equal valuation_context.domestic_currency",
                    },
                )
            if base_result.metric_class is None:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "metric_class",
                        "reason": "metric_class must be explicit",
                    },
                )
            base_pv = _to_decimal(base_result.pv)
            out_currency = base_result.currency
            out_metric = base_result.metric_class.value

            for scenario_key, scenario_id in zip(scenario_grid.scenarios, scenario_grid.scenario_ids):
                shocked_snapshot = _apply_shock_snapshot(base_snapshot, scenario_key)
                priced = run_price_forward(contract, request.valuation_context, shocked_snapshot)

                if priced.currency != request.valuation_context.domestic_currency:
                    _reject(
                        "VALIDATION_ERROR",
                        {
                            "field": "currency",
                            "reason": "pricing currency must equal valuation_context.domestic_currency",
                        },
                    )
                if priced.metric_class is None:
                    _reject(
                        "VALIDATION_ERROR",
                        {
                            "field": "metric_class",
                            "reason": "metric_class must be explicit",
                        },
                    )

                scenario_pvs.append(
                    InstrumentScenarioPV(
                        instrument_id=instrument_id,
                        scenario_id=scenario_id,
                        pv_domestic=_to_decimal(priced.pv),
                        currency=priced.currency,
                        metric_class=priced.metric_class.value,
                    )
                )

        elif isinstance(contract, OptionContractV1):
            if market_snapshot_payload is None:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "market_snapshot_payload",
                        "reason": "required when pricing OptionContractV1",
                    },
                )

            if contract.time_fraction_policy_id != TIME_FRACTION_POLICY_ACT_365F:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "time_fraction_policy_id",
                        "reason": f"must be {TIME_FRACTION_POLICY_ACT_365F}",
                    },
                )

            if contract.domestic_ccy != request.valuation_context.domestic_currency:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "domestic_ccy",
                        "reason": "must equal valuation_context.domestic_currency",
                    },
                )

            if contract.underlying not in market_snapshot_payload.spots.prices:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "spots.prices",
                        "reason": f"missing spot for underlying={contract.underlying}",
                    },
                )

            base_spot_dec = Decimal(str(market_snapshot_payload.spots.prices[contract.underlying]))
            ttm_years = _compute_ttm_years_act_365f(
                as_of_ts=request.valuation_context.as_of_ts,
                expiry=contract.expiry,
            )

            try:
                base_df_dom, base_df_for = get_pair_dfs_v0(
                    market_snapshot_payload,
                    domestic_ccy=contract.domestic_ccy,
                    foreign_ccy=contract.foreign_ccy,
                    ttm_years=ttm_years,
                )
            except DfLookupError as exc:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "df_lookup",
                        "reason": str(exc),
                    },
                )

            try:
                option_vol = get_vol(
                    market_snapshot_payload,
                    VolKey(
                        underlying=contract.underlying,
                        expiry_t=ttm_years,
                        strike=float(contract.strike),
                        option_type=contract.option_type,
                    ),
                )
            except VolLookupError as exc:
                _reject(
                    "VALIDATION_ERROR",
                    {
                        "field": "vol_lookup",
                        "reason": str(exc),
                    },
                )

            base_priced = price_european_option_bs_v1(
                spot=float(base_spot_dec),
                strike=float(contract.strike),
                domestic_df=base_df_dom,
                foreign_df=base_df_for,
                vol=float(option_vol),
                ttm_years=ttm_years,
                option_type=contract.option_type,
                notional=float(contract.notional),
                time_fraction_policy_id=contract.time_fraction_policy_id,
            )
            base_pv = _to_decimal(base_priced.pv_domestic)
            out_currency = request.valuation_context.domestic_currency
            out_metric = "PRICE"

            for scenario_key, scenario_id in zip(scenario_grid.scenarios, scenario_grid.scenario_ids):
                spot_factor = Decimal("1") + scenario_key.spot_shock
                dom_factor = Decimal("1") + scenario_key.df_domestic_shock
                for_factor = Decimal("1") + scenario_key.df_foreign_shock
                if spot_factor <= 0:
                    _reject(
                        "VALIDATION_ERROR",
                        {
                            "field": "spot_shock",
                            "reason": "(1 + spot_shock) must be > 0",
                        },
                    )
                if dom_factor <= 0:
                    _reject(
                        "VALIDATION_ERROR",
                        {
                            "field": "df_domestic_shock",
                            "reason": "(1 + df_domestic_shock) must be > 0",
                        },
                    )
                if for_factor <= 0:
                    _reject(
                        "VALIDATION_ERROR",
                        {
                            "field": "df_foreign_shock",
                            "reason": "(1 + df_foreign_shock) must be > 0",
                        },
                    )

                shocked_spot = base_spot_dec * spot_factor
                shocked_df_dom = Decimal(str(base_df_dom)) * dom_factor
                shocked_df_for = Decimal(str(base_df_for)) * for_factor

                priced = price_european_option_bs_v1(
                    spot=float(shocked_spot),
                    strike=float(contract.strike),
                    domestic_df=float(shocked_df_dom),
                    foreign_df=float(shocked_df_for),
                    vol=float(option_vol),
                    ttm_years=ttm_years,
                    option_type=contract.option_type,
                    notional=float(contract.notional),
                    time_fraction_policy_id=contract.time_fraction_policy_id,
                )

                scenario_pvs.append(
                    InstrumentScenarioPV(
                        instrument_id=instrument_id,
                        scenario_id=scenario_id,
                        pv_domestic=_to_decimal(priced.pv_domestic),
                        currency=out_currency,
                        metric_class=out_metric,
                    )
                )

        else:
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "contracts_by_instrument_id",
                    "reason": f"unsupported contract type for instrument_id={instrument_id}",
                },
            )

        if len(scenario_pvs) != len(scenario_grid.scenarios):
            _reject(
                "VALIDATION_ERROR",
                {
                    "field": "scenario_pvs",
                    "reason": "scenario_pvs length must equal scenario grid length",
                },
            )

        cubes.append(
            InstrumentRiskCube(
                instrument_id=instrument_id,
                base_pv=base_pv,
                scenario_pvs=tuple(scenario_pvs),
            )
        )

    return RiskResult(
        schema_version=schema_version,
        market_snapshot_id=request.market_snapshot_id,
        scenario_set_id=scenario_grid.scenario_set_id,
        results=tuple(cubes),
    )


__all__ = [
    "InstrumentRiskCube",
    "InstrumentScenarioPV",
    "PriceForwardCallable",
    "RiskResult",
    "SUPPORTED_SCHEMA_VERSION",
    "reprice_fx_forward_risk",
]
