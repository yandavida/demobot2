"""
Gate F8.3 — DF Policy Lock

This test suite enforces that FX MTM pricing consumes discount factors
as immutable inputs and does not construct them internally.

Any attempt to introduce rate-based DF construction must go through
a new Gate and governance approval.
"""
import datetime
import inspect

import pytest

from core.pricing.fx import forward_mtm
from core.pricing.fx import types as fx_types
from core import numeric_policy


# ============================================================================
# Test 1️⃣: DF Mandatory
# ============================================================================

def test_missing_df_domestic_raises_value_error():
    """Missing df_domestic must raise ValueError."""
    as_of_ts = datetime.datetime(2026, 1, 15, 16, 0, 0, tzinfo=datetime.timezone.utc)
    
    contract = fx_types.FXForwardContract(
        base_currency="EUR",
        quote_currency="USD",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 4, 15),
        forward_rate=1.10,
        direction="receive_foreign_pay_domestic"
    )
    
    # Missing df_domestic (None)
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=1.08,
        df_domestic=None,  # Missing
        df_foreign=0.998
    )
    
    with pytest.raises(ValueError, match="df_domestic is required"):
        forward_mtm.price_fx_forward(as_of_ts, contract, snapshot, None)


def test_missing_df_foreign_raises_value_error():
    """Missing df_foreign must raise ValueError."""
    as_of_ts = datetime.datetime(2026, 1, 15, 16, 0, 0, tzinfo=datetime.timezone.utc)
    
    contract = fx_types.FXForwardContract(
        base_currency="EUR",
        quote_currency="USD",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 4, 15),
        forward_rate=1.10,
        direction="receive_foreign_pay_domestic"
    )
    
    # Missing df_foreign (None)
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=1.08,
        df_domestic=0.995,
        df_foreign=None  # Missing
    )
    
    with pytest.raises(ValueError, match="df_foreign is required"):
        forward_mtm.price_fx_forward(as_of_ts, contract, snapshot, None)


# ============================================================================
# Test 2️⃣: DF Positivity
# ============================================================================

def test_zero_df_domestic_raises_value_error():
    """df_domestic = 0 must raise ValueError (division by zero protection)."""
    as_of_ts = datetime.datetime(2026, 1, 15, 16, 0, 0, tzinfo=datetime.timezone.utc)
    
    contract = fx_types.FXForwardContract(
        base_currency="EUR",
        quote_currency="USD",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 4, 15),
        forward_rate=1.10,
        direction="receive_foreign_pay_domestic"
    )
    
    # Non-positive DF must be rejected at boundary construction
    with pytest.raises(ValueError, match="df_domestic must be positive"):
        snapshot = fx_types.FxMarketSnapshot(
            as_of_ts=as_of_ts,
            spot_rate=1.08,
            df_domestic=0.0,  # Zero
            df_foreign=0.998
        )
        forward_mtm.price_fx_forward(as_of_ts, contract, snapshot, None)


def test_negative_df_domestic_raises_value_error():
    """df_domestic < 0 must raise ValueError (invalid discount factor)."""
    as_of_ts = datetime.datetime(2026, 1, 15, 16, 0, 0, tzinfo=datetime.timezone.utc)
    
    contract = fx_types.FXForwardContract(
        base_currency="EUR",
        quote_currency="USD",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 4, 15),
        forward_rate=1.10,
        direction="receive_foreign_pay_domestic"
    )
    
    with pytest.raises(ValueError, match="df_domestic must be positive"):
        # Negative df_domestic (economically invalid)
        snapshot = fx_types.FxMarketSnapshot(
            as_of_ts=as_of_ts,
            spot_rate=1.08,
            df_domestic=-0.995,  # Negative
            df_foreign=0.998
        )
        forward_mtm.price_fx_forward(as_of_ts, contract, snapshot, None)


