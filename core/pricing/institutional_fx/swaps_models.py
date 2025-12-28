from enum import Enum
from dataclasses import dataclass
from core.contracts.money import Currency
from core.pricing.institutional_fx.models import InstitutionalFxMtmResult

class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class SwapType(str, Enum):
    BUY_SELL = "BUY_SELL"
    SELL_BUY = "SELL_BUY"

@dataclass(frozen=True)
class FxSwapTrade:
    pair: str
    base_notional: float
    swap_type: SwapType
    near_forward_rate: float
    far_forward_rate: float
    near_df_base: float
    near_df_quote: float
    near_df_mtm: float
    far_df_base: float
    far_df_quote: float
    far_df_mtm: float
    spot: float
    presentation_currency: Currency

    def __post_init__(self):
        if not isinstance(self.pair, str) or "/" not in self.pair:
            raise ValueError(f"Invalid pair format: {self.pair!r}")
        base, quote = self.pair.split("/")
        if not base or not quote:
            raise ValueError(f"Invalid pair format: {self.pair!r}")
        if self.base_notional <= 0:
            raise ValueError("base_notional must be > 0")
        for attr in ["near_df_base", "near_df_quote", "near_df_mtm", "far_df_base", "far_df_quote", "far_df_mtm"]:
            if getattr(self, attr) <= 0:
                raise ValueError(f"{attr} must be > 0")

@dataclass(frozen=True)
class FxSwapMtmResult:
    mtm: float
    currency: Currency
    near_leg: InstitutionalFxMtmResult
    far_leg: InstitutionalFxMtmResult
    notes: tuple[str, ...] = ()
