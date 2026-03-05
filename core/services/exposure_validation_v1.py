from __future__ import annotations

from decimal import Decimal
from decimal import InvalidOperation
from typing import Sequence


class ExposureValidationError(ValueError):
    """Raised when exposure rows fail deterministic validation checks."""


def base_ccy_from_pair_v1(pair: str) -> str:
    if not isinstance(pair, str) or "/" not in pair:
        raise ExposureValidationError("INVALID_PAIR: pair must contain '/'")
    base = pair.split("/", 1)[0].strip().upper()
    if not base:
        raise ExposureValidationError("INVALID_PAIR: base currency is empty")
    return base


def quote_ccy_from_pair_v1(pair: str) -> str:
    if not isinstance(pair, str) or "/" not in pair:
        raise ExposureValidationError("INVALID_PAIR: pair must contain '/'")
    quote = pair.split("/", 1)[1].strip().upper()
    if not quote:
        raise ExposureValidationError("INVALID_PAIR: quote currency is empty")
    return quote


def _parse_amount(row: dict, row_index: int) -> Decimal:
    if "amount_foreign" not in row:
        raise ExposureValidationError(
            f"ROW_AMOUNT_ZERO: amount_foreign is required and non-zero, row_index={row_index}"
        )
    try:
        amount = Decimal(str(row["amount_foreign"]))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ExposureValidationError(
            f"ROW_AMOUNT_ZERO: amount_foreign must be numeric and non-zero, row_index={row_index}"
        ) from exc
    if not amount.is_finite() or amount == 0:
        raise ExposureValidationError(
            f"ROW_AMOUNT_ZERO: amount_foreign must be numeric and non-zero, row_index={row_index}"
        )
    return amount


def _normalize_type(row: dict) -> str | None:
    raw = row.get("type")
    if raw is None:
        raw = row.get("direction")
    if raw is None:
        return None
    return str(raw).strip().upper() or None


def _normalize_maturity(row: dict, row_index: int) -> str:
    days = row.get("days_to_maturity")
    if days is not None:
        if not isinstance(days, int) or days < 0:
            raise ExposureValidationError(
                f"ROW_NEGATIVE_DAYS: days_to_maturity must be int >= 0, row_index={row_index}"
            )
        return f"DAYS:{days}"

    maturity_date = row.get("maturity_date")
    if maturity_date is None or not str(maturity_date).strip():
        raise ExposureValidationError(
            f"ROW_MISSING_MATURITY: days_to_maturity or maturity_date is required, row_index={row_index}"
        )
    return f"DATE:{str(maturity_date).strip()}"


def validate_exposure_rows_v1(
    *,
    company_id: str,
    pair: str,
    as_of_date: str,
    exposure_rows: Sequence[dict],
) -> None:
    if not isinstance(company_id, str) or not company_id.strip():
        raise ExposureValidationError("INVALID_COMPANY_ID: company_id must be non-empty")
    if not isinstance(pair, str) or "/" not in pair:
        raise ExposureValidationError("INVALID_PAIR: pair must contain '/'")
    if not isinstance(as_of_date, str) or not as_of_date.strip():
        raise ExposureValidationError("INVALID_AS_OF_DATE: as_of_date must be non-empty")

    base_ccy = base_ccy_from_pair_v1(pair)
    _ = quote_ccy_from_pair_v1(pair)

    if not exposure_rows:
        raise ExposureValidationError("EMPTY_EXPOSURES: exposure_rows must be non-empty")

    seen: set[tuple[str, str, str, str | None]] = set()

    for i, row in enumerate(exposure_rows):
        if not isinstance(row, dict):
            raise ExposureValidationError(f"ROW_INVALID_TYPE: each row must be dict, row_index={i}")

        ccy = row.get("ccy")
        if ccy is None:
            ccy = row.get("currency")
        ccy_norm = str(ccy).strip().upper() if ccy is not None else ""
        if ccy_norm != base_ccy:
            raise ExposureValidationError(
                f"ROW_CCY_MISMATCH: row currency must match base currency {base_ccy}, row_index={i}"
            )

        amount = _parse_amount(row, i)
        maturity_norm = _normalize_maturity(row, i)
        type_norm = _normalize_type(row)

        if amount > 0 and type_norm not in {"PAYABLE", "RECEIVABLE"}:
            raise ExposureValidationError(
                f"ROW_DIRECTION_AMBIGUOUS: positive amount requires type/direction PAYABLE or RECEIVABLE, row_index={i}"
            )

        dup_key = (ccy_norm, maturity_norm, str(amount), type_norm)
        if dup_key in seen:
            raise ExposureValidationError(
                f"DUPLICATE_ROW: normalized duplicate exposure row, row_index={i}"
            )
        seen.add(dup_key)


__all__ = [
    "ExposureValidationError",
    "base_ccy_from_pair_v1",
    "quote_ccy_from_pair_v1",
    "validate_exposure_rows_v1",
]
