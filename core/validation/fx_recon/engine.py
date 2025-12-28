from core.validation.fx_recon.models import (
    InstrumentType, BankFxForwardStatement, BankFxSwapStatement, ReconResult, ReconDelta
)
from core.pricing.institutional_fx.models import InstitutionalFxMtmResult
from core.pricing.institutional_fx.swaps_models import FxSwapMtmResult

def reconcile_fx_forward(*, system: InstitutionalFxMtmResult, bank: BankFxForwardStatement, tol: float = 0.01) -> ReconResult:
    notes = []
    if system.currency != bank.presentation_currency:
        raise ValueError("Currency mismatch between system and bank statement")
    total_delta = system.mtm - bank.mtm_total
    components_delta = {}
    near_delta = None
    far_delta = None
    # Components
    if bank.leg is not None:
        for comp in ["spot_component", "forward_points_component", "discounting_component"]:
            sys_val = getattr(system, comp, None)
            bank_val = getattr(bank.leg, comp, None)
            if sys_val is not None and bank_val is not None:
                components_delta[comp] = sys_val - bank_val
    else:
        notes.append("bank_leg_missing")
    if abs(total_delta) <= tol:
        notes.append("within_tolerance")
    else:
        notes.append("out_of_tolerance")
    delta = ReconDelta(
        total_delta=total_delta,
        near_delta=near_delta,
        far_delta=far_delta,
        components_delta=components_delta,
        notes=tuple(notes),
    )
    return ReconResult(
        instrument=InstrumentType.FORWARD,
        pair=bank.pair,
        currency=system.currency,
        system_total=system.mtm,
        bank_total=bank.mtm_total,
        delta=delta,
    )

def reconcile_fx_swap(*, system: FxSwapMtmResult, bank: BankFxSwapStatement, tol: float = 0.01) -> ReconResult:
    notes = []
    if system.currency != bank.presentation_currency:
        raise ValueError("Currency mismatch between system and bank statement")
    total_delta = system.mtm - bank.mtm_total
    # Per-leg deltas
    near_delta = far_delta = None
    if bank.near_leg is not None and system.near_leg is not None:
        near_delta = system.near_leg.mtm - bank.near_leg.mtm
    else:
        notes.append("bank_near_leg_missing")
    if bank.far_leg is not None and system.far_leg is not None:
        far_delta = system.far_leg.mtm - bank.far_leg.mtm
    else:
        notes.append("bank_far_leg_missing")
    # Components delta (only if both legs present)
    components_delta = {}
    for comp in ["spot_component", "forward_points_component", "discounting_component"]:
        sys_near = getattr(system.near_leg, comp, None) if system.near_leg else None
        bank_near = getattr(bank.near_leg, comp, None) if bank.near_leg else None
        sys_far = getattr(system.far_leg, comp, None) if system.far_leg else None
        bank_far = getattr(bank.far_leg, comp, None) if bank.far_leg else None
        # Only if both present and same currency
        if sys_near is not None and bank_near is not None:
            components_delta[f"near_{comp}"] = sys_near - bank_near
        if sys_far is not None and bank_far is not None:
            components_delta[f"far_{comp}"] = sys_far - bank_far
    if bank.near_leg is None or bank.far_leg is None:
        notes.append("bank_legs_missing")
    if abs(total_delta) <= tol:
        notes.append("within_tolerance")
    else:
        notes.append("out_of_tolerance")
    delta = ReconDelta(
        total_delta=total_delta,
        near_delta=near_delta,
        far_delta=far_delta,
        components_delta=components_delta,
        notes=tuple(notes),
    )
    return ReconResult(
        instrument=InstrumentType.SWAP,
        pair=bank.pair,
        currency=system.currency,
        system_total=system.mtm,
        bank_total=bank.mtm_total,
        delta=delta,
    )
