from core.pnl.theoretical import compute_position_pnl
from core.pricing.types import PriceResult
from core.contracts.money import Currency, Money

class DummyFxConverter:
    def convert(self, money: Money, to_ccy: Currency) -> Money:
        # USD <-> ILS: 1 USD = 4 ILS
        if money.ccy == to_ccy:
            return money
        if money.ccy == "USD" and to_ccy == "ILS":
            return Money(money.amount * 4, "ILS")
        if money.ccy == "ILS" and to_ccy == "USD":
            return Money(money.amount / 4, "USD")
        raise ValueError("Unsupported currency conversion")

class DummySnapshot:
    def __init__(self, spot: float, iv: float = 0.0):
        self._spot = spot
        self._iv = iv
    def get_spot(self, symbol):
        return self._spot
    def get_iv(self, symbol):
        return self._iv

def test_step_pnl_basic():
    pr1 = PriceResult(pv=100.0, currency="USD", breakdown={"delta": 1.0})
    pr2 = PriceResult(pv=110.0, currency="USD", breakdown={"delta": 1.0})
    snap1 = DummySnapshot(spot=100.0)
    snap2 = DummySnapshot(spot=110.0)
    pnl = compute_position_pnl(
        position_id="pos1",
        symbol="A",
        prev_pr=pr1,
        curr_pr=pr2,
        prev_snapshot=snap1,
        curr_snapshot=snap2,
        quantity=1.0,
        base_currency="USD",
        fx_converter=DummyFxConverter(),
        mode="step",
        t_prev=1,
        t_curr=2,
    )
    assert abs(pnl.pnl - 10.0) < 1e-8
    assert abs(pnl.attribution.delta_pnl - 10.0) < 1e-8
    assert pnl.currency == "USD"

def test_currency_conversion():
    pr1 = PriceResult(pv=400.0, currency="ILS", breakdown={"delta": 1.0})
    pr2 = PriceResult(pv=440.0, currency="ILS", breakdown={"delta": 1.0})
    snap1 = DummySnapshot(spot=100.0)
    snap2 = DummySnapshot(spot=110.0)
    pnl = compute_position_pnl(
        position_id="pos1",
        symbol="A",
        prev_pr=pr1,
        curr_pr=pr2,
        prev_snapshot=snap1,
        curr_snapshot=snap2,
        quantity=1.0,
        base_currency="USD",
        fx_converter=DummyFxConverter(),
        mode="step",
        t_prev=1,
        t_curr=2,
    )
    assert abs(pnl.pv - 110.0) < 1e-8
    assert abs(pnl.pnl - 10.0) < 1e-8
    assert pnl.currency == "USD"

def test_attribution_no_prev_snapshot():
    pr2 = PriceResult(pv=110.0, currency="USD", breakdown={"delta": 1.0})
    snap2 = DummySnapshot(spot=110.0)
    pnl = compute_position_pnl(
        position_id="pos1",
        symbol="A",
        prev_pr=None,
        curr_pr=pr2,
        prev_snapshot=None,
        curr_snapshot=snap2,
        quantity=1.0,
        base_currency="USD",
        fx_converter=DummyFxConverter(),
        mode="step",
        t_prev=None,
        t_curr=2,
    )
    assert pnl.attribution.delta_pnl == 0.0
    assert "No previous snapshot" in " ".join(pnl.attribution.notes)

def test_vega_attribution_missing_iv():
    pr1 = PriceResult(pv=100.0, currency="USD", breakdown={"delta": 1.0, "vega": 2.0})
    pr2 = PriceResult(pv=110.0, currency="USD", breakdown={"delta": 1.0, "vega": 2.0})
    snap1 = DummySnapshot(spot=100.0)
    snap2 = DummySnapshot(spot=110.0)
    # No IV in snapshots
    pnl = compute_position_pnl(
        position_id="pos1",
        symbol="A",
        prev_pr=pr1,
        curr_pr=pr2,
        prev_snapshot=snap1,
        curr_snapshot=snap2,
        quantity=1.0,
        base_currency="USD",
        fx_converter=DummyFxConverter(),
        mode="step",
        t_prev=1,
        t_curr=2,
    )
    assert pnl.attribution.vega_pnl == 0.0
    assert "dIV=0" in " ".join(pnl.attribution.notes)

def test_determinism():
    pr1 = PriceResult(pv=100.0, currency="USD", breakdown={"delta": 1.0})
    pr2 = PriceResult(pv=110.0, currency="USD", breakdown={"delta": 1.0})
    snap1 = DummySnapshot(spot=100.0)
    snap2 = DummySnapshot(spot=110.0)
    args = dict(
        position_id="pos1",
        symbol="A",
        prev_pr=pr1,
        curr_pr=pr2,
        prev_snapshot=snap1,
        curr_snapshot=snap2,
        quantity=1.0,
        base_currency="USD",
        fx_converter=DummyFxConverter(),
        mode="step",
        t_prev=1,
        t_curr=2,
    )
    pnl1 = compute_position_pnl(**args)
    pnl2 = compute_position_pnl(**args)
    assert pnl1 == pnl2
