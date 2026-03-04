from __future__ import annotations

import datetime
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest

from core.contracts.option_contract_v1 import OptionContractV1
from core.market_data.market_snapshot_payload_v0 import Curve
from core.market_data.market_snapshot_payload_v0 import FxRates
from core.market_data.market_snapshot_payload_v0 import InterestRateCurves
from core.market_data.market_snapshot_payload_v0 import MarketConventions
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.market_snapshot_payload_v0 import SpotPrices
from core.market_data.market_snapshot_payload_v0 import VolSurface
from core.market_data.market_snapshot_payload_v0 import VolSurfaces
from core.market_data.market_snapshot_payload_v0 import make_vol_lookup_key
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext
from core.risk.exposures import compute_exposures_v1
from core.risk.portfolio_surface import compute_portfolio_surface_v1
from core.risk.reprice_harness import RiskValidationError
from core.risk.reprice_harness import reprice_fx_forward_risk
from core.risk.risk_artifact import build_risk_artifact_v1
from core.risk.risk_request import RiskRequest
from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import ScenarioSpec
from core.vol.types import VolKey


DATA_DIR = Path("tests/core/risk/_data")
RISK_FIXTURE = DATA_DIR / "g10_options_risk_artifact_v1_fixture.json"
EXPOSURES_FIXTURE = DATA_DIR / "g10_options_exposures_v1_fixture.json"
SURFACE_FIXTURE = DATA_DIR / "g10_options_portfolio_surface_v1_fixture.json"

PINNED_RISK_ARTIFACT_SHA = "52373ee9c82b42dbbc9cfffe5d7a733507e6e8d04050f4d6e2c2c8470cbad778"
PINNED_EXPOSURES_ARTIFACT_SHA = "147fedc63267dd4b28d086c022873e640560a385768b4decc88ac0d2bef92bad"
PINNED_SURFACE_ARTIFACT_SHA = "01f1e444c873b0717f540df5cf6fe8058a4881a69847731ba7729861ef008bf9"


def _canonical_sha_without_sha(obj: dict) -> str:
    body = {k: v for k, v in obj.items() if k != "sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _context() -> ValuationContext:
    return ValuationContext(
        as_of_ts=datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc),
        domestic_currency="USD",
        strict_mode=True,
    )


def _spec() -> ScenarioSpec:
    return ScenarioSpec(
        schema_version=1,
        spot_shocks=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        df_domestic_shocks=(Decimal("0.00"),),
        df_foreign_shocks=(Decimal("0.00"),),
    )


def _request() -> RiskRequest:
    return RiskRequest(
        schema_version=1,
        valuation_context=_context(),
        market_snapshot_id="snap-g10-options-001",
        instrument_ids=("opt_call", "opt_put"),
        scenario_spec=_spec(),
        strict=True,
    )


def _grid() -> ScenarioGrid:
    return ScenarioGrid.from_scenario_set(ScenarioSet.from_spec(_spec()))


def _market_payload(*, include_put_vol: bool = True) -> MarketSnapshotPayloadV0:
    ttm_years = 1.0
    call_key = make_vol_lookup_key(VolKey(underlying="AAPL", expiry_t=ttm_years, strike=100.0, option_type="call"))
    put_key = make_vol_lookup_key(VolKey(underlying="AAPL", expiry_t=ttm_years, strike=100.0, option_type="put"))

    quotes = {call_key: 0.20}
    if include_put_vol:
        quotes[put_key] = 0.22

    return MarketSnapshotPayloadV0(
        fx_rates=FxRates(base_ccy="USD", quotes={"USD/USD": 1.0, "USD/EUR": 0.92, "EUR/USD": 1 / 0.92}),
        spots=SpotPrices(prices={"AAPL": 100.0}, currency={"AAPL": "USD"}),
        curves=InterestRateCurves(
            curves={
                "USD": Curve(day_count="ACT/365", compounding="continuous", zero_rates={"365D": 0.02}),
                "EUR": Curve(day_count="ACT/365", compounding="continuous", zero_rates={"365D": 0.01}),
            }
        ),
        vols=VolSurfaces(
            surfaces={
                "OPTIONS": VolSurface(type="flat", data={"quotes": quotes}),
            }
        ),
        conventions=MarketConventions(calendar="NONE", day_count_default="ACT/365", spot_lag=2),
    )


