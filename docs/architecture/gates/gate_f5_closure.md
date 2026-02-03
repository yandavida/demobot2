# Gate F5 — Hedging Layer Closure Note

**סטטוס:** CLOSED
**תאריך:** 2026-02-03
**תחום:** שכבת ה‑Hedging (פיצוי דלתא, רב‑מכשירי)

## מטרת השער
מטרת Gate F5 הייתה לאשר, לנעול ולמתעד את היכולת החישובית הדטרמיניסטית לשם חישוב פיצוי דלתא עבור תיקים חד‑מכשיריים ורב‑מכשיריים, כולל ממשקי חיבור לקריאה (contract surfaces / read‑model) ללא שינוי במדיניות מחירים/MTM.

## יכולות שננעלו
- פרימיטיבים של hedging: `delta_hedge`, `multi_delta_hedge`.
- מדיניות קנונית דטרמיניסטית לבחירת קבוצת המכשירים הנבחרת והקצאת כמויות כאשר קיימים קשרים/תיקונים מסוג tie.
- אכיפת SSOT של מדיניות נומרית: כל השוואות וסף‑השוואות משתמשות אך ורק ב‑`core.numeric_policy.DEFAULT_TOLERANCES` (אין שום eps מקומי קבוע בקוד).
- הפרדת `v2` contract surfaces ו‑read‑model מה‑pricing/MTM (אין חישוב מחירים בתוך ה‑read‑model; רק קריאה לפרימיטיבים הפשוטים מסודרת).
- קבוצה של בדיקות‑invariants שנכתבו בגישת tests‑first לאימות תכונות אלגבריות ודטרמיניסטיות.
- מנגנון Golden governance: `hedging_canonical` (v1) נוצר ונקבע כקובץ זהב להשוואת פלטים קנוניים.

## מדיניות מתמטית קנונית (תמצית)
- שגיאה/רזידואל של החיוב: 

  residual = dp - \sum_i (q_i * delta_i)

- בחירת קבוצת המכשירים הנבחרת S:

  S = \{ i : |delta_i| >= max_j |delta_j| - DEFAULT_TOLERANCES[MetricClass.DELTA].abs \}

  (כלומר, נבחרים כל המכשירים שגם הם בתוך מרחק ה‑absolute tolerance של המקסימום המוחלט — מבטיח קשרים/טיי רעיוניים בלי שימוש ב‑index tie‑breaking)

- הקצאה פרופורציונלית על S:

  q_i = dp * sign(delta_i) / \sum_{j\in S} |delta_j|

- תכונות חשובות:
  - Permutation invariance — תוצאה אינה תלויה בסדר הקלט.
  - Determinism — אין תלות בזמני קיר או מצב ריצה; אימות חוזר נותן פלטים זהים.
  - residual ≈ 0 בתוך הגבולות של `DEFAULT_TOLERANCES[MetricClass.DELTA]`.

## אי‑מטרות (Explicit Non-Goals)
- אין כיסוי או הנחות לגבי היקוף ל־gamma/vega hedging או פתרונות אופטימיזציה.
- לא נכללים נושאים של rebalancing בזמן אמת, ועדות עלויות ועמלות.
- לא נעשה אינטגרציה עם שכבת ה‑strategy/orkestration במשימה זו.

## ציות לממשל (Governance Compliance)
- שינוי תיעודי בלבד: קובץ תיעוד חדש שנוצר תחת `docs/architecture/gates`.
- אין שינויים בקוד בפרודקשן (core/** נשמר נקי מפניות ל‑api/**; אין שינויים ב‑schemas או בהוספת תלויות).
- CI ירוק ומעבר על בדיקות Golden/Pipeline/Architecture הושלם בהצלחה לפני פתיחת ה‑PR.
- קבלת ההחלטה על סגירה נעשתה על סמך tests‑first, בדיקות יחידה, ובדיקות זהירות של harness‑הזהב.

**ADR references (normative):**

- `docs/adr/adr-004-gate-b-gate-a-integration-guarantees.md` (Determinism / integration guarantees)
- `docs/adr/adr-005-institutional-default-bias.md` (Math / institutional defaults)
- `docs/architecture/adr/adr-008-numeric-policy-first-class-contract.md` (Numeric policy as first-class contract)
- `docs/architecture/adr/adr-010-golden-regression-governance.md` (Golden regression governance)
- `docs/architecture/adr/adr-012-ci-enforcement-golden-regression.md` (CI enforcement for golden regression)
- `docs/architecture/adr/adr-014-deterministic-event-time-and-replay.md` (Deterministic event time & replay)

## נקודות הרחבה / שערים עתידיים (לא המלצה, אלא הכנה פורמלית)
- הרחבה ל‑multi‑target hedging (gamma/vega multi‑objective) — ידרוש ADR מוצהר לשינוי מדיניות הנומרית והוספת מטרות אופטימיזציה.
- הוספת מגבלות עסקיות (מסחריות, כמותיות) ושילוב עלות־טרנזקציה — ידרוש Gate נפרד.
- אינטגרציה עם שכבת ה‑strategy (רתימת hedging כחלק מזרימת ההחלטות) — יידרש ADR ועבודה ארכיטקטונית נוספת.

## סיכום סופי
Gate F5 — CLOSED and LOCKED.
הפונקציות והמדיניות המוגדרות לעיל מהוות את היסוד הקנוני לחישובי דלתא בסביבת V2. ניתן להמשיך משלב זה לפרויקטים תלויי‑hedging (כגון FX deals ו‑Theoretical MTM), בתנאי שכל שינוי מדיניות יעבור ADR ויתנהל תחת מסלול שערים רשמי.
