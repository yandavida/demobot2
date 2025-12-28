from core.contracts.money import Currency
from .models import InstitutionalFxMtmResult

class InstitutionalFxPricingEngine:
    def price_forward(
        self,
        *,
        notional: float,
        spot: float,
        contract_forward_rate: float,
        df_base: float,
        df_quote: float,
        df_mtm: float,
        presentation_currency: Currency,
    ) -> InstitutionalFxMtmResult:
        # 1) Market forward
        F_market = spot * (df_base / df_quote)
        # 2) Forward diff
        diff = F_market - contract_forward_rate
        # 3) MTM
        mtm = notional * diff * df_mtm
        # 4) Components
        spot_component = notional * (spot * (df_base / df_quote - 1.0)) * df_mtm
        forward_points_component = notional * (spot - contract_forward_rate) * df_mtm
        discounting_component = mtm - (spot_component + forward_points_component)
        return InstitutionalFxMtmResult(
            mtm=mtm,
            currency=presentation_currency,
            spot_component=spot_component,
            forward_points_component=forward_points_component,
            discounting_component=discounting_component,
        )
