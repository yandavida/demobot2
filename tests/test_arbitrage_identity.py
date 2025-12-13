from core.arbitrage.identity import opportunity_id


def test_opportunity_id_stable_within_bucket() -> None:
    base_params = dict(
        symbol="ES",
        buy_venue="A",
        sell_venue="B",
        base_ccy="USD",
        buy_price_base=100.001,
        sell_price_base=101.002,
        tick=0.01,
    )
    first = opportunity_id(**base_params)
    second = opportunity_id(**base_params)
    assert first == second


def test_opportunity_id_bucket_tolerance() -> None:
    id1 = opportunity_id(
        symbol="ES",
        buy_venue="A",
        sell_venue="B",
        base_ccy="USD",
        buy_price_base=100.001,
        sell_price_base=101.004,
        tick=0.01,
    )
    id2 = opportunity_id(
        symbol="ES",
        buy_venue="A",
        sell_venue="B",
        base_ccy="USD",
        buy_price_base=100.005,
        sell_price_base=101.006,
        tick=0.01,
    )
    assert id1 == id2


def test_opportunity_id_changes_on_venue_order() -> None:
    id1 = opportunity_id(
        symbol="ES",
        buy_venue="A",
        sell_venue="B",
        base_ccy="USD",
        buy_price_base=100.0,
        sell_price_base=101.0,
    )
    id2 = opportunity_id(
        symbol="ES",
        buy_venue="B",
        sell_venue="A",
        base_ccy="USD",
        buy_price_base=100.0,
        sell_price_base=101.0,
    )
    assert id1 != id2
