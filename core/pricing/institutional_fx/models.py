from dataclasses import dataclass
from core.contracts.money import Currency

@dataclass(frozen=True)
class InstitutionalFxMtmResult:
    mtm: float
    currency: Currency
    spot_component: float
    forward_points_component: float
    discounting_component: float

@dataclass(frozen=True)
class FxForwardInput:
    notional: float
    spot: float
    contract_forward_rate: float
    df_base: float
    df_quote: float
    df_mtm: float
