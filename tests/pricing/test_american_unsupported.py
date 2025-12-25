import pytest
from core.pricing.bs import bs_greeks

def test_american_option_raises():
    # American options are not supported; must raise with clear message
    with pytest.raises((NotImplementedError, ValueError)) as excinfo:
        # Simulate an American option by passing a flag or type (here, cp='A')
        bs_greeks(spot=100, strike=100, t=1.0, rate=0.01, div=0.0, vol=0.2, cp='A')
    msg = str(excinfo.value).lower()
    assert (
        'american' in msg
        or 'unsupported' in msg
        or 'invalid option type' in msg
    )
