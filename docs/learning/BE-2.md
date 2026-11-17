# BE-2: Platform helpers (Part A) — Berlin dates, euro formatting, error codes

## What I built
Three small helper files that the whole backend will use. They have no database
and no web code, so they are easy to test.

## The files
- **errors.py** — one list of all error codes (like PERIOD_LOCKED, NOT_FOUND)
  and which HTTP status each one gets (409, 404 …). `DomainError` is the one
  exception every business rule raises: code + message + which field is wrong.
  → The frontend always gets errors in the same shape.

- **clock.py** — "today" and month calculations in Berlin time.
  The server runs in UTC, so 23:30 UTC on 3 Nov is already 4 Nov in Berlin.
  Months are stored as their first day (2026-10-01) and sent as "2026-10".
  `parse_month` rejects bad input like "2026-13" with a VALIDATION_ERROR.

- **money.py** — turns cents into German euros: 123456 → "1.234,56 €".
  Money is stored as whole cents, because floats give rounding errors
  (0.1 + 0.2 is not exactly 0.3).

## What I learned
- Pure function → same input always gives the same output, no database or clock inside.
- Time zones → always decide which time zone "today" means; servers use UTC.
- Summer time → Berlin is UTC+1 in winter, UTC+2 in summer; ZoneInfo handles it.
- Making time a parameter (`today_berlin(now)`) lets tests choose the moment.
- `@pytest.mark.parametrize` → one test, many inputs.
- `StrEnum` → a fixed list of allowed values that are also strings.

## Check-yourself answers
1. Why did 23:30 UTC on 3 November count as 4 November?
   ...
2. Why must a 500 response never include the exception text?
   ... (we'll see this in Part B)

## What was hard
- ImportError: the files existed but the functions were missing / not saved.
  Lesson: check the tab for the ● unsaved dot, and that function names match the tests.

## Interview line
"I keep business helpers like time zones, money formatting and error codes as pure,
tested functions, so the whole app handles Berlin dates and euro amounts the same way."