def test_negative_df_foreign_raises_value_error():
    """df_foreign < 0 must raise ValueError (invalid discount factor)."""
    as_of_ts = datetime.datetime(2026, 1, 15, 16, 0, 0, tzinfo=datetime.timezone.utc)
    
    contract = fx_types.FXForwardContract(
        base_currency="EUR",
        quote_currency="USD",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 4, 15),
        forward_rate=1.10,
        direction="receive_foreign_pay_domestic"
    )
    
    with pytest.raises(ValueError, match="df_foreign must be positive"):
        # Negative df_foreign
        snapshot = fx_types.FxMarketSnapshot(
            as_of_ts=as_of_ts,
            spot_rate=1.08,
            df_domestic=0.995,
            df_foreign=-0.998  # Negative
        )
        forward_mtm.price_fx_forward(as_of_ts, contract, snapshot, None)


# ============================================================================
# Test 3️⃣: Deterministic Failure
# ============================================================================

def test_deterministic_failure_on_missing_df():
    """Calling pricing twice with missing DF must produce identical exceptions."""
    as_of_ts = datetime.datetime(2026, 1, 15, 16, 0, 0, tzinfo=datetime.timezone.utc)
    
    contract = fx_types.FXForwardContract(
        base_currency="EUR",
        quote_currency="USD",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 4, 15),
        forward_rate=1.10,
        direction="receive_foreign_pay_domestic"
    )
    
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=1.08,
        df_domestic=None,  # Missing
        df_foreign=0.998
    )
    
    # First call
    exc1 = None
    try:
        forward_mtm.price_fx_forward(as_of_ts, contract, snapshot, None)
    except Exception as e:
        exc1 = e
    
    # Second call
    exc2 = None
    try:
        forward_mtm.price_fx_forward(as_of_ts, contract, snapshot, None)
    except Exception as e:
        exc2 = e
    
    # Both must raise same exception type
    assert exc1 is not None
    assert exc2 is not None
    assert type(exc1) is type(exc2)
    
    # Both must have identical message (deterministic)
    assert str(exc1) == str(exc2)


# ============================================================================
# Test 4️⃣: No Rate → DF Construction
# ============================================================================

def test_no_rate_to_df_construction_in_source():
    """Verify that price_fx_forward source does not contain rate/curve construction logic."""
    source = inspect.getsource(forward_mtm.price_fx_forward)
    
    # Forbidden patterns that indicate rate → DF construction
    forbidden_patterns = [
        "exp(",
        "log(",
        "rate",
        "zero_rate",
        "zero_rates",
        "compounding",
        "daycount",
        "year_fraction",
        "curve",
        "yield",
        "interpolation",
        "bootstrap",
    ]
    
    for pattern in forbidden_patterns:
        if pattern == "rate":
            continue
        assert pattern not in source, \
            f"Forbidden pattern '{pattern}' found in price_fx_forward source. " \
            f"This suggests rate → DF construction, which violates F8.3 DF policy lock."
    
    # The word "rate" should only appear in forward_rate context, not in DF construction
    # We allow "forward_rate" but not standalone "rate" variable construction
    lines = source.split("\n")
    for line in lines:
        # Skip comments and forward_rate references
        if "#" in line:
            line = line.split("#")[0]
        if "forward_rate" in line:
            continue
        if "spot_rate" in line:
            continue
        
        # Check for suspicious standalone "rate" usage
        if " rate " in line or " rate=" in line or "rate)" in line:
            # Allow: "forward_rate", "spot_rate"
            if "forward_rate" not in line and "spot_rate" not in line:
                pytest.fail(
                    f"Suspicious 'rate' usage in line: {line.strip()}. "
                    f"This may indicate rate → DF construction."
                )


# ============================================================================
# Test 5️⃣: No Curve Imports
# ============================================================================

def test_no_curve_imports_in_forward_mtm_module():
    """Verify that forward_mtm module does not import curve/rates/lifecycle modules."""
    source = inspect.getsource(forward_mtm)
    
    # Forbidden import patterns
    forbidden_imports = [
        "curve",
        "rates",
        "yield",
        "interpolation",
        "lifecycle",
        "strategy",
        "zero_curve",
        "discount_curve",
    ]
    
    for forbidden in forbidden_imports:
        assert forbidden not in source, \
            f"Forbidden import '{forbidden}' found in forward_mtm module. " \
            f"This violates F8.3 isolation boundary."


