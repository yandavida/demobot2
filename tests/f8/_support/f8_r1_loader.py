from __future__ import annotations

from dataclasses import dataclass
import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any

from core import numeric_policy
from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext


@dataclass(frozen=True)
class ForwardExternalCase:
    case_id: str
    artifact: dict[str, Any]
    context: ValuationContext
    contract: fx_types.FXForwardContract
    market_snapshot: fx_types.FxMarketSnapshot
    expected_pv: float
    expected_currency: str
    expected_metric_class: numeric_policy.MetricClass
    expected_metric_class_raw: str
    tolerance_abs: float
    sha256: str


def canonical_sha256(obj: Any) -> str:
    canonical_json = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _to_float(value: str, field_name: str) -> float:
    try:
        parsed = float(Decimal(value))
    except Exception as exc:
        raise ValueError(f"{field_name} must be a valid numeric string") from exc
    return parsed


def _required(mapping: dict[str, Any], key: str, parent: str) -> Any:
    if key not in mapping:
        raise ValueError(f"missing required field: {parent}.{key}")
    return mapping[key]


def _parse_metric_class(raw: str) -> numeric_policy.MetricClass:
    if raw != "MTM":
        raise ValueError("expected.metric_class must be MTM")
    return numeric_policy.MetricClass.PRICE


def load_external_forward_cases(dataset_path: Path) -> tuple[ForwardExternalCase, ...]:
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("dataset must be a list of cases")

    cases: list[ForwardExternalCase] = []
    for entry in payload:
        case_id = _required(entry, "case_id", "case")
        artifact = _required(entry, "artifact", case_id)
        expected = _required(entry, "expected", case_id)
        tolerance = _required(entry, "tolerance", case_id)
        sha256_value = _required(entry, "sha256", case_id)

        valuation_context = _required(artifact, "valuation_context", f"{case_id}.artifact")
        contract_payload = _required(artifact, "contract", f"{case_id}.artifact")
        snapshot_payload = _required(artifact, "market_snapshot", f"{case_id}.artifact")

        as_of_ts = datetime.datetime.fromisoformat(
            _required(valuation_context, "as_of_ts", f"{case_id}.artifact.valuation_context")
        )
        if as_of_ts.tzinfo is None:
            raise ValueError("artifact.valuation_context.as_of_ts must be timezone-aware")

        domestic_currency = _required(
            valuation_context,
            "domestic_currency",
            f"{case_id}.artifact.valuation_context",
        )
        if not isinstance(domestic_currency, str) or domestic_currency.strip() == "":
            raise ValueError("artifact.valuation_context.domestic_currency must be non-empty")

        pair = _required(contract_payload, "pair", f"{case_id}.artifact.contract")
        if not isinstance(pair, str) or "/" not in pair:
            raise ValueError("artifact.contract.pair must be in BASE/QUOTE format")
        base_currency, quote_currency = pair.split("/", 1)

        contract = fx_types.FXForwardContract(
            base_currency=base_currency,
            quote_currency=quote_currency,
            notional=_to_float(
                _required(contract_payload, "notional_foreign", f"{case_id}.artifact.contract"),
                "artifact.contract.notional_foreign",
            ),
            forward_date=datetime.date.fromisoformat(
                _required(contract_payload, "settlement_date", f"{case_id}.artifact.contract")
            ),
            forward_rate=_to_float(
                _required(contract_payload, "strike", f"{case_id}.artifact.contract"),
                "artifact.contract.strike",
            ),
            direction=_required(contract_payload, "direction", f"{case_id}.artifact.contract"),
        )

        market_snapshot = fx_types.FxMarketSnapshot(
            as_of_ts=as_of_ts,
            spot_rate=_to_float(
                _required(snapshot_payload, "spot", f"{case_id}.artifact.market_snapshot"),
                "artifact.market_snapshot.spot",
            ),
            df_domestic=_to_float(
                _required(snapshot_payload, "df_domestic", f"{case_id}.artifact.market_snapshot"),
                "artifact.market_snapshot.df_domestic",
            ),
            df_foreign=_to_float(
                _required(snapshot_payload, "df_foreign", f"{case_id}.artifact.market_snapshot"),
                "artifact.market_snapshot.df_foreign",
            ),
        )

        context = ValuationContext(as_of_ts=as_of_ts, domestic_currency=domestic_currency)

        expected_metric_class_raw = _required(expected, "metric_class", f"{case_id}.expected")
        expected_metric_class = _parse_metric_class(expected_metric_class_raw)

        case = ForwardExternalCase(
            case_id=case_id,
            artifact=artifact,
            context=context,
            contract=contract,
            market_snapshot=market_snapshot,
            expected_pv=_to_float(
                _required(expected, "pv_domestic", f"{case_id}.expected"),
                "expected.pv_domestic",
            ),
            expected_currency=_required(expected, "currency", f"{case_id}.expected"),
            expected_metric_class=expected_metric_class,
            expected_metric_class_raw=expected_metric_class_raw,
            tolerance_abs=_to_float(
                _required(tolerance, "abs", f"{case_id}.tolerance"),
                "tolerance.abs",
            ),
            sha256=sha256_value,
        )
        cases.append(case)

    return tuple(cases)
