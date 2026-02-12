"""Gate F8.2 invariant tests: FX Forward MTM close-out PV (bank-standard).

Tests MUST pass before implementation is considered complete.
All formulas follow ISA close-out valuation rule.
"""
import datetime

import pytest

from core.pricing.fx import types as fx_types
from core.pricing.fx import forward_mtm
from core import numeric_policy


# Helpers for tolerance-aware comparisons
def approx_zero(value: float) -> bool:
    """Check if value is approximately zero using PRICE tolerances."""
    tol = numeric_policy.DEFAULT_TOLERANCES[numeric_policy.MetricClass.PRICE]
    return abs(value) <= tol.abs


def approx_equal(a: float, b: float) -> bool:
    """Check if two values are approximately equal using PRICE tolerances."""
    tol = numeric_policy.DEFAULT_TOLERANCES[numeric_policy.MetricClass.PRICE]
    abs_diff = abs(a - b)
    if abs_diff <= tol.abs:
        return True
    rel_diff = abs_diff / max(abs(a), abs(b), 1e-9)
    return rel_diff <= tol.rel


# Test 1: Close-out parity (zero PV when K == F_mkt)
def test_closeout_parity_zero_pv_when_forward_equals_market():
    """If K == F_mkt, then PV must be approximately zero."""
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 5, 12)
    
    # Setup: S=1.10, DFd=0.99, DFf=0.98
    # Then F_mkt = 1.10 * 0.98 / 0.99 = 1.088888...
    # Set K = F_mkt
    S = 1.10
    DFd = 0.99
    DFf = 0.98
    F_mkt = S * DFf / DFd
    K = F_mkt
    
    contract = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=1_000_000.0,
        forward_date=maturity,
        forward_rate=K,
        direction="receive_foreign_pay_domestic"
    )
    
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=S,
        df_domestic=DFd,
        df_foreign=DFf
    )
    
    result = forward_mtm.price_fx_forward(as_of, contract, snapshot, None)
    
    assert result.as_of_ts == as_of
    assert approx_zero(result.pv), f"Expected PV ≈ 0, got {result.pv}"


# Test 2: Linearity (PV scales linearly with notional)
def test_linearity_pv_scales_with_notional():
    """PV must scale linearly with foreign notional."""
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 5, 12)
    
    S = 1.10
    K = 1.08
    DFd = 0.99
    DFf = 0.98
    
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=S,
        df_domestic=DFd,
        df_foreign=DFf
    )
    
    # Notional 1M
    contract_1m = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=1_000_000.0,
        forward_date=maturity,
        forward_rate=K,
        direction="receive_foreign_pay_domestic"
    )
    result_1m = forward_mtm.price_fx_forward(as_of, contract_1m, snapshot, None)
    
    # Notional 2M (double)
    contract_2m = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=2_000_000.0,
        forward_date=maturity,
        forward_rate=K,
        direction="receive_foreign_pay_domestic"
    )
    result_2m = forward_mtm.price_fx_forward(as_of, contract_2m, snapshot, None)
    
    # PV should double
    assert approx_equal(result_2m.pv, 2.0 * result_1m.pv), \
        f"Linearity violated: 2x notional should give 2x PV, got {result_2m.pv} vs 2*{result_1m.pv}"


# Test 3: Symmetry (flipping direction flips PV sign)
def test_symmetry_flip_direction_flips_pv_sign():
    """Flipping contract direction must flip PV sign (magnitude equal within tolerances)."""
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 5, 12)
    
    S = 1.10
    K = 1.08
    DFd = 0.99
    DFf = 0.98
    Nf = 1_000_000.0
    
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=S,
        df_domestic=DFd,
        df_foreign=DFf
    )
    
    # Direction 1: receive foreign, pay domestic
    contract_receive = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=Nf,
        forward_date=maturity,
        forward_rate=K,
        direction="receive_foreign_pay_domestic"
    )
    result_receive = forward_mtm.price_fx_forward(as_of, contract_receive, snapshot, None)
    
    # Direction 2: pay foreign, receive domestic (opposite)
    contract_pay = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=Nf,
        forward_date=maturity,
        forward_rate=K,
        direction="pay_foreign_receive_domestic"
    )
    result_pay = forward_mtm.price_fx_forward(as_of, contract_pay, snapshot, None)
    
    # PVs should be negatives of each other
    assert approx_equal(result_receive.pv, -result_pay.pv), \
        f"Symmetry violated: PVs should be negatives, got {result_receive.pv} and {result_pay.pv}"


# Test 4: DF edge case (DFd=DFf=1 implies PV = Nf*(S-K) with correct sign)
def test_df_edge_case_no_discounting():
    """If DFd=DFf=1, then PV = Nf*(S-K) with correct sign by direction."""
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 2, 12)  # Same day, no discount
    
    S = 1.10
    K = 1.08
    Nf = 1_000_000.0
    DFd = 1.0
    DFf = 1.0
    
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=S,
        df_domestic=DFd,
        df_foreign=DFf
    )
    
    contract = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=Nf,
        forward_date=maturity,
        forward_rate=K,
        direction="receive_foreign_pay_domestic"
    )
    
    result = forward_mtm.price_fx_forward(as_of, contract, snapshot, None)
    
    # Expected: PV = Nf * (S - K) = 1,000,000 * (1.10 - 1.08) = 20,000
    expected_pv = Nf * (S - K)
    assert approx_equal(result.pv, expected_pv), \
        f"DF=1 edge case failed: expected {expected_pv}, got {result.pv}"


