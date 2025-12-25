def to_canonical_greeks(g):
    """
    Convert greeks dict from bs_greeks (vega per 1.0 vol, theta per year)
    to canonical units (vega per 1% vol, theta per day).
    """
    out = dict(g)
    if 'vega' in out:
        out['vega'] = out['vega'] / 100.0
    if 'theta' in out:
        out['theta'] = out['theta'] / 365.0
    return out
