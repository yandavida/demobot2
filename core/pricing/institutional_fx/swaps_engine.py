import math
from core.pricing.institutional_fx.swaps_models import FxSwapTrade, FxSwapMtmResult, SwapType, Action
from core.pricing.institutional_fx.engine import InstitutionalFxPricingEngine

class InstitutionalFxSwapPricingEngine:
    def __init__(self, forward_engine: InstitutionalFxPricingEngine):
        self.forward_engine = forward_engine

    def price_swap(self, *, trade: FxSwapTrade) -> FxSwapMtmResult:
        base_ccy, quote_ccy = trade.pair.split("/")
        notes = []
        # Presentation currency validation
        if trade.presentation_currency not in (base_ccy, quote_ccy):
            raise ValueError(f"presentation_currency must be base or quote (got {trade.presentation_currency})")
        # Determine actions
        if trade.swap_type == SwapType.BUY_SELL:
            near_action, far_action = Action.BUY, Action.SELL
        elif trade.swap_type == SwapType.SELL_BUY:
            near_action, far_action = Action.SELL, Action.BUY
        else:
            raise ValueError(f"Unknown swap_type: {trade.swap_type}")
        # Notional sign logic
        def signed_notional(action, presentation):
            if presentation == quote_ccy:
                return -trade.base_notional if action == Action.BUY else trade.base_notional
            else:
                notes.append(f"presentation_currency is base ({base_ccy}), sign logic reversed")
                return trade.base_notional if action == Action.BUY else -trade.base_notional
        near_signed = signed_notional(near_action, trade.presentation_currency)
        far_signed = signed_notional(far_action, trade.presentation_currency)
        # Price each leg
        near_leg = self.forward_engine.price_forward(
            notional=near_signed,
            spot=trade.spot,
            contract_forward_rate=trade.near_forward_rate,
            df_base=trade.near_df_base,
            df_quote=trade.near_df_quote,
            df_mtm=trade.near_df_mtm,
            presentation_currency=trade.presentation_currency,
        )
        far_leg = self.forward_engine.price_forward(
            notional=far_signed,
            spot=trade.spot,
            contract_forward_rate=trade.far_forward_rate,
            df_base=trade.far_df_base,
            df_quote=trade.far_df_quote,
            df_mtm=trade.far_df_mtm,
            presentation_currency=trade.presentation_currency,
        )
        total_mtm = math.fsum([near_leg.mtm, far_leg.mtm])
        return FxSwapMtmResult(
            mtm=total_mtm,
            currency=trade.presentation_currency,
            near_leg=near_leg,
            far_leg=far_leg,
            notes=tuple(notes),
        )
