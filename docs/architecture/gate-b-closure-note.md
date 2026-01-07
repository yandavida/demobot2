## Gate B — מסמך סגירה מוסדי (Institutional Firewall)

סיכום: Gate B מוגדר כגבול פקודות מוסדי (Command Boundary) המחייב איסור שינוי והתערבות ברמת האינטרנט/הקוד והסכימות. מסמך זה מתעד רשמית את ההקף, המגבלות, וההצהרות הנדרשות לצורך נעילה ארגונית.

**Scope (מה כולל / מה לא):**
- **כולל:** חוקים מוסדיים להגבלת כניסת פקודות חיצוניות דרך ממשק Gate B; סדרי בדיקה ו־quality gates להבטחת אי־שינוי במדיניות ההכנסה; מסמכי ממשק (contract) כערכים בלתי־נתיכים מבחינת היחסים הבין־מערכתיים.
- **לא כולל:** אין שינוי בפונקציונליות עצמה של רכיבי Finance, Read Models, Orchestration, או סכימות persistency. אין שינויים בקוד המפעיל את Gate A או רכיבים פנימיים אחרים.

**Non‑Negotiables (Locked):**
- אין לשנות את סכימת persistency המופעלת כיום (core/v2/sqlite_schema.py) — סכמה מוסכמת ונעולה.
- אין להוסיף לוגיקה חדשה ב־Orchestration, Finance או Read Models הקשורים ל־Gate B.
- כל חריגה מהסעיפים הללו מחייבת אישור ADR פורמלי וחתימת שלוש בעלי עניין (Architecture, Compliance, Product).

**Deliverables שבוצעו בפועל:**
- מיפוי חד‑משמעי של בקשות API ל־command envelope בקצה Gate B.
- החלת מדיניות סדרי בדיקה (validation precedence) ו־ErrorEnvelope קנוני ברמת ה־API.
- בדיקות יחידה אינדקסיות ובדיקות אינטגרציה תקינות אשר וידאו כי שינוי התיעוד אינו משנה התנהגות קיימת.

**Canonical failure precedence (סדר אימות / שגיאות):**
1. אימות `schema_version` — יש לאמת ולהחזיר שגיאה תואמת אם `schema_version` אינו נתמך. זהו שלב ראשון וחיוני ומחייב דחייה מידית של הבקשה אם נכשל.
2. אימות סכמטי/פורמלי של payload — בעת מצב `strict` בקשות יידחו על אי־התאמה. במצב `lenient` ייתכן קבלה עם אזהרה, אך ללא שינוי סכמה.
3. בדיקות legality / business rules — הן מוחלות לאחר אימות הסכמה (schema acceptance) אך לפני ביצוע side‑effects או persistency.
4. במידה ובוצע סכסוך אירועים ב־store (EventConflict) — יש להעלות את החריגה באופן חיצוני (exceptions out) ולמנוע כל שינוי סטייט מוסדי עקבי.

**Institutional default bias:**
- ברירת המחדל המוסדית היא **שמרנות**: `strict` validation והעדפת דחיית בקשה על פני קבלת נתונים לא־מאומתים. שחרור ל־`lenient` מחייב החלטה רשמית ונשלטת.

**Evidence (quality gates):**
- ריצת lint סטנדרטית: `ruff check .` — ללא שגיאות על קוד הפרויקט הנוגע.
- קומפילציה בייט‑קוד: `python -m compileall .` — ללא שגיאות סינטקס.
- כל המבחנים: `pytest -q` — כל המבחנים עוברים באחוז הכיסוי הנוכחי לפני הסגירה.
- כל ראיה (פלטים של ריצות אלו) חייבת להיכלל ב־PR כמסמך ראיה.

**Freeze declaration (מה ננעל ואסור לשנות):**
- Gate B API contract וה־ErrorEnvelope הקנוני — ננעלים לחלוטין.
- סדרי אימות ו־precedence כמפורט לעיל — ננעלים.
- אין לשנות סכימות persistency, orchestrator behavior או מדיניות exception propagation ללא ADR חדש.

**Deferred items:**
- B7 (אפשרות לשדרוג מאוחר של taxonomy או הרחבת validation modes) — נדחה להחלטה ארגונית נפרדת.
- איחוד טקסונומיית שגיאות (B4 error taxonomy unification) — מקובל כיעד עתידי אך דורש ADR ומשאבי אינטגרציה; לא יתבצע במסגרת סגירה זו.

**Recommended next step (בחירה מודעת בלבד):**
- לקבוע מועדי בחינה תקופתיים (quarterly review) להערכת השימוש ב־`lenient` ולקבל החלטות מבוססות נתונים לפני כל שחרור שינוי מדיניות.

**ADR references (normative):**
- ADR-001
- ADR-002
- ADR-003
- ADR-004
- ADR-005

הדגשה: ה־ADRs המצוינים הם מסמכים נורמטיביים (normative) ומעצבים את פרשנות המסמך הזה; כל ויתור או שינוי מחייב עדכון ADR מתאים.

**NO CHANGES TO CODE**
- אין לשנות קבצי Python, סכימות נתונים, להוסיף בדיקות חדשות או לבצע refactors כחלק מסגירה זו.

**Validation rules (לפני commit):**
הריצו את הפקודות הבאות באופן מקומי לאימות לפני פתיחת ה־PR:
```bash
ruff check .
python -m compileall .
pytest -q
```

חתימת סגירה:
Gate B נסגרה באופן מוסדי. כל שינוי הקשור ל־Gate B, כפי שמוגדר במסמך זה, אסור עד אשר יתקבל ADR חדש וחתימות האחראים.

***
מסמך זה נוצר לצורך נעילה ותיעוד מוסדי בלבד; אין בו קוד, TODOs או דוגמאות API.
