from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional
from core.contracts.money import Currency

class InstrumentType(str, Enum):
    FORWARD = "FORWARD"
    SWAP = "SWAP"

@dataclass(frozen=True)
class BankMtmLegInput:
    mtm: float
    currency: Currency
    spot_component: Optional[float] = None
    forward_points_component: Optional[float] = None
    discounting_component: Optional[float] = None

@dataclass(frozen=True)
class BankFxForwardStatement:
    pair: str
    notional_base: float
    value_date: Any = None
    maturity_date: Any = None
    presentation_currency: Currency = "ILS"
    mtm_total: float = 0.0
    leg: Optional[BankMtmLegInput] = None

@dataclass(frozen=True)
class BankFxSwapStatement:
    pair: str
    base_notional: float
    near_date: Any = None
    far_date: Any = None
    presentation_currency: Currency = "ILS"
    mtm_total: float = 0.0
    near_leg: Optional[BankMtmLegInput] = None
    far_leg: Optional[BankMtmLegInput] = None

@dataclass(frozen=True)
class ReconDelta:
    total_delta: float
    near_delta: Optional[float] = None
    far_delta: Optional[float] = None
    components_delta: dict[str, float] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

@dataclass(frozen=True)
class ReconResult:
    instrument: InstrumentType
    pair: str
    currency: Currency
    system_total: float
    bank_total: float
    delta: ReconDelta
