# V2-F.1 Finance Math Contracts

## A) Greeks Canonical Units

- **Vega_1pct**: Change in present value (dPV) when implied volatility increases by 0.01 (1%).
- **Theta_1d**: Change in present value for a decrease of 1 day to expiry:  PV(T-1/365) - PV(T). Reported as change per day (usually negative for long options).
- **Portfolio aggregation**: All greeks are per-contract. Aggregation is performed by multiplying by quantity and contract_multiplier.
- **Scaling**: All greeks and P&L are per-contract/unit. Portfolio/position scaling is always qty * contract_multiplier.
- **Deterministic outputs**: All pricing and greeks outputs are deterministic for given inputs.
- **Single Source of Truth (SoT)**: Unit normalization (vega/theta) is performed only in `core/pricing/units.py` (`to_canonical_greeks`). No distributed normalization elsewhere.
- **Gate rule**: Any change to math contracts requires updating audit tests and this document.

## B) FX Forward P&L Convention

- **BUY_BASE (long base)**:  P&L_quote = notional_base * (spot - forward)
- **SELL_BASE (short base)**: P&L_quote = -notional_base * (spot - forward)
- **Invariant**: If spot == forward, then P&L == 0
- **Sign convention**: BUY_BASE and SELL_BASE are always exact opposites for the same notional and rates.

## C) American Options Note

- **Scope**: Only European options are supported in V2-F.1. American options are not implemented; any attempt to price them must raise a clear error (NotImplementedError or ValueError with 'unsupported' or 'American' in the message).
- **Placeholder**: Support for early exercise (binomial / Bjerksund–Stensland) is planned for a future release. Placeholder tests and documentation are provided.
