from __future__ import annotations

from dataclasses import dataclass
import datetime
from decimal import Decimal
from decimal import InvalidOperation
import json
from typing import Any


SUPPORTED_CONTRACT_VERSION = "v1"
SUPPORTED_OPTION_TYPES = {"call", "put"}
SUPPORTED_TIME_FRACTION_POLICY_IDS = {"ACT_365F"}


def _to_decimal(value: Any, field: str) -> Decimal:
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a valid decimal") from exc
    if not dec.is_finite():
        raise ValueError(f"{field} must be finite")
    return dec


@dataclass(frozen=True)
class OptionContractV1:
    instrument_id: str
    underlying: str
    option_type: str
    strike: Decimal
    expiry: datetime.datetime
    notional: Decimal
    domestic_ccy: str
    foreign_ccy: str
    time_fraction_policy_id: str
    contract_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, str) or not self.instrument_id.strip():
            raise ValueError("instrument_id must be a non-empty string")
        if not isinstance(self.underlying, str) or not self.underlying.strip():
            raise ValueError("underlying must be a non-empty string")

        option_type = str(self.option_type).strip().lower()
        if option_type not in SUPPORTED_OPTION_TYPES:
            raise ValueError(f"option_type must be one of {sorted(SUPPORTED_OPTION_TYPES)}")
        object.__setattr__(self, "option_type", option_type)

        strike = _to_decimal(self.strike, "strike")
        if strike <= 0:
            raise ValueError("strike must be > 0")
        object.__setattr__(self, "strike", strike)

        notional = _to_decimal(self.notional, "notional")
        if notional <= 0:
            raise ValueError("notional must be > 0")
        object.__setattr__(self, "notional", notional)

        if not isinstance(self.expiry, datetime.datetime):
            raise ValueError("expiry must be a datetime")
        if self.expiry.tzinfo is None:
            raise ValueError("expiry must be timezone-aware")

        if not isinstance(self.domestic_ccy, str) or len(self.domestic_ccy.strip()) != 3:
            raise ValueError("domestic_ccy must be a 3-letter currency code")
        if not isinstance(self.foreign_ccy, str) or len(self.foreign_ccy.strip()) != 3:
            raise ValueError("foreign_ccy must be a 3-letter currency code")
        object.__setattr__(self, "domestic_ccy", self.domestic_ccy.strip().upper())
        object.__setattr__(self, "foreign_ccy", self.foreign_ccy.strip().upper())

        policy_id = str(self.time_fraction_policy_id).strip().upper()
        if policy_id not in SUPPORTED_TIME_FRACTION_POLICY_IDS:
            raise ValueError(
                f"time_fraction_policy_id must be one of {sorted(SUPPORTED_TIME_FRACTION_POLICY_IDS)}"
            )
        object.__setattr__(self, "time_fraction_policy_id", policy_id)

        if self.contract_version != SUPPORTED_CONTRACT_VERSION:
            raise ValueError(f"contract_version must be {SUPPORTED_CONTRACT_VERSION}")

    def to_dict(self) -> dict[str, str]:
        return {
            "contract_version": self.contract_version,
            "domestic_ccy": self.domestic_ccy,
            "expiry": self.expiry.isoformat(),
            "foreign_ccy": self.foreign_ccy,
            "instrument_id": self.instrument_id,
            "notional": str(self.notional),
            "option_type": self.option_type,
            "strike": str(self.strike),
            "time_fraction_policy_id": self.time_fraction_policy_id,
            "underlying": self.underlying,
        }

    def to_canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> OptionContractV1:
        return cls(
            instrument_id=payload["instrument_id"],
            underlying=payload["underlying"],
            option_type=payload["option_type"],
            strike=payload["strike"],
            expiry=datetime.datetime.fromisoformat(payload["expiry"]),
            notional=payload["notional"],
            domestic_ccy=payload["domestic_ccy"],
            foreign_ccy=payload["foreign_ccy"],
            time_fraction_policy_id=payload["time_fraction_policy_id"],
            contract_version=payload["contract_version"],
        )


__all__ = [
    "OptionContractV1",
    "SUPPORTED_CONTRACT_VERSION",
    "SUPPORTED_OPTION_TYPES",
    "SUPPORTED_TIME_FRACTION_POLICY_IDS",
]
