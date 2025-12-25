# V2-F.4 MarketData Integration v1 — Contract & Design

## MarketSnapshot v1
- Contains:
  - `spots`: dict[str, float]
  - `vols`: dict[str, float]
  - `rates`: dict[str, float]
  - `divs`: dict[str, float]
  - `fx_spots`: dict[str, float]
  - `fx_forwards`: dict[str, float]
  - `asof`: datetime (ISO string or datetime, per repo convention)

## Determinism Rules
- All keys sorted (dicts, quote lists)
- Canonical JSON for fingerprinting
- No implicit current time (asof must be explicit)

## Validation Rules
- Required: spot+vol for each symbol in positions (BS path)
- divs: missing => treat as 0.0 only (documented)
- rates: missing => error (unless repo has explicit default)
- Duplicates for (kind, key): error

## Out of Scope
- No curves, swaps, advanced surfaces
- No live feed, DB, event store
- No FastAPI wiring

---

# See also:
- V2-F.3 Scenario Engine
- F1 canonical pricing path
