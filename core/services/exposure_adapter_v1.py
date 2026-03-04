from __future__ import annotations

import datetime
from decimal import Decimal
import hashlib

from core.pricing.fx.types import FXForwardContract
from core.services.advisory_input_contract_v1 import AdvisoryInputNormalizedV1


def _to_float(value: Decimal) -> float:
    return float(value)


def _instrument_id(
    *,
    company_id: str,
    currency_pair: str,
    maturity_date: datetime.date,
    row_id: str,
) -> str:
    material = f"{company_id}|{currency_pair}|{maturity_date.isoformat()}|{row_id}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"fxfwd_{digest}"


def _direction_from_business(direction: str) -> str:
    if direction == "receivable":
        return "receive_foreign_pay_domestic"
    return "pay_foreign_receive_domestic"


def build_risk_request_from_advisory_v1(normalized_input: AdvisoryInputNormalizedV1):
    rows = tuple(
        sorted(
            normalized_input.exposures,
            key=lambda row: (
                row.currency_pair,
                row.maturity_date.isoformat(),
                row.row_id,
            ),
        )
    )

    contracts_by_instrument_id: dict[str, FXForwardContract] = {}
    for row in rows:
        base_currency, quote_currency = row.currency_pair.split("/", 1)
        effective_notional = row.notional
        if row.hedge_ratio is not None:
            effective_notional = effective_notional * row.hedge_ratio

        instrument_id = _instrument_id(
            company_id=normalized_input.company_id,
            currency_pair=row.currency_pair,
            maturity_date=row.maturity_date,
            row_id=row.row_id,
        )

        contracts_by_instrument_id[instrument_id] = FXForwardContract(
            base_currency=base_currency,
            quote_currency=quote_currency,
            notional=_to_float(effective_notional),
            forward_date=row.maturity_date,
            direction=_direction_from_business(row.direction),
        )

    instrument_ids = tuple(sorted(contracts_by_instrument_id.keys()))
    domestic_currency = rows[0].currency_pair.split("/", 1)[1] if rows else ""

    risk_request = {
        "snapshot_id": normalized_input.snapshot_id,
        "scenario_template_id": normalized_input.scenario_template_id,
        "instrument_ids": instrument_ids,
        "valuation_context": {
            "domestic_currency": domestic_currency,
        },
    }

    return contracts_by_instrument_id, risk_request


__all__ = ["build_risk_request_from_advisory_v1"]
