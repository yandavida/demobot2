# V2-F.3 Scenario Engine v1 (Full Repricing) — Contract & Design

## Scope (v1)
- Full repricing engine for scenario analysis (no greeks approximation)
- Axes:
  - `spot_shocks`: percentage shocks (e.g. -0.2 means -20%)
  - `vol_shocks`: absolute volatility bumps Δσ (e.g. +0.05)
- Output: flat list of `ScenarioPoint` (deterministic ordering)
- Caching: in-memory, deterministic, stable hash key (inputs → key)

## Explicitly OUT of Scope (v1)
- No time axis/theta decay
- No execution/market realism
- No market data adapters (F4)

## Determinism Rules
- All outputs must be deterministic for identical inputs
- Permutation invariance: positions order does not affect result
- Market input dicts must be sorted for hashing
- Axes order is locked: spot_shocks outer, vol_shocks inner

## Contract
- `spot_shocks`: list of float, interpreted as percentage (e.g. 0.1 = +10%)
- `vol_shocks`: list of float, interpreted as absolute Δσ (e.g. 0.05 = +5 vol points)

## Cache Key Composition
- Deterministic hash of:
  - Sorted, normalized positions payload (json-serializable)
  - Market inputs (sorted keys)
  - Axes arrays
  - Model version string (e.g. "scenario_v1_fullrepricing")

## File Structure
- `core/scenario/schemas.py`: Scenario models
- `core/scenario/cache.py`: Cache interface & in-memory impl
- `core/scenario/engine.py`: Hashing, engine logic

---

# See also:
- V2-F.2 RiskSnapshot contract
- F1 canonical pricing path
