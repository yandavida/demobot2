from core.arbitrage.opportunity_space.builder import build_opportunity_space
from core.arbitrage import ArbitrageConfig, VenueQuote


def _simple_quotes_orderings():
    # Three venues for same symbol, with prices that allow multiple profitable pairs
    base = [
        VenueQuote(venue="A", symbol="TST", bid=101.0, ask=100.5, size=10, fees_bps=0),
        VenueQuote(venue="B", symbol="TST", bid=100.8, ask=100.4, size=8, fees_bps=0),
        VenueQuote(venue="C", symbol="TST", bid=101.2, ask=100.6, size=5, fees_bps=0),
    ]
    # produce two different input orders
    return [base, list(reversed(base)), [base[1], base[2], base[0]]]


def test_builder_is_deterministic_across_input_orders():
    config = ArbitrageConfig(min_edge_bps=0, allow_same_venue=False, min_size=1)

    outputs = []
    for quotes in _simple_quotes_orderings():
        opts = build_opportunity_space(quotes, config=config)
        # capture key summary for comparison: (buy_venue, sell_venue, buy_price, sell_price)
        summary = [(o.buy.venue, o.sell.venue, o.buy.price, o.sell.price) for o in opts]
        outputs.append(summary)

    # All outputs must be identical (deterministic ordering)
    assert len(outputs) >= 2
    first = outputs[0]
    for other in outputs[1:]:
        assert other == first


def test_builder_stable_ordering_and_provenance():
    config = ArbitrageConfig(min_edge_bps=0, allow_same_venue=False, min_size=1)
    quotes = _simple_quotes_orderings()[0]
    opts = build_opportunity_space(quotes, config=config)

    # Deterministic sort_key ensures first element is symbol 'TST' buy 'A' sell 'C' given our sort rules
    assert len(opts) > 0
    first = opts[0]
    assert first.symbol == "TST"
    # ensure provenance fields are present and consistent
    assert first.buy.price <= first.sell.price
    assert first.size > 0
    assert hasattr(first, "net_edge")
