# V2-F.5 Backtest Engine v1 — Contract & Design

## Scope v1
- Deterministic timeline replay of MarketSnapshots
- Inputs: positions, market_timeline (MarketSnapshot), scenario axes, use_cache
- Outputs: per-timepoint summaries (risk, scenario, PnL)
- Determinism: same inputs → same outputs (ordering, hashing)
- Out of scope: execution realism, DB/event store, live feed, slippage/fees, portfolio persistence
- Composes with: F2 (RiskSnapshot), F3 (Scenario), F4 (MarketSnapshot)

## Contracts
- BacktestRequest: positions, market_timeline, spot_shocks, vol_shocks, use_cache
- BacktestPoint: asof, risk_snapshot, scenario_hash_key, pnl_at_zero_shock
- BacktestResult: points, run_hash_key

## Determinism Guarantees
- Timeline must be ordered by asof (non-decreasing)
- run_hash_key includes: positions, timeline fingerprints, axes, model_version

## Out of Scope
- No execution realism (F6)
- No DB/event store
- No market adapters (already in F4)
- No optimization/vectorization

---

# See also:
- V2-F.2 RiskSnapshot
- V2-F.3 Scenario Engine
- V2-F.4 MarketSnapshot
