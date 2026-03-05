from __future__ import annotations

import pytest

from core.services.exposure_validation_v1 import ExposureValidationError
from core.services.exposure_validation_v1 import validate_exposure_rows_v1


def test_valid_rows_pass() -> None:
    validate_exposure_rows_v1(
        company_id="treasury-demo",
        pair="USD/ILS",
        as_of_date="2026-03-05",
        exposure_rows=[
            {
                "ccy": "USD",
                "amount_foreign": -1000000,
                "days_to_maturity": 30,
            },
            {
                "currency": "USD",
                "amount_foreign": 1500000,
                "type": "RECEIVABLE",
                "maturity_date": "2026-06-15",
            },
        ],
    )


def test_empty_rows_raises() -> None:
    with pytest.raises(ExposureValidationError, match="EMPTY_EXPOSURES"):
        validate_exposure_rows_v1(
            company_id="treasury-demo",
            pair="USD/ILS",
            as_of_date="2026-03-05",
            exposure_rows=[],
        )


def test_ccy_mismatch_raises() -> None:
    with pytest.raises(ExposureValidationError, match="ROW_CCY_MISMATCH"):
        validate_exposure_rows_v1(
            company_id="treasury-demo",
            pair="USD/ILS",
            as_of_date="2026-03-05",
            exposure_rows=[
                {
                    "ccy": "EUR",
                    "amount_foreign": -1000000,
                    "days_to_maturity": 30,
                }
            ],
        )


def test_missing_maturity_raises() -> None:
    with pytest.raises(ExposureValidationError, match="ROW_MISSING_MATURITY"):
        validate_exposure_rows_v1(
            company_id="treasury-demo",
            pair="USD/ILS",
            as_of_date="2026-03-05",
            exposure_rows=[
                {
                    "ccy": "USD",
                    "amount_foreign": -1000000,
                }
            ],
        )


def test_negative_days_raises() -> None:
    with pytest.raises(ExposureValidationError, match="ROW_NEGATIVE_DAYS"):
        validate_exposure_rows_v1(
            company_id="treasury-demo",
            pair="USD/ILS",
            as_of_date="2026-03-05",
            exposure_rows=[
                {
                    "ccy": "USD",
                    "amount_foreign": -1000000,
                    "days_to_maturity": -1,
                }
            ],
        )


def test_direction_ambiguous_raises() -> None:
    with pytest.raises(ExposureValidationError, match="ROW_DIRECTION_AMBIGUOUS"):
        validate_exposure_rows_v1(
            company_id="treasury-demo",
            pair="USD/ILS",
            as_of_date="2026-03-05",
            exposure_rows=[
                {
                    "ccy": "USD",
                    "amount_foreign": 1000000,
                    "days_to_maturity": 10,
                }
            ],
        )


def test_duplicate_rows_raises() -> None:
    with pytest.raises(ExposureValidationError, match="DUPLICATE_ROW"):
        validate_exposure_rows_v1(
            company_id="treasury-demo",
            pair="USD/ILS",
            as_of_date="2026-03-05",
            exposure_rows=[
                {
                    "ccy": "USD",
                    "amount_foreign": -1000000,
                    "days_to_maturity": 30,
                    "type": "payable",
                },
                {
                    "currency": "USD",
                    "amount_foreign": "-1000000",
                    "days_to_maturity": 30,
                    "type": "PAYABLE",
                },
            ],
        )
