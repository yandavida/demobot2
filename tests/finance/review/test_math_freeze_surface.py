import inspect
import math
from core.pnl.theoretical import compute_position_pnl
from core.pnl.portfolio_breakdown import compute_portfolio_pnl_breakdown
from core.contracts.money import Currency

def dummy_fx():
    class DummyFxConverter:
        def convert(self, amount: float, from_ccy: Currency, to_ccy: Currency, *, strict: bool = True) -> float:
            if from_ccy == to_ccy:
                return float(amount)
            if from_ccy == "USD" and to_ccy == "ILS":
                return float(amount) * 4
            if from_ccy == "ILS" and to_ccy == "USD":
                return float(amount) / 4
            raise ValueError("Unsupported currency conversion")
    return DummyFxConverter()

def make_price(pv, ccy, breakdown):
    return type("PriceResult", (), {"pv": pv, "currency": ccy, "breakdown": breakdown})()

def test_signature_lock():
    # F6.5: InstitutionalFxSwapPricingEngine.price_swap signature
    from core.pricing.institutional_fx.swaps_engine import InstitutionalFxSwapPricingEngine
    from core.pricing.institutional_fx.swaps_models import FxSwapTrade, FxSwapMtmResult
    swap_engine = InstitutionalFxSwapPricingEngine
    swap_sig = inspect.signature(swap_engine.price_swap)
    swap_params = list(swap_sig.parameters)
    assert swap_params == ["self", "trade"]
    # FxSwapTrade dataclass fields
    import dataclasses
    trade_fields = [f.name for f in dataclasses.fields(FxSwapTrade)]
    required_trade = [
        "pair", "base_notional", "swap_type", "near_forward_rate", "far_forward_rate",
        "near_df_base", "near_df_quote", "near_df_mtm", "far_df_base", "far_df_quote", "far_df_mtm", "spot", "presentation_currency"
    ]
    for f in required_trade:
        assert f in trade_fields
    # FxSwapMtmResult dataclass fields
    mtm_fields = [f.name for f in dataclasses.fields(FxSwapMtmResult)]
    required_mtm = ["mtm", "currency", "near_leg", "far_leg"]
    for f in required_mtm:
        assert f in mtm_fields
    sig = inspect.signature(compute_position_pnl)
    params = list(sig.parameters)
    required = ["position_id", "symbol", "prev_pr", "curr_pr", "prev_snapshot", "curr_snapshot", "quantity", "base_currency", "fx_converter", "mode"]
    for r in required:
        assert r in params, f"Missing param: {r}"
    sig2 = inspect.signature(compute_portfolio_pnl_breakdown)
    assert "positions_inputs" in sig2.parameters
    # FxConverter signature (robust to bound/unbound)
    fx = dummy_fx()
    fx_sig = inspect.signature(type(fx).convert)
    fx_params = list(fx_sig.parameters)
    assert fx_params[0] == "self"
    assert fx_params[1:4] == ["amount", "from_ccy", "to_ccy"]
    if "strict" in fx_sig.parameters:
        assert fx_sig.parameters["strict"].kind == inspect.Parameter.KEYWORD_ONLY

def test_frozen_invariants_quick():
    fx = dummy_fx()
    pr1 = make_price(100, "USD", {"delta": 1.0, "theta": 2.0, "gamma": 0.0, "vega": 0.0})
    prev1 = make_price(90, "USD", {"delta": 1.0, "theta": 2.0, "gamma": 0.0, "vega": 0.0})
    pr2 = make_price(400, "ILS", {"delta": 2.0, "theta": 1.0, "gamma": 0.0, "vega": 0.0})
    prev2 = make_price(360, "ILS", {"delta": 2.0, "theta": 1.0, "gamma": 0.0, "vega": 0.0})
    pos1 = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    pos2 = compute_position_pnl(position_id="p2", symbol="B", prev_pr=prev2, curr_pr=pr2, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    # Additivity
    total = pos1.pnl + pos2.pnl
    sum_components = math.fsum([pos1.attribution.delta_pnl + pos2.attribution.delta_pnl,
                                pos1.attribution.theta_pnl + pos2.attribution.theta_pnl,
                                pos1.attribution.gamma_pnl + pos2.attribution.gamma_pnl,
                                pos1.attribution.vega_pnl + pos2.attribution.vega_pnl,
                                pos1.attribution.residual + pos2.attribution.residual])
    assert math.isclose(total, sum_components, rel_tol=1e-12)
    # Portfolio
    portfolio = compute_portfolio_pnl_breakdown(positions_inputs=[pos1, pos2], base_currency="USD")
    assert math.isclose(portfolio.total_pnl, total, rel_tol=1e-12)
    # Permutation invariance
    perm1 = [pos1, pos2]
    perm2 = [pos2, pos1]
    p1 = compute_portfolio_pnl_breakdown(positions_inputs=perm1, base_currency="USD")
    p2 = compute_portfolio_pnl_breakdown(positions_inputs=perm2, base_currency="USD")
    assert p1.total_pnl == p2.total_pnl
    assert p1.delta_pnl == p2.delta_pnl
    assert p1.theta_pnl == p2.theta_pnl
    assert p1.gamma_pnl == p2.gamma_pnl
    assert p1.vega_pnl == p2.vega_pnl
    assert p1.residual == p2.residual
