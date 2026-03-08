from __future__ import annotations

import datetime
import inspect

from core.contracts.model_registry import ModelCapability
from core.contracts.model_registry import ModelRegistryEntry
from core.contracts.reference_data_set import ReferenceDataSet
from core.contracts.valuation_policy_set import ValuationPolicySet
from core.contracts.valuation_run import ValuationRun
from core.market_data.market_snapshot_payload_v0 import Curve
from core.market_data.market_snapshot_payload_v0 import FxRates
from core.market_data.market_snapshot_payload_v0 import InterestRateCurves
from core.market_data.market_snapshot_payload_v0 import MarketConventions
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.market_snapshot_payload_v0 import SpotPrices
from core.persistence.repositories import ArtifactRecord
from core.persistence.repositories import ArtifactRepository
from core.persistence.repositories import MarketSnapshotRepository
from core.persistence.repositories import ModelRegistryRepository
from core.persistence.repositories import ReferenceDataSetRepository
from core.persistence.repositories import ValuationPolicySetRepository
from core.persistence.repositories import ValuationRunRepository


def _snapshot() -> MarketSnapshotPayloadV0:
    return MarketSnapshotPayloadV0(
        fx_rates=FxRates(base_ccy="USD", quotes={"ILS": 3.67}),
        spots=SpotPrices(prices={"USDILS": 3.67}, currency={"USDILS": "ILS"}),
        curves=InterestRateCurves(
            curves={
                "USD": Curve(
                    day_count="ACT_365F",
                    compounding="continuous",
                    zero_rates={"1Y": 0.05},
                )
            }
        ),
        conventions=MarketConventions(calendar="TARGET", day_count_default="ACT_365F", spot_lag=2),
    )


def _reference_data_set() -> ReferenceDataSet:
    return ReferenceDataSet(
        calendar_version="cal-v2026-01",
        holiday_calendar_refs=("cal.us.nyfed",),
        day_count_convention_refs=("dcc.ACT_365F",),
        business_day_adjustment_refs=("bda.MOD_FOLLOWING",),
        settlement_convention_refs=("set.fx.spot_t2",),
        fixing_source_refs=("fix.wm_reuters_16",),
        exercise_convention_refs=("ex.european.at_expiry",),
        taxonomy_mapping_refs=("tax.fxopt.g10",),
        reference_data_version_id="refdata-2026-01-31",
    )


def _valuation_policy_set() -> ValuationPolicySet:
    return ValuationPolicySet(
        valuation_policy_id="vps-fx-options-core",
        model_family="black_scholes_crr",
        pricing_engine_policy="engine.policy.v1",
        numeric_policy_id="numeric.policy.v1",
        tolerance_policy_id="tol.policy.v1",
        calibration_recipe_id="cal.recipe.v1",
        approval_status="approved",
        policy_version="v1",
        policy_owner="treasury_risk_committee",
        created_timestamp=datetime.datetime(2026, 3, 8, 12, 0, 0, tzinfo=datetime.timezone.utc),
    )


def _valuation_run() -> ValuationRun:
    return ValuationRun(
        valuation_run_id="vr-2026-03-08-001",
        portfolio_state_id="ps-2026-03-08-001",
        market_snapshot_id="ms-2026-03-08-001",
        reference_data_set_id="rds-2026-03-08-001",
        valuation_policy_set_id="vps-2026-03-08-001",
        valuation_context_id="vc-2026-03-08-001",
        scenario_set_id="scn-2026-03-08-001",
        software_build_hash="build-abc123def",
        run_timestamp=datetime.datetime(2026, 3, 8, 12, 0, 0, tzinfo=datetime.timezone.utc),
        valuation_timestamp=datetime.datetime(2026, 3, 8, 11, 59, 0, tzinfo=datetime.timezone.utc),
        run_purpose="risk_snapshot",
    )


def _model_entry() -> ModelRegistryEntry:
    return ModelRegistryEntry(
        model_id="model.fx.bs.v1",
        semantic_version="1.0.0",
        implementation_version="impl-2026-03-08",
        validation_status="approved",
        owner="treasury_model_risk",
        approval_date=datetime.date(2026, 3, 8),
        benchmark_pack_id="bench.fx.options.v1",
        known_limitations=("european-only",),
        numeric_policy_id="numeric.policy.v1",
        supported_capabilities=(
            ModelCapability(
                instrument_family="fx_option_vanilla",
                exercise_style="european",
                measure="pv",
            ),
        ),
    )


def test_repository_protocols_define_expected_method_surface() -> None:
    expected_methods = {
        MarketSnapshotRepository: {"get_by_id", "save"},
        ReferenceDataSetRepository: {"get_by_id", "save"},
        ValuationPolicySetRepository: {"get_by_id", "save"},
        ValuationRunRepository: {"get_by_id", "save"},
        ArtifactRepository: {"get_by_id", "save", "list_by_valuation_run_id"},
        ModelRegistryRepository: {"get_by_model_id", "save"},
    }

    for protocol_cls, expected in expected_methods.items():
        names = {
            name
            for name, value in protocol_cls.__dict__.items()
            if callable(value) and not name.startswith("_")
        }
        assert expected.issubset(names)


def test_repository_protocol_signatures_do_not_leak_storage_terms() -> None:
    forbidden_tokens = ("sql", "table", "row", "cursor", "query", "schema")

    for protocol_cls in (
        MarketSnapshotRepository,
        ReferenceDataSetRepository,
        ValuationPolicySetRepository,
        ValuationRunRepository,
        ArtifactRepository,
        ModelRegistryRepository,
    ):
        for method_name, method in protocol_cls.__dict__.items():
            if not callable(method) or method_name.startswith("_"):
                continue
            signature = inspect.signature(method)
            for param_name in signature.parameters:
                assert not any(token in param_name.lower() for token in forbidden_tokens)


def test_runtime_checkable_protocols_accept_structural_implementations() -> None:
    class DemoRepo:
        def __init__(self) -> None:
            self._snapshot = _snapshot()
            self._reference_data = _reference_data_set()
            self._policy = _valuation_policy_set()
            self._run = _valuation_run()
            self._artifact = ArtifactRecord(
                artifact_id="artifact-001",
                valuation_run_id="vr-2026-03-08-001",
                artifact_type="risk_artifact",
                content_hash="sha256:abc123",
                payload_json='{"schema":"v1"}',
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
            self._model_entry = _model_entry()

        def get_by_id(self, _id: str):
            return self._snapshot

        def save(self, *_args):
            return None

        def list_by_valuation_run_id(self, _valuation_run_id: str) -> tuple[ArtifactRecord, ...]:
            return (self._artifact,)

        def get_by_model_id(self, _model_id: str) -> ModelRegistryEntry:
            return self._model_entry

    demo = DemoRepo()

    assert isinstance(demo, MarketSnapshotRepository)
    assert isinstance(demo, ReferenceDataSetRepository)
    assert isinstance(demo, ValuationPolicySetRepository)
    assert isinstance(demo, ValuationRunRepository)
    assert isinstance(demo, ArtifactRepository)
    assert isinstance(demo, ModelRegistryRepository)
