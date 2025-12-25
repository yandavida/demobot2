from core.greeks import aggregate_greeks

def test_greeks_aggregation_scaling():
    # Example: two legs, same params, different qty
    g1 = {'vega': 1.0, 'theta': -2.0}
    g2 = {'vega': 1.0, 'theta': -2.0}
    qty1 = 2
    qty2 = 4
    cmult = 10
    agg1 = aggregate_greeks([g1], [qty1], [cmult])
    agg2 = aggregate_greeks([g2], [qty2], [cmult])
    # Scaling: double qty, double result
    assert abs(agg2['vega'] / agg1['vega'] - qty2 / qty1) < 1e-10
    assert abs(agg2['theta'] / agg1['theta'] - qty2 / qty1) < 1e-10
    # Canonical units: vega per 1%, theta per day
    assert abs(agg1['vega'] - 1.0 * qty1 * cmult) < 1e-10
    assert abs(agg1['theta'] + 2.0 * qty1 * cmult) < 1e-10
