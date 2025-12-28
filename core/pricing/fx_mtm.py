from core.contracts.money import Currency
from core.pricing.mtm_method import FxMtmMethod
from core.pricing.institutional_fx.engine import InstitutionalFxPricingEngine

def compute_fx_forward_mtm(
    *,
    method: FxMtmMethod,
    notional: float,
    spot: float,
    contract_forward_rate: float,
    df_base: float,
    df_quote: float,
    df_mtm: float,
    presentation_currency: Currency,
    institutional_engine: InstitutionalFxPricingEngine | None = None,
) -> float:
    if method == FxMtmMethod.THEORETICAL:
        raise NotImplementedError(
            "THEORETICAL forward MTM is computed in F6.2; wiring for forward MTM is INSTITUTIONAL-only for now."
        )
    if method == FxMtmMethod.INSTITUTIONAL:
        if institutional_engine is None:
            raise ValueError("institutional_engine must be provided for INSTITUTIONAL method")
        result = institutional_engine.price_forward(
            notional=notional,
            spot=spot,
            contract_forward_rate=contract_forward_rate,
            df_base=df_base,
            df_quote=df_quote,
            df_mtm=df_mtm,
            presentation_currency=presentation_currency,
        )
        return result.mtm
    raise ValueError(f"Unknown FX MTM method: {method}")
