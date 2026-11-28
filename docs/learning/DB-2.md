SQLAlchemy: Python classes become tables.
Session: one conversation with the database; commit saves, rollback undoes.
get_session: each API request gets its own session; it commits if the request succeeds and rolls back if it fails.
Alembic: version control for the database structure.
Testcontainers: a real throwaway Postgres for tests.
Test isolation: each test runs in a transaction that's rolled back, so tests never affect each other.
What was hard: the Docker socket on Mac; the .env value with spaces needing quotes; import order (I001).
Check-yourself answers (from the plan):
What does session.commit() do that session.flush() doesn't?
Why test against a real Postgres instead of SQLite?

Commit it, push, open the pull request, and merge once it's green.

3. Then:

say "walkthrough DB-2" for the explanation and interview questions; or
say "next" to start DB-3, where you create the real tables (customers, products, rates, orders, payments, bills) and your first Alembic migration.
What does session.commit() do that session.flush() doesn't?
Why test against a real Postgres instead of SQLite?

Here are the answers to put in your own words.

1. What does commit() do that flush() doesn't?

Both send your changes to the database, but only commit() makes them permanent.

flush() sends the SQL (INSERT, UPDATE) inside the open transaction. The database checks it: constraints run, IDs get created. But it isn't final; a rollback() can still undo it, and other connections can't see it yet.
commit() flushes anything still pending, then ends the transaction and saves everything for good. Now everyone can see it, and it survives a restart.

Comparison: flush() is like putting items on the till so the cashier scans them (you see prices and errors); commit() is paying. Until you pay, you can still put everything back.

Where you'll use it:

flush() in services and tests, when you need a new row's ID before saving, or want a constraint error now. DB-3's tests use session.flush() to check that a duplicate rate raises an error.
commit() happens once, at the end of each request, in get_session.
In tests nothing is ever committed for real, because the session fixture rolls everything back. That's why tests stay clean.
2. Why test against a real Postgres instead of SQLite?

Because production runs Postgres, and SQLite behaves differently in ways that matter for this app. A test only proves something if it runs on the same kind of database as production.

Real differences you'd hit:

Native enums: your order statuses become a Postgres ENUM type; SQLite has none.
CHECK constraints and types: SQLite is very loose. It happily stores text in an integer column; Postgres rejects it.
Time zones: timestamptz works properly in Postgres; SQLite has no real date or time types.
Migrations: your Alembic migrations are written for Postgres. Running them on SQLite might fail, or pass while hiding bugs.
SQL features later: ILIKE (case-insensitive search, used in BE-13) exists in Postgres but not SQLite.

If tests passed on SQLite but production broke on Postgres, the tests would give you false confidence. Testcontainers makes real Postgres easy: one throwaway container per test run, the same version as production (16), started automatically.

The trade-off: it's a bit slower (a few seconds to start) and needs Docker. That's worth it for correctness.

Interview line: "I test against the same database engine as production, using Testcontainers, so constraints, enums and migrations behave exactly as they will live; each test runs in a rolled-back transaction, so tests stay isolated and fast."