def _contracts() -> dict[str, OptionContractV1]:
    expiry = datetime.datetime(2027, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    return {
        "opt_call": OptionContractV1(
            instrument_id="opt_call",
            underlying="AAPL",
            option_type="call",
            strike=Decimal("100"),
            expiry=expiry,
            notional=Decimal("1000"),
            domestic_ccy="USD",
            foreign_ccy="EUR",
            time_fraction_policy_id="ACT_365F",
            contract_version="v1",
        ),
        "opt_put": OptionContractV1(
            instrument_id="opt_put",
            underlying="AAPL",
            option_type="put",
            strike=Decimal("100"),
            expiry=expiry,
            notional=Decimal("1000"),
            domestic_ccy="USD",
            foreign_ccy="EUR",
            time_fraction_policy_id="ACT_365F",
            contract_version="v1",
        ),
    }


def _base_snapshot() -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=_context().as_of_ts,
        spot_rate=1.0,
        df_domestic=1.0,
        df_foreign=1.0,
        domestic_currency="USD",
    )


def _build_artifacts(*, include_put_vol: bool = True) -> tuple[dict, dict, dict]:
    request = _request()
    grid = _grid()
    risk_result = reprice_fx_forward_risk(
        request,
        _base_snapshot(),
        grid,
        _contracts(),
        market_snapshot_payload=_market_payload(include_put_vol=include_put_vol),
    )
    risk = build_risk_artifact_v1(request, grid, risk_result)
    exposures = compute_exposures_v1(risk, base_spot=Decimal("100.0"))
    surface = compute_portfolio_surface_v1(risk)
    return risk, exposures, surface


def test_t1_options_flow_produces_deterministic_artifacts() -> None:
    risk_a, exposures_a, surface_a = _build_artifacts()
    risk_b, exposures_b, surface_b = _build_artifacts()

    assert risk_a == risk_b
    assert exposures_a == exposures_b
    assert surface_a == surface_b

    assert risk_a["schema"]["name"] == "pe.g9.risk_artifact"
    assert exposures_a["schema"]["name"] == "pe.g9.exposures_artifact"
    assert surface_a["schema"]["name"] == "pe.g9.portfolio_surface_artifact"


def test_t2_new_g10_fixtures_are_hash_pinned() -> None:
    risk_fixture = json.loads(RISK_FIXTURE.read_text(encoding="utf-8"))
    exposures_fixture = json.loads(EXPOSURES_FIXTURE.read_text(encoding="utf-8"))
    surface_fixture = json.loads(SURFACE_FIXTURE.read_text(encoding="utf-8"))

    assert _canonical_sha_without_sha(risk_fixture) == risk_fixture["sha256"]
    assert _canonical_sha_without_sha(exposures_fixture) == exposures_fixture["sha256"]
    assert _canonical_sha_without_sha(surface_fixture) == surface_fixture["sha256"]

    assert risk_fixture["sha256"] == PINNED_RISK_ARTIFACT_SHA
    assert exposures_fixture["sha256"] == PINNED_EXPOSURES_ARTIFACT_SHA
    assert surface_fixture["sha256"] == PINNED_SURFACE_ARTIFACT_SHA

    built_risk, built_exposures, built_surface = _build_artifacts()
    assert built_risk == risk_fixture
    assert built_exposures == exposures_fixture
    assert built_surface == surface_fixture


def test_t3_missing_required_vol_fails_explicitly() -> None:
    with pytest.raises(RiskValidationError) as exc:
        _build_artifacts(include_put_vol=False)

    details = getattr(exc.value.envelope, "details", {})
    assert details.get("field") == "vol_lookup"
    assert "vol" in str(details.get("reason", "")).lower()


def test_t4_fd_delta_sign_sanity_for_call_leg() -> None:
    _, exposures_artifact, _ = _build_artifacts()
    rows = {
        row["instrument_id"]: Decimal(row["delta_per_pct"])
        for row in exposures_artifact["outputs"]["per_instrument"]
    }
    assert rows["opt_call"] > Decimal("0")
