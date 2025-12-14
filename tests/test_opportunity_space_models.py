from datetime import datetime, timezone

from core.arbitrage.opportunity_space import (
    CanonicalKey,
    EconomicsBreakdown,
    ExecutionOption,
    Provenance,
)


def test_canonical_key_as_tuple():
    key = CanonicalKey(
        symbol="XYZ",
        buy_venue="Alpha",
        sell_venue="Bravo",
        pricing_mode="executable_bid_ask",
        qty_rule="opp_size",
        fee_model="venue_bps",
    )

    assert key.as_tuple() == (
        "XYZ",
        "Alpha",
        "Bravo",
        "executable_bid_ask",
        "opp_size",
        "venue_bps",
    )


def test_provenance_construction():
    ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
    provenance = Provenance(
        as_of=ts,
        quote_refs={"buy": "Alpha:XYZ@ts", "sell": "Bravo:XYZ@ts"},
        fx_refs=None,
        notes=["seed"],
    )

    assert provenance.as_of == ts
    assert provenance.quote_refs["buy"] == "Alpha:XYZ@ts"
    assert provenance.fx_refs is None
    assert provenance.notes == ["seed"]


def test_economics_breakdown_from_prices():
    breakdown = EconomicsBreakdown.from_prices(
        buy_price=10.0,
        sell_price=10.5,
        quantity=3,
        fees_total=0.15,
    )

    assert breakdown.gross_edge == 0.5
    assert breakdown.notional == 30.0
    assert breakdown.profit == 1.35
    assert breakdown.net_edge == 0.45
    assert breakdown.edge_bps == 450.0


def test_execution_option_sort_key():
    key_a = CanonicalKey(
        symbol="ABC",
        buy_venue="X",
        sell_venue="Y",
        pricing_mode="mode",
        qty_rule="rule",
        fee_model="model",
    )
    key_b = CanonicalKey(
        symbol="DEF",
        buy_venue="X",
        sell_venue="Y",
        pricing_mode="mode",
        qty_rule="rule",
        fee_model="model",
    )

    provenance = Provenance(
        as_of=datetime(2024, 1, 1, tzinfo=timezone.utc),
        quote_refs={},
        fx_refs=None,
        notes=[],
    )
    economics = EconomicsBreakdown.from_prices(
        buy_price=1.0,
        sell_price=2.0,
        quantity=1.0,
        fees_total=0.0,
    )

    options = [
        ExecutionOption(
            key=key_b,
            opportunity_id="2",
            economics=economics,
            validation=None,
            readiness=None,
            provenance=provenance,
        ),
        ExecutionOption(
            key=key_a,
            opportunity_id="1",
            economics=economics,
            validation=None,
            readiness=None,
            provenance=provenance,
        ),
    ]

    options.sort(key=lambda opt: opt.sort_key())

    assert [opt.opportunity_id for opt in options] == ["1", "2"]
