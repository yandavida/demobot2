from core.arbitrage import (
    ArbitrageConfig,
    ArbitrageOpportunity,
    VenueQuote,
    find_cross_venue_opportunities,
)


def test_finds_cross_venue_opportunity_with_fees():
    quotes = [
        VenueQuote(venue="Alpha", symbol="XYZ", bid=101.0, ask=100.2, size=50, fees_bps=5),
        VenueQuote(venue="Bravo", symbol="XYZ", bid=100.5, ask=99.4, size=10, fees_bps=5),
    ]

    opportunities = find_cross_venue_opportunities(quotes)

    assert len(opportunities) == 1
    opp: ArbitrageOpportunity = opportunities[0]

    assert opp.symbol == "XYZ"
    assert opp.buy.venue == "Bravo"
    assert opp.sell.venue == "Alpha"
    assert opp.size == 10

    # Edge should account for 5 bps fees on both legs
    assert opp.gross_edge == 101.0 - 99.4
    assert opp.net_edge == pytest.approx(1.4998, rel=1e-4)
    assert opp.edge_bps == pytest.approx((opp.net_edge / opp.buy.price) * 10_000)
    assert opp.expected_profit == pytest.approx(opp.net_edge * opp.size)


def test_skips_same_venue_and_thresholds():
    quotes = [
        VenueQuote(venue="Solo", symbol="ABC", bid=10.2, ask=10.0, size=5),
        VenueQuote(venue="Solo", symbol="ABC", bid=10.1, ask=9.95, size=5),
        VenueQuote(venue="Echo", symbol="ABC", bid=10.05, ask=10.04, size=5),
    ]

    # Without allowing same venue we should ignore the Solo-Solo spread
    assert find_cross_venue_opportunities(quotes) == []

    # With thresholds, only true edges should remain
    config = ArbitrageConfig(min_edge_bps=50, allow_same_venue=True, min_size=1)
    opportunities = find_cross_venue_opportunities(quotes, config=config)

    assert len(opportunities) == 1
    opp = opportunities[0]
    assert opp.buy.venue == "Solo"
    assert opp.sell.venue == "Solo"
    assert opp.edge_bps >= 50
    assert opp.size == 5


import pytest
