from core.fx_math import fx_forward_payoff_curve
import numpy as np

def test_fx_forward_convention_buy_sell_base():
    notional = 1_000_000
    forward = 3.5
    spot_up = 3.6
    spot_down = 3.4
    # BUY_BASE
    pl_buy_up = fx_forward_payoff_curve(spot_up, forward, notional, 'BUY_BASE')
    pl_buy_down = fx_forward_payoff_curve(spot_down, forward, notional, 'BUY_BASE')
    assert pl_buy_up > pl_buy_down
    assert fx_forward_payoff_curve(forward, forward, notional, 'BUY_BASE') == 0
    # SELL_BASE
    pl_sell_up = fx_forward_payoff_curve(spot_up, forward, notional, 'SELL_BASE')
    pl_sell_down = fx_forward_payoff_curve(spot_down, forward, notional, 'SELL_BASE')
    assert pl_sell_up < pl_sell_down
    assert fx_forward_payoff_curve(forward, forward, notional, 'SELL_BASE') == 0
    # Opposite sign
    assert np.isclose(pl_buy_up, -pl_sell_up)
    assert np.isclose(pl_buy_down, -pl_sell_down)
