from __future__ import annotations

from dataclasses import dataclass
import datetime
from decimal import Decimal
from decimal import InvalidOperation
import hashlib
import json
import re
from typing import Any


SUPPORTED_CONTRACT_VERSION = "v1"
ALLOWED_DIRECTIONS = {"receivable", "payable"}
PAIR_RE = re.compile(r"^[A-Z]{3}/[A-Z]{3}$")


class AdvisoryInputValidationError(ValueError):
    pass


def _to_decimal(value: Any, *, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise AdvisoryInputValidationError(f"{field} must be a valid decimal") from exc
    if not parsed.is_finite():
        raise AdvisoryInputValidationError(f"{field} must be finite")
    return parsed


def _parse_date(value: Any, *, field: str) -> datetime.date:
    if not isinstance(value, str) or not value:
        raise AdvisoryInputValidationError(f"{field} is required")
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise AdvisoryInputValidationError(f"{field} must be YYYY-MM-DD") from exc


@dataclass(frozen=True)
class AdvisoryExposureRowV1:
    row_id: str
    currency_pair: str
    direction: str
    notional: Decimal
    maturity_date: datetime.date
    hedge_ratio: Decimal | None


@dataclass(frozen=True)
class AdvisoryInputNormalizedV1:
    contract_version: str
    company_id: str
    snapshot_id: str
    scenario_template_id: str
    exposures: tuple[AdvisoryExposureRowV1, ...]


def _stable_row_id(
    *,
    currency_pair: str,
    direction: str,
    notional: Decimal,
    maturity_date: datetime.date,
    hedge_ratio: Decimal | None,
) -> str:
    payload = {
        "currency_pair": currency_pair,
        "direction": direction,
        "notional": str(notional),
        "maturity_date": maturity_date.isoformat(),
        "hedge_ratio": None if hedge_ratio is None else str(hedge_ratio),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_row(raw: dict[str, Any]) -> AdvisoryExposureRowV1:
    pair_raw = raw.get("currency_pair")
    if not isinstance(pair_raw, str) or not pair_raw.strip():
        raise AdvisoryInputValidationError("currency_pair is required")
    currency_pair = pair_raw.strip().upper()
    if PAIR_RE.match(currency_pair) is None:
        raise AdvisoryInputValidationError("currency_pair must match AAA/BBB")

    direction_raw = raw.get("direction")
    if not isinstance(direction_raw, str):
        raise AdvisoryInputValidationError("direction is required")
    direction = direction_raw.strip().lower()
    if direction not in ALLOWED_DIRECTIONS:
        raise AdvisoryInputValidationError("direction must be receivable or payable")

    notional = _to_decimal(raw.get("notional"), field="notional")
    if notional <= 0:
        raise AdvisoryInputValidationError("notional must be > 0")

    maturity_date = _parse_date(raw.get("maturity_date"), field="maturity_date")

    hedge_ratio: Decimal | None
    if "hedge_ratio" in raw and raw.get("hedge_ratio") is not None:
        hedge_ratio = _to_decimal(raw.get("hedge_ratio"), field="hedge_ratio")
        if hedge_ratio < 0 or hedge_ratio > 1:
            raise AdvisoryInputValidationError("hedge_ratio must be between 0 and 1")
    else:
        hedge_ratio = None

    row_id = _stable_row_id(
        currency_pair=currency_pair,
        direction=direction,
        notional=notional,
        maturity_date=maturity_date,
        hedge_ratio=hedge_ratio,
    )

    return AdvisoryExposureRowV1(
        row_id=row_id,
        currency_pair=currency_pair,
        direction=direction,
        notional=notional,
        maturity_date=maturity_date,
        hedge_ratio=hedge_ratio,
    )


def normalize_advisory_input_v1(payload: dict[str, Any]) -> AdvisoryInputNormalizedV1:
    if not isinstance(payload, dict):
        raise AdvisoryInputValidationError("payload must be an object")

    contract_version = payload.get("contract_version")
    if contract_version != SUPPORTED_CONTRACT_VERSION:
        raise AdvisoryInputValidationError(f"contract_version must be {SUPPORTED_CONTRACT_VERSION}")

    company_id = payload.get("company_id")
    if not isinstance(company_id, str) or not company_id.strip():
        raise AdvisoryInputValidationError("company_id is required")

    snapshot_id = payload.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        raise AdvisoryInputValidationError("snapshot_id is required")

    scenario_template_id = payload.get("scenario_template_id")
    if not isinstance(scenario_template_id, str) or not scenario_template_id.strip():
        raise AdvisoryInputValidationError("scenario_template_id is required")

    exposures_raw = payload.get("exposures")
    if not isinstance(exposures_raw, list):
        raise AdvisoryInputValidationError("exposures must be a list")

    normalized_rows = []
    for row in exposures_raw:
        if not isinstance(row, dict):
            raise AdvisoryInputValidationError("each exposure row must be an object")
        normalized_rows.append(_normalize_row(row))

    normalized_rows_sorted = tuple(
        sorted(
            normalized_rows,
            key=lambda r: (
                r.currency_pair,
                r.direction,
                r.maturity_date.isoformat(),
                str(r.notional),
                "" if r.hedge_ratio is None else str(r.hedge_ratio),
                r.row_id,
            ),
        )
    )

    return AdvisoryInputNormalizedV1(
        contract_version=SUPPORTED_CONTRACT_VERSION,
        company_id=company_id.strip(),
        snapshot_id=snapshot_id.strip(),
        scenario_template_id=scenario_template_id.strip(),
        exposures=normalized_rows_sorted,
    )


__all__ = [
    "ALLOWED_DIRECTIONS",
    "AdvisoryExposureRowV1",
    "AdvisoryInputNormalizedV1",
    "AdvisoryInputValidationError",
    "SUPPORTED_CONTRACT_VERSION",
    "normalize_advisory_input_v1",
]