def test_no_curve_imports_in_types_module():
    """Verify that types module does not import curve/rates/lifecycle modules."""
    source = inspect.getsource(fx_types)
    
    forbidden_imports = [
        "curve",
        "rates",
        "yield",
        "interpolation",
        "lifecycle",
        "strategy",
    ]
    
    for forbidden in forbidden_imports:
        assert forbidden not in source, \
            f"Forbidden import '{forbidden}' found in types module. " \
            f"This violates F8.3 isolation boundary."


# ============================================================================
# Test 6️⃣: No Snapshot Field Drift
# ============================================================================

def test_no_rate_fields_on_snapshot():
    """Verify that FxMarketSnapshot does not expose rate fields (only DF fields)."""
    as_of_ts = datetime.datetime(2026, 1, 15, 16, 0, 0, tzinfo=datetime.timezone.utc)
    
    snapshot = fx_types.FxMarketSnapshot(
        as_of_ts=as_of_ts,
        spot_rate=1.08,
        df_domestic=0.995,
        df_foreign=0.998
    )
    
    # Forbidden fields that would indicate rate → DF construction drift
    forbidden_fields = [
        "zero_rate",
        "zero_rates",
        "rate_domestic",
        "rate_foreign",
        "discount_rate_domestic",
        "discount_rate_foreign",
        "yield_domestic",
        "yield_foreign",
    ]
    
    for field in forbidden_fields:
        assert not hasattr(snapshot, field), \
            f"FxMarketSnapshot exposes field '{field}', which violates DF-only policy. " \
            f"Only discount factors (df_domestic, df_foreign) are allowed."


# ============================================================================
# Test 7️⃣: Numeric Policy
# ============================================================================

def test_numeric_policy_available():
    """Verify that DEFAULT_TOLERANCES is accessible and contains PRICE tolerances."""
    assert hasattr(numeric_policy, "DEFAULT_TOLERANCES")
    assert hasattr(numeric_policy, "MetricClass")
    
    # Verify PRICE class exists
    assert hasattr(numeric_policy.MetricClass, "PRICE")
    
    # Verify tolerance structure
    price_tol = numeric_policy.DEFAULT_TOLERANCES[numeric_policy.MetricClass.PRICE]
    assert hasattr(price_tol, "abs")
    assert hasattr(price_tol, "rel")
    
    # Verify tolerances are finite and positive
    assert price_tol.abs > 0
    assert price_tol.rel > 0
    assert price_tol.abs < 1.0  # Sanity check
    assert price_tol.rel < 1.0  # Sanity check


def test_no_hardcoded_tolerances_in_this_file():
    """Verify that this test file does not contain hard-coded tolerance values."""
    source = inspect.getsource(inspect.getmodule(test_no_hardcoded_tolerances_in_this_file))
    
    # Check for suspicious numeric literals that might be tolerances
    # Allow: 0.0, 1.0, -1.0, integer literals, dates
    # Forbid: small decimals like 1e-6, 0.001, etc. in comparison context
    
    lines = source.split("\n")
    for i, line in enumerate(lines, 1):
        # Skip comments
        if "#" in line:
            code_part = line.split("#")[0]
        else:
            code_part = line
        
        # Skip this test itself (meta) and its list definitions
        if "test_no_hardcoded_tolerances" in line:
            continue
        if "suspicious_patterns" in line:
            continue
        # Skip string literals in list definitions (quoted patterns)
        if code_part.strip().startswith('"') and code_part.strip().endswith('",'):
            continue
        if code_part.strip().startswith('"') and code_part.strip().endswith('"'):
            continue
        
        # Check for suspicious tolerance patterns
        suspicious_patterns = [
            "1e-6",
            "1e-8",
            "0.001",
            "0.0001",
            "1e-4",
            "1e-9",
            "0.00001",
        ]
        
        for pattern in suspicious_patterns:
            if pattern in code_part:
                # Allow in date/time literals
                if "datetime" in code_part or "date(" in code_part:
                    continue
                # Allow in notional/rate values
                if "notional" in code_part or "forward_rate" in code_part or "spot_rate" in code_part:
                    continue
                # Allow in df values (e.g., 0.995, 0.998)
                if "df_" in code_part:
                    continue
                
                pytest.fail(
                    f"Line {i}: Hard-coded tolerance suspected: {line.strip()}. "
                    f"Use numeric_policy.DEFAULT_TOLERANCES instead."
                )
