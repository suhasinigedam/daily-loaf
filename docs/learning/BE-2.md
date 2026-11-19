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

# BE-2 Part B — One error format, request IDs, JSON logs
Imagine the API is a restaurant kitchen. Part B adds three things every professional kitchen needs.

1. api/middleware.py: the order ticket and the safety net
The ticket: every request gets a unique number, the request ID, like an order ticket number. It’s sent back in the X-Request-ID header.
The safety net: if code crashes unexpectedly, this catches it, writes the full details to the log, and sends the user only a polite “Internal error”. The app never shows its insides.

Why: when something goes wrong, the user can say “reference abc-123”, and you find exactly that request in the logs.

2. api/errors.py: one standard way to say “no”

The app can refuse a request for different reasons:

a business rule, e.g. “this month is already billed” (DomainError);
bad input, e.g. quantity 0;
a wrong URL.

This file turns all of them into the same JSON shape:

json
{"error": {"code": "PERIOD_LOCKED", "message": "...", "field": "paid_on"}}

Why: the Angular app only needs to understand one error format. It reads code to choose the message, and field to highlight the right input box.

3. logging_config.py: a structured diary

It makes every log line JSON, and adds the request ID automatically:

json
{"timestamp": "...", "level": "ERROR", "logger": "app.request", "message": "unhandled_error", "request_id": "abc-123"}

Why: on AWS, CloudWatch can search and filter JSON logs, e.g. “show me everything for request abc-123”, or “all errors today”. Plain text lines are much harder to search.

How they work together
1. Request arrives        → middleware gives it ID abc-123
2. Something goes wrong   → errors.py answers {"error": {...}}   (known problem)
                            or middleware answers "Internal error" (unexpected crash)
3. Log line written       → logging_config adds "request_id": "abc-123"
4. Response sent          → header X-Request-ID: abc-123

In one sentence: the user gets a clear, safe answer; the frontend gets one predictable error format; and you can find any problem in the logs by its ID.