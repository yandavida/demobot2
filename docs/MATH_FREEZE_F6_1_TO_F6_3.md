# Mathematical Freeze: F6.1–F6.3

## Scope frozen
- **F6.1:** Position lifecycle invariants & event/state model
- **F6.2:** Theoretical PnL (`compute_position_pnl`) + attribution identities
- **F6.3:** Portfolio breakdown aggregation rules (pure sum, fsum, permutation-invariant)

## Non-negotiable invariants
- Determinism
- Permutation invariance
- Additivity: total == sum(components)+residual
- Portfolio == sum(positions) for total + each component
- Missing IV ⇒ vega_pnl=0 + note "dIV=0"
- No institutional conventions in these layers

## Change protocol
כל שינוי מתמטי דורש:
1. הוספת/עדכון invariant test שמוכיח את הדרישה
2. PR נפרד עם תיאור “Math Change Request”
3. אין שינוי ללא CI ירוק + review ידני