# Test 5: Determinism (repeated calls yield identical results)
def test_determinism_repeated_calls_identical():
    """Repeated calls with same inputs must yield structurally identical PricingResult."""
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 5, 12)
    
    S = 1.10
    K = 1.08
    DFd = 0.99
    DFf = 0.98
    Nf = 1_000_000.0
    
    contract = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=Nf,
        forward_date=maturity,
        forward_rate=K,
        direction="receive_foreign_pay_domestic"
    )
    
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=S,
        df_domestic=DFd,
        df_foreign=DFf
    )
    
    result1 = forward_mtm.price_fx_forward(as_of, contract, snapshot, None)
    result2 = forward_mtm.price_fx_forward(as_of, contract, snapshot, None)
    
    assert result1 == result2, "Determinism violated: identical inputs produced different results"
    assert result1.pv == result2.pv


# Test 6: Non-finite rejection (NaN/Inf in required inputs)
def test_non_finite_rejection():
    """Any NaN or Inf in required inputs must raise ValueError deterministically."""
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 5, 12)
    
    # NaN in contract forward_rate (caught at construction)
    with pytest.raises(ValueError):
        fx_types.FXForwardContract(
            base_currency="USD",
            quote_currency="EUR",
            notional=1_000_000.0,
            forward_date=maturity,
            forward_rate=float("nan"),
            direction="receive_foreign_pay_domestic"
        )
    
    # Inf in snapshot df_domestic (caught at construction)
    with pytest.raises(ValueError):
        fx_types.FxMarketSnapshot(
            as_of_ts=as_of,
            spot_rate=1.10,
            df_domestic=float("inf"),
            df_foreign=0.98
        )


# Test 7: Missing market inputs (missing spot or DF)
def test_missing_market_inputs_deterministic_failure():
    """Missing required market inputs (spot or DFs) must raise ValueError."""
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 5, 12)
    
    contract = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=1_000_000.0,
        forward_date=maturity,
        forward_rate=1.08,
        direction="receive_foreign_pay_domestic"
    )
    
    # Missing df_domestic
    snapshot_missing_dfd = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=1.10,
        df_foreign=0.98
    )
    
    with pytest.raises(ValueError, match="df_domestic.*required|missing"):
        forward_mtm.price_fx_forward(as_of, contract, snapshot_missing_dfd, None)
    
    # Missing df_foreign
    snapshot_missing_dff = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=1.10,
        df_domestic=0.99
    )
    
    with pytest.raises(ValueError, match="df_foreign.*required|missing"):
        forward_mtm.price_fx_forward(as_of, contract, snapshot_missing_dff, None)
    
    # Missing forward_rate
    contract_missing_k = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=1_000_000.0,
        forward_date=maturity,
        direction="receive_foreign_pay_domestic"
    )
    
    snapshot_valid = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=1.10,
        df_domestic=0.99,
        df_foreign=0.98
    )
    
    with pytest.raises(ValueError, match="forward_rate.*required|missing"):
        forward_mtm.price_fx_forward(as_of, contract_missing_k, snapshot_valid, None)
    
    # Missing direction
    contract_missing_dir = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=1_000_000.0,
        forward_date=maturity,
        forward_rate=1.08
    )
    
    with pytest.raises(ValueError, match="direction.*required|missing"):
        forward_mtm.price_fx_forward(as_of, contract_missing_dir, snapshot_valid, None)


# Test 8: Architecture firewall sanity
def test_no_api_imports_in_forward_mtm():
    """Ensure no forbidden imports (core must not import api)."""
    import inspect
    src = inspect.getsource(forward_mtm)
    assert "import api" not in src
    assert "from api" not in src


# Test 9: Formula consistency (A) and (B) match
def test_formula_consistency_a_and_b():
    """Both formula variants (A) and (B) must yield PV within tolerances."""
    as_of = datetime.datetime(2026, 2, 12, 17, 0, 0)
    maturity = datetime.date(2026, 5, 12)
    
    S = 1.10
    K = 1.08
    Nf = 1_000_000.0
    DFd = 0.99
    DFf = 0.98
    
    # Formula A: PV = Nf * (S * DFf - K * DFd)
    pv_a = Nf * (S * DFf - K * DFd)
    
    # Formula B: PV = Nf * DFd * (F_mkt - K), where F_mkt = S * DFf / DFd
    F_mkt = S * DFf / DFd
    pv_b = Nf * DFd * (F_mkt - K)
    
    assert approx_equal(pv_a, pv_b), \
        f"Formula consistency check failed: A={pv_a}, B={pv_b}"
    
    # Now verify implementation returns the same value
    contract = fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="EUR",
        notional=Nf,
        forward_date=maturity,
        forward_rate=K,
        direction="receive_foreign_pay_domestic"
    )
    
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of,
        spot_rate=S,
        df_domestic=DFd,
        df_foreign=DFf
    )
    
    result = forward_mtm.price_fx_forward(as_of, contract, snapshot, None)
    
    assert approx_equal(result.pv, pv_a), \
        f"Implementation PV doesn't match formula A: impl={result.pv}, A={pv_a}"
    assert approx_equal(result.pv, pv_b), \
        f"Implementation PV doesn't match formula B: impl={result.pv}, B={pv_b}"
