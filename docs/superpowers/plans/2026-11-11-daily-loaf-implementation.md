# Daily Loaf — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Suhasini builds every task herself, in VS Code, as a learning project.** An agent's job is the walkthrough and review described in "Learning loop". Never run [MANUAL] tasks, and never push to her repo.

**Goal:** An admin-only, mobile-friendly web app for a home bread business (customers, orders, daily rates, payments, monthly PDF bills with carry-forward). It runs on AWS for close to €0 and is published as a public portfolio repo with a live demo.

**Architecture:** Angular + TypeScript SPA on S3/CloudFront calls a FastAPI backend running as a Lambda container image behind API Gateway. Data lives in Neon Postgres (Frankfurt) and PDF bills in a private S3 bucket. Admins sign in with Cognito (MFA). Business rules are pure Python, tested without AWS or a database. Search runs on Elasticsearch locally and in CI, with a Postgres implementation of the same interface on AWS.

**Tech Stack:**
- **Backend:** Python 3.12, uv, FastAPI, Pydantic v2, SQLAlchemy 2 (sync), Alembic, psycopg 3, PyJWT, WeasyPrint, boto3, Mangum.
- **Search:** Elasticsearch 9 (Docker locally), `elasticsearch` Python client.
- **Backend tests:** pytest, Testcontainers (Postgres and Elasticsearch), moto, time-machine.
- **Frontend:** Node 26, current Angular (standalone, signals, zoneless), TypeScript (strict), RxJS, typed Reactive Forms, Angular Material + CDK, openapi-typescript (types only), aws-amplify 6 (Auth only), angularx-qrcode.
- **Frontend tests:** Angular CLI test runner (Vitest), Angular Testing Library, `HttpTestingController`, Playwright.
- **Infrastructure and CI:** Terraform ≥ 1.9, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-11-daily-loaf-architecture.md` (architecture, data model, rules, API, diagrams). Read the matching section before each task.

**Repo:** `daily-loaf` (wherever a GitHub path says `bread-order-app`, use `daily-loaf`). AWS resource names keep the `bread-` prefix.

---

## How to use this plan

| Group | Who | Tasks |
|---|---|---|
| 1. Git & GitHub | **Suhasini, in VS Code and on github.com** | GIT-1, GIT-2 |
| 2. Database and search | Code | DB-1 … DB-5 |
| 3. Backend | Code | BE-1 … BE-13 |
| 4. Frontend (Angular) | Code | FE-1 … FE-12 |
| 5. AWS & deployment | **Suhasini, step by step** | AWS-1 … AWS-10 |

**Execution order** (groups depend on each other, so follow this order rather than the group order):

GIT-1 → DB-1 → BE-1 → GIT-2 → BE-2 → DB-2 → DB-3 → DB-4 → BE-3 → BE-4 → BE-5 … BE-12 → DB-5 → BE-13 → FE-1 … FE-12 → AWS-1 … AWS-10

**Interview-first order (BKA prep):** FE-1 … FE-7 can be built before the backend, because their unit tests fake the API with `HttpTestingController`.
- Until BE-12 produces `backend/openapi.json`, skip `npm run gen:api` and the schema-diff CI step.
- Write the types you need by hand in `core/api/api-types.ts`, matching the schemas in the BE tasks.
- Switch to the generated types once BE-12 is done.

All commands in code tasks run from the repo root unless a `cd` is shown. Commit steps are written as `git` commands, but you can do the same from VS Code's Source Control panel.

## Learning loop (every task)

Each task is built by you, then explained back to you, so you learn the why as well as the how.

```
1. Read      the task's "Learn first" block and the spec section it points to (15–30 min)
2. Branch    git switch -c <type>/<task-id>-<short-name>     e.g. feat/be-5-customers
3. Build     follow the steps: failing test → code → passing test → commit
4. Stuck?    paste the error or failing test to Claude: "stuck on BE-5 step 3"
5. Note      write docs/learning/<TASK-ID>.md (template below), commit it with the task
6. Walk      ask Claude "walkthrough <TASK-ID>" and paste your diff or the PR link
7. Merge     open the PR, wait for green CI, merge, tick the task in this plan
```

**What a walkthrough gives you:**
- your own code explained top to bottom: what each part does and why it's designed that way;
- how it connects to the earlier and later tasks;
- what to improve, if anything (a review, not a rewrite);
- 3–5 interview questions on it, which you answer and I correct;
- one sentence you can use in an interview to describe the task.

**Learning note template (`docs/learning/<TASK-ID>.md`):**
```markdown
# <TASK-ID>: <title>
## What I built
2–3 sentences.
## What I learned
- concept → what it means in my own words
## Check-yourself answers
1. ...
## What was hard / what I'd do differently
## Interview line
One sentence I'd say about this in an interview.
```

The notes live in the public repo. They show recruiters how you think, and they become your revision sheet before interviews.

**Progress so far:**
- GIT-1 is done: the repo `daily-loaf` exists, with the docs pushed.
- DB-1: `docker-compose.yml` may already exist; finish the remaining steps.

## Global Constraints

- **Money:** whole cents (`int`) everywhere: in the database, the API and frontend state. It is displayed in German format: `format_eur(55) == "0,55 €"` (a normal space before €).
- **Dates:**
  - Calendar dates are in Europe/Berlin.
  - "Today" is always `today_berlin()` on the backend and `todayBerlin()` on the frontend, never UTC.
  - Months are sent over the API as `"YYYY-MM"`.
- **Products and initial rates** (effective from `2026-01-01`):

  | code | name | price |
  |---|---|---|
  | `MINI_PAV` | Mini pav | 40 |
  | `MEDIUM_PAV` | Medium pav | 55 |
  | `NORMAL_PAV` | Normal pav | 60 |
  | `BROWNIE` | Brownie | 100 |
  | `ROTI` | Roti | 100 |

- **Order statuses:** `pending → confirmed → in_prep → delivered`; `pending | confirmed | in_prep → cancelled`.
  - Items are editable only in `pending` or `confirmed`.
  - Only `delivered` orders are billed, in the month of `delivery_date`.
- **API:**
  - Every route is under `/api/v1` and requires a Cognito access token, except `GET /api/v1/health`.
  - Every response has an `X-Request-ID` header.
  - Error body: `{"error": {"code": "<CODE>", "message": "<text>", "field": "<dotted.path or null>"}}`
- **PDF bill:**
  - Invoice number: `YYYY-MM-<customer id>`.
  - The note, verbatim: `Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.`
- **Bill storage:**
  - S3 key: `statements/YYYY-MM/<customer id>.pdf`.
  - Presigned download URLs expire after 300 seconds.
- **Mobile:**
  - Every screen works from 360px wide with no horizontal scroll.
  - Bottom tab bar below 1024px, sidenav from 1024px (CDK `BreakpointObserver`, query `(min-width: 1024px)`).
  - Tables become cards below 768px (CSS media query).
  - Touch targets at least 44×44px (global `.touch` class).
  - Inputs use a font size of at least 16px (stops iOS from zooming in).
- **Security:**
  - Never commit `.env`, `.tfvars`, Terraform state, connection strings or real customer data.
  - Tests and demo use Faker (`de_DE`, seed `42`) only.
  - No fonts, icons or scripts from third-party CDNs (GDPR, CSP): install them as npm packages.
  - Elasticsearch security is turned off only in the local Docker container, which is never exposed beyond your machine.
- **Quality:**
  - Backend coverage of at least 85% (`--cov-fail-under=85`).
  - ruff, mypy `--strict`, angular-eslint, Prettier and `ng build` (strict templates) must all pass in CI.
- **Region:**
  - AWS resources in `eu-central-1`.
  - Neon in AWS Europe Central 1 (Frankfurt).
- **Commits:** Conventional Commits (`feat:`, `fix:`, `test:`, `chore:`, `docs:`, `ci:`).

### Error codes (backend `ErrorCode`, frontend `messageFor`)

| Code | HTTP | Frontend message |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Please check the highlighted field. |
| `UNAUTHORIZED` | 401 | Your session has expired. Please sign in again. |
| `NOT_FOUND` | 404 | This item no longer exists. |
| `NO_RATE_FOR_DATE` | 422 | No price is set for this date. Add a rate first. |
| `INVALID_STATUS_TRANSITION` | 409 | This order can't move to that status. |
| `ORDER_NOT_EDITABLE` | 409 | Orders can only be edited before prep starts. |
| `CUSTOMER_INACTIVE` | 409 | This customer is inactive. |
| `PERIOD_LOCKED` | 409 | This month is already billed for this customer. |
| `RATE_EXISTS` | 409 | A price already starts on this date. |
| `PREVIOUS_MONTH_NOT_ISSUED` | 409 | Issue last month's bills first. |
| `LATER_MONTH_GENERATED` | 409 | A later month has already been generated. |
| `MONTH_NOT_ENDED` | 409 | Bills can be issued after the month ends. |
| `STATEMENT_ALREADY_ISSUED` | 409 | This bill is already issued. |
| `STATEMENT_NOT_ISSUED` | 409 | Issue this bill before downloading it. |
| `INTERNAL_ERROR` | 500 | Something went wrong. Reference: `<request id>` |

### Billing-period lock (architecture §5.5)

Months are tracked in a `billing_months` table (one row per generated month). Month M is **locked** for customer C if either of these is true:

- C has an **issued** statement for M, or
- any `billing_months` row exists with a month later than M.

When M is locked for C, the following are rejected with `PERIOD_LOCKED`:

- marking C's order delivered when its `delivery_date` is in M;
- creating or deleting C's payments with `paid_on` in M;
- creating or deleting C's adjustments for M.

## Review Focus

1. **Just after midnight in Berlin** (e.g. 2026-11-03 23:30 UTC = 4 Nov 00:30 Berlin): the dashboard, default dates and "month ended" checks use 4 November, not 3 November. Lambda runs in UTC. *Tested in BE-2 and BE-11.*
2. **Issuing a bill before its month has ended** is rejected with `MONTH_NOT_ENDED`, so the rest of the month's orders can't be locked out. *Tested in BE-10.*
3. **Placing an order for a deactivated or anonymised customer** is rejected with `CUSTOMER_INACTIVE`. *Tested in BE-7.*
4. **Marking an order delivered when its month is already billed** for that customer (issued statement, or a later month generated) is rejected with `PERIOD_LOCKED` and leaves the order unchanged. *Tested in BE-7.*
5. **Bad order items:** no items, a quantity of 0, or the same product twice gives 422 `VALIDATION_ERROR` with the field path, and the phone form shows the message next to the field. *Tested in BE-7 and FE-7.*

---

## File structure

```
.github/workflows/      backend.yml, frontend.yml, security.yml, deploy-demo.yml, deploy-prod.yml
.github/dependabot.yml
docker-compose.yml      local Postgres 16 + MinIO (S3) + Elasticsearch
backend/
  pyproject.toml  uv.lock  alembic.ini  Dockerfile  .env.example  openapi.json
  app/
    main.py             create_app()
    config.py           Settings
    clock.py            Berlin time + month helpers
    money.py            format_eur
    errors.py           ErrorCode, DomainError
    logging_config.py   JSON logging with request id
    auth.py             token verification, CurrentUser
    db.py               engine, session factory, get_session
    storage.py          BillStore, S3BillStore
    secrets.py          load SSM parameters at cold start
    lambda_handler.py   Mangum handler
    seed_demo.py        demo data + reset handler
    export_openapi.py
    domain/             enums.py, pricing.py, order_status.py, statements.py   (pure Python)
    models/             base.py, customer.py, product.py, order.py, payment.py, statement.py
    repositories/       customers.py, products.py, orders.py, payments.py, statements.py
    services/           customers.py, rates.py, orders.py, period_lock.py, payments.py,
                        statements.py, dashboard.py
    schemas/            common.py, customers.py, products.py, orders.py, payments.py,
                        statements.py, dashboard.py, search.py
    api/                deps.py, errors.py, middleware.py,
                        routes/{health,me,customers,products,orders,payments,adjustments,statements,dashboard,search}.py
    pdf/                render.py, templates/bill.html
    search/             mapping.py, base.py, documents.py, es_backend.py, pg_backend.py, sync.py, reindex.py
  migrations/           env.py, versions/
  tests/                conftest.py, factories.py, unit/, api/, db/, search/
frontend/
  angular.json  package.json  proxy.conf.json  playwright.config.ts
  public/config.json    runtime config (one build, any environment)
  src/main.ts  src/styles.scss
  src/app/
    app.ts  app.config.ts  app.routes.ts
    core/config/        app-config.ts (AppConfig, APP_CONFIG, loadAppConfig)
    core/api/           schema.d.ts (generated), api-types.ts, api-error.ts, error-messages.ts, interceptors.ts
    core/auth/          auth-api.ts, amplify-auth-api.ts, dev-auth-api.ts, auth.service.ts, auth.guard.ts, login.page.ts
    core/format/        money.ts, dates.ts, eur.pipe.ts, de-date.pipe.ts
    layout/             shell.component.ts, more-sheet.component.ts, demo-banner.component.ts, nav-items.ts
    shared/             responsive-list.component.ts, card-template.directive.ts, money-input.component.ts,
                        quantity-stepper.component.ts, confirm.service.ts, confirm-dialog.component.ts, validators.ts
    features/{dashboard,customers,rates,orders,payments,bills,search}/   (*.service.ts, *.page.ts, *.spec.ts)
  e2e/{full-flow.spec.ts, mobile-layout.spec.ts}
infra/
  bootstrap/            state bucket + lock table
  modules/app/          one environment (Cognito, S3, ECR, Lambda, API GW, CloudFront, alarms)
  envs/demo/  envs/prod/
docs/superpowers/{specs,plans}/
```

---

# Group 1 — Git & GitHub

### GIT-1: Create the GitHub repo and local project [MANUAL — VS Code]

**Learn first**

- **Concepts:**
  - Git tracks snapshots (commits); GitHub hosts a copy (the remote, `origin`).
  - `.gitignore` keeps secrets and generated files out of history for good.
  - Commit identity (`user.name`, `user.email`) is per machine or per repo.
- **Why it's built this way:** A public repo is your CV: clean history, no secrets, your own name on every commit.
- **Read:** [Pro Git book, chapters 1–2](https://git-scm.com/book/en/v2)
- **Check yourself** (answer these in your learning note):
  1. What's the difference between `git add`, `git commit` and `git push`?
  2. Why can't you just delete a leaked password in a later commit?
- **After the task:** write `docs/learning/GIT-1.md`, then ask me for **"walkthrough GIT-1"**.


- [ ] **Step 1: Install the tools**
  - Git, VS Code, Docker Desktop
  - uv (`pipx install uv` or the installer from docs.astral.sh/uv)
  - Node 26 LTS (from nodejs.org)
  - Terraform ≥ 1.9
  - AWS CLI v2

  **VS Code extensions:**
  - Python, Pylance, Ruff
  - Angular Language Service, ESLint, Prettier
  - Docker, HashiCorp Terraform
  - GitHub Pull Requests, GitHub Actions

  Check: `git --version`, `uv --version`, `node -v` (v22.x), `terraform -v`, `aws --version`, `docker compose version`.

- [ ] **Step 2: Hide your email in public commits**
  1. On github.com go to Settings → Emails.
  2. Turn on "Keep my email addresses private" and "Block command line pushes that expose my email".
  3. Copy your `…@users.noreply.github.com` address.
  4. In the VS Code terminal run:
     `git config --global user.name "Suhasini Gedam"`
     `git config --global user.email "<noreply address>"`

- [ ] **Step 3: Create the repo on github.com**
  1. Click New repository.
  2. Name: `bread-order-app`. Visibility: Public.
  3. Description: "Order, billing & payments app for a home bakery — Angular + FastAPI + Elasticsearch on AWS serverless".
  4. Tick "Add a README". License: MIT. .gitignore: None.

- [ ] **Step 4: Clone in VS Code**
  1. Open the Command Palette (Ctrl/Cmd+Shift+P) and run **Git: Clone**.
  2. Paste the repo URL and choose a parent folder (e.g. `~/projects`).
  3. Click Open.

- [ ] **Step 5: Add the design documents**
  Copy the downloaded spec and this plan into `docs/superpowers/specs/` and `docs/superpowers/plans/` in the repo.

- [ ] **Step 6: Create `.gitignore` at the repo root** with exactly:
```
.env
.env.*
!.env.example
__pycache__/
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
coverage/
htmlcov/
node_modules/
dist/
playwright-report/
test-results/
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
!example.tfvars
.DS_Store
.idea/
```

- [ ] **Step 7: Create `.editorconfig`** with: UTF-8, LF line endings, final newline, 4-space indent for `*.py`, 2-space indent for everything else.

- [ ] **Step 8: Commit and push**
  1. In the Source Control panel (Ctrl/Cmd+Shift+G), stage all files.
  2. Commit with the message `docs: add design spec and implementation plan`.
  3. Click **Sync Changes**.
  4. Check on github.com that `docs/` and `.gitignore` are there.

### GIT-2: Protect `main` and switch on GitHub security [MANUAL — github.com, after BE-1 has pushed CI]

**Learn first**

- **Concepts:**
  - Branch protection and rulesets force changes through pull requests.
  - Required status checks block merges until CI is green.
  - Secret scanning and push protection stop tokens reaching GitHub.
- **Why it's built this way:** Teams work this way; showing it on a solo project tells recruiters you know team workflow.
- **Read:** [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- **Check yourself** (answer these in your learning note):
  1. Merge commit vs squash vs rebase merge: when would you pick each?
  2. What is Dependabot for?
- **After the task:** write `docs/learning/GIT-2.md`, then ask me for **"walkthrough GIT-2"**.


- [ ] **Step 1: Turn on code security**
  In Settings → Code security, enable:
  - Dependency graph
  - Dependabot alerts
  - Dependabot security updates
  - Secret scanning
  - Push protection

- [ ] **Step 2: Add a branch ruleset**
  In Settings → Rules → Rulesets, create a new branch ruleset:
  - **Name:** `protect-main`
  - **Target:** default branch
  - **Rules to tick:**
    - Restrict deletions
    - Block force pushes
    - Require a pull request before merging (0 approvals, since you're the only developer)
    - Require status checks to pass: `backend`, `security`; add `frontend` once FE-1 has run
  - **Bypass list:** leave empty.

- [ ] **Step 3: Add topics**
  On the repo's About panel, add the topics `angular`, `typescript`, `elasticsearch`, `docker`, `fastapi`, `python`, `aws`, `serverless`, `terraform`, `postgresql`.

- [ ] **Step 4: Check the rules work**
  Try pushing directly to `main` from VS Code. It should be rejected. From now on, work on branches (e.g. `feat/be-2-platform`) and merge through pull requests.

---

# Group 2 — Database

### DB-1: Local Postgres and S3 with Docker Compose

**Learn first**

- **Concepts:**
  - An image is a template; a container is a running instance of it.
  - Compose starts several containers with networks, ports, volumes and health checks from one file.
  - Named volumes keep data when containers are recreated.
- **Why it's built this way:** Everyone (you, CI, a new teammate) gets the same Postgres and S3 with one command, without installing them.
- **Read:** [Docker Compose overview](https://docs.docker.com/compose/)
- **Check yourself** (answer these in your learning note):
  1. What happens to the data if you run `docker compose down` vs `down -v`?
  2. What does the port mapping `5432:5432` mean?
- **After the task:** write `docs/learning/DB-1.md`, then ask me for **"walkthrough DB-1"**.


**Files:**
- Create: `docker-compose.yml`, `backend/.env.example`

- [ ] **Step 1: Write `docker-compose.yml`** with three services:
  - **`db`:**
    - Image `postgres:16-alpine`; user, password and database all `bread` (local only).
    - Port `5432:5432`.
    - Healthcheck `pg_isready -U bread`.
    - Named volume `pgdata`.
  - **`s3`:**
    - Image `minio/minio`, command `server /data --console-address ":9001"`.
    - Ports `9000` and `9001`; user `minio`, password `minio12345`.
  - **`s3-init`:**
    - Image `minio/mc`, depends on `s3`.
    - Creates bucket `bread-bills-local`, then exits.

- [ ] **Step 2: Write `backend/.env.example`:**
```
ENVIRONMENT=local
DATABASE_URL=postgresql+psycopg://bread:bread@localhost:5432/bread
CORS_ORIGINS=["http://localhost:4200"]
AUTH_MODE=dev
COGNITO_ISSUER=
COGNITO_CLIENT_ID=
BILLS_BUCKET=bread-bills-local
S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio12345
AWS_DEFAULT_REGION=eu-central-1
BUSINESS_NAME=Demo Bakery
BUSINESS_ADDRESS=Musterstraße 1, 60311 Frankfurt am Main
```

- [ ] **Step 3: Start the services**
  Run: `docker compose up -d && docker compose ps`
  Expected: `db` shows `healthy`, `s3` shows `running`, and `s3-init` has exited with code 0.

- [ ] **Step 4: Commit**
```bash
git add docker-compose.yml backend/.env.example
git commit -m "chore: local postgres and minio via docker compose"
```

### DB-2: SQLAlchemy foundation, Alembic and test database fixtures

**Learn first**

- **Concepts:**
  - SQLAlchemy ORM maps Python classes to tables; a Session is a unit of work.
  - Alembic versions the schema as migration scripts.
  - Test isolation: each test runs inside a transaction that is rolled back.
- **Why it's built this way:** Migrations make schema changes reviewable and repeatable; rollback-per-test keeps tests fast and independent.
- **Read:** [SQLAlchemy 2.0 ORM quickstart](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) · [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- **Check yourself** (answer these in your learning note):
  1. What does `session.commit()` do that `session.flush()` doesn't?
  2. Why test against a real Postgres (Testcontainers) instead of SQLite?
- **After the task:** write `docs/learning/DB-2.md`, then ask me for **"walkthrough DB-2"**.


**Files:**
- Create:
  - `backend/app/db.py`
  - `backend/app/models/__init__.py`
  - `backend/app/models/base.py`
  - `backend/alembic.ini`
  - `backend/migrations/env.py`
  - `backend/migrations/script.py.mako`
- Modify: `backend/tests/conftest.py` (created in BE-1)
- Test: `backend/tests/db/test_connection.py`

**Interfaces:**
- Consumes: `Settings.database_url` (BE-1).
- Produces:
  - **In `app/models/base.py`:**
    - `class Base(DeclarativeBase)`.
    - `class AuditMixin` with columns `created_at`, `created_by: str(100)`, `updated_at`, `updated_by: str(100)`.
    - `created_at` and `updated_at` are `timestamptz` with server default `now()`.
    - `def touch(obj: AuditMixin, username: str) -> None` sets `updated_by`, and also `created_by` when it is `None`.
  - **In `app/db.py`:**
    - `def make_session_factory(database_url: str) -> sessionmaker[Session]`
    - FastAPI dependency `def get_session(request: Request) -> Iterator[Session]`. It uses `request.app.state.session_factory`, commits on success and rolls back on exception.
  - **Test fixtures in `tests/conftest.py`:**
    - `pg_url` (session scope): a Testcontainers `postgres:16-alpine` URL with driver `psycopg`, migrated to `head`.
    - `engine` (session scope).
    - `session` (function scope): an outer transaction rolled back after each test, using `join_transaction_mode="create_savepoint"`.

- [ ] **Step 1: Write the failing test**
```python
def test_database_reachable(session):
    assert session.execute(text("select 1")).scalar_one() == 1
```

- [ ] **Step 2: Run it to verify it fails**
  Run: `cd backend && uv run pytest tests/db/test_connection.py -v`
  Expected: an ERROR, because the `session` fixture isn't defined yet.

- [ ] **Step 3: Implement the files above and set up Alembic**
  - Run `uv run alembic init migrations`.
  - In `migrations/env.py`:
    - Read the URL from `DATABASE_URL`, or from `config.get_main_option("sqlalchemy.url")` when tests set it.
    - Set `target_metadata = Base.metadata` and import `app.models`.
  - In `alembic.ini`, use the file template `%%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s`.
  - The `pg_url` fixture runs `alembic.command.upgrade(cfg, "head")`, with `cfg` set to the container URL.

- [ ] **Step 4: Run it to verify it passes**
  Run: `cd backend && uv run pytest tests/db/test_connection.py -v`
  Expected: PASS (Docker must be running).

- [ ] **Step 5: Commit**
```bash
git add backend/app/db.py backend/app/models backend/alembic.ini backend/migrations backend/tests
git commit -m "feat(db): sqlalchemy base, alembic and test database fixtures"
```

### DB-3: Tables and the initial migration

**Learn first**

- **Concepts:**
  - Primary and foreign keys, UNIQUE and CHECK constraints.
  - Postgres native enums.
  - `ON DELETE CASCADE` for child rows; autogenerate then review migrations.
- **Why it's built this way:** Constraints are the last line of defence: even buggy code can't store a quantity of 0 or two prices on one date.
- **Read:** [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- **Check yourself** (answer these in your learning note):
  1. Why store money as integer cents?
  2. Why is `order_items.unit_price_cents` a copy instead of a join to `product_rates`?
- **After the task:** write `docs/learning/DB-3.md`, then ask me for **"walkthrough DB-3"**.


**Files:**
- Create:
  - `backend/app/domain/__init__.py`
  - `backend/app/domain/enums.py`
  - `backend/app/models/{customer,product,order,payment,statement}.py`
  - `backend/migrations/versions/<rev>_initial_schema.py` (autogenerated, then reviewed)
- Test: `backend/tests/db/test_schema.py`

**Interfaces:**
- Produces:
  - **Enums** (`StrEnum`, stored as Postgres native enums using their lowercase values):

    | Enum | Values |
    |---|---|
    | `OrderStatus` | `pending`, `confirmed`, `in_prep`, `delivered`, `cancelled` |
    | `OrderSource` | `whatsapp`, `phone`, `other` |
    | `PaymentMethod` | `cash`, `bank_transfer`, `other` |
    | `StatementStatus` | `draft`, `issued` |

  - **Models.** Every model has `id: int` as an identity primary key and includes `AuditMixin`, except `BillingMonth`.

    | Model | Columns and constraints |
    |---|---|
    | `Customer` | `name` str(200) not null; `phone` str(50) null; `address` text null; `notes` text null; `is_active` bool default true; `anonymised_at` timestamptz null |
    | `Product` | `code` str(30) unique; `name` str(100); `is_active` bool; `sort_order` int |
    | `ProductRate` | `product_id` FK; `price_cents` int CHECK > 0; `effective_from` date; UNIQUE(`product_id`, `effective_from`) |
    | `Order` | `customer_id` FK; `delivery_date` date (indexed); `source`; `status`; `notes` text null; `items` relationship (cascade `all, delete-orphan`) |
    | `OrderItem` | `order_id` FK `ON DELETE CASCADE`; `product_id` FK; `quantity` int CHECK > 0; `unit_price_cents` int CHECK ≥ 0; UNIQUE(`order_id`, `product_id`) |
    | `Payment` | `customer_id`; `amount_cents` CHECK > 0; `paid_on` date; `method`; `note` text null |
    | `Adjustment` | `customer_id`; `amount_cents` CHECK ≠ 0; `applies_to_month` date CHECK day = 1; `reason` text not null |
    | `MonthlyStatement` | `customer_id`; `month` date (first of month); `opening_cents`, `orders_cents`, `payments_cents`, `adjustments_cents`, `closing_cents` int; `status`; `pdf_s3_key` str null; `issued_at` timestamptz null; UNIQUE(`customer_id`, `month`) |
    | `BillingMonth` | `month` date primary key; `generated_at` timestamptz; `generated_by` str(100) |

- [ ] **Step 1: Write the failing tests**
```python
def test_migration_creates_all_tables(engine):
    names = set(inspect(engine).get_table_names())
    assert {"customers", "products", "product_rates", "orders", "order_items", "payments",
            "adjustments", "monthly_statements", "billing_months"} <= names

def test_models_match_migrations(pg_url):
    alembic_command.check(alembic_cfg(pg_url))  # raises if autogenerate would emit changes

def test_rate_unique_per_product_and_date(session):
    ...  # insert two ProductRate rows with same product_id + effective_from
    with pytest.raises(IntegrityError):
        session.flush()

def test_order_item_quantity_must_be_positive(session):
    ...  # OrderItem(quantity=0)
    with pytest.raises(IntegrityError):
        session.flush()
```
  `alembic_cfg(url)` is a helper in `conftest.py` that is shared with the `pg_url` fixture.

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/db/test_schema.py -v`
  Expected: FAIL, because the tables are missing.

- [ ] **Step 3: Write the models and generate the migration**
  - Write the enums and models.
  - Run `docker compose up -d db`, then `cd backend && uv run alembic revision --autogenerate -m "initial schema"`.
  - Read the generated file. Check that the native enum types, the CHECK constraints and `ON DELETE CASCADE` are all present, and add any that are missing by hand.
  - Run `uv run alembic upgrade head`, then `uv run alembic downgrade base`, then `uv run alembic upgrade head` to prove the migration works in both directions.

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest tests/db -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend/app/domain backend/app/models backend/migrations backend/tests/db
git commit -m "feat(db): schema for customers, products, rates, orders, payments, statements"
```

### DB-4: Seed products and initial rates

**Learn first**

- **Concepts:**
  - Data migrations insert reference data, not just schema.
  - `downgrade()` must undo exactly what `upgrade()` did.
- **Why it's built this way:** Every environment (local, CI, demo, prod) gets the same five products automatically.
- **Read:** [Alembic operations](https://alembic.sqlalchemy.org/en/latest/ops.html)
- **Check yourself** (answer these in your learning note):
  1. Why not insert the products from the app at startup instead?
- **After the task:** write `docs/learning/DB-4.md`, then ask me for **"walkthrough DB-4"**.


**Files:**
- Create: `backend/migrations/versions/<rev>_seed_products.py` (a data migration)
- Test: `backend/tests/db/test_seed.py`

- [ ] **Step 1: Write the failing test**
```python
def test_products_and_initial_rates_seeded(session):
    rows = session.execute(text(
        "select p.code, p.name, r.price_cents, r.effective_from from products p "
        "join product_rates r on r.product_id = p.id order by p.sort_order")).all()
    assert [(c, n, pr) for c, n, pr, _ in rows] == [
        ("MINI_PAV", "Mini pav", 40), ("MEDIUM_PAV", "Medium pav", 55),
        ("NORMAL_PAV", "Normal pav", 60), ("BROWNIE", "Brownie", 100), ("ROTI", "Roti", 100)]
    assert {d for *_, d in rows} == {date(2026, 1, 1)}
```

- [ ] **Step 2: Run it to verify it fails**
  Run: `cd backend && uv run pytest tests/db/test_seed.py -v`
  Expected: FAIL (the result is an empty list).

- [ ] **Step 3: Write the data migration**
  - Create it with `uv run alembic revision -m "seed products"`.
  - Insert the products with `sort_order` 1–5, the rates from Global Constraints, and `created_by='system'`.
  - `downgrade()` deletes these rows by `code`.

- [ ] **Step 4: Run it to verify it passes**
  Run: `cd backend && uv run pytest tests/db -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend/migrations backend/tests/db/test_seed.py
git commit -m "feat(db): seed products and initial rates"
```

---

### DB-5: Elasticsearch locally and the search index definition

**Learn first**

- **Concepts:**
  - Inverted index, mappings and analyzers.
  - `text` vs `keyword`; `nested` vs `object`.
  - Index lifecycle: create, recreate, ensure.
- **Why it's built this way:** An explicit mapping makes search predictable; the folding analyzer handles German umlauts.
- **Read:** [Mapping](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html) · [Nested field type](https://www.elastic.co/guide/en/elasticsearch/reference/current/nested.html)
- **Check yourself** (answer these in your learning note):
  1. What would go wrong with order items if `items` were a plain `object`?
  2. Why is `status` a `keyword` and not `text`?
- **After the task:** write `docs/learning/DB-5.md`, then ask me for **"walkthrough DB-5"**.


**Files:**
- Modify: `docker-compose.yml`, `backend/.env.example`, `backend/pyproject.toml`, `backend/tests/conftest.py`
- Create: `backend/app/search/__init__.py`, `backend/app/search/mapping.py`
- Test: `backend/tests/search/test_mapping.py`

**Interfaces:**
- Produces:
  - **`mapping.py`:**
    - `INDEX_NAME = "daily-loaf-search"`
    - `INDEX_BODY: dict[str, Any]`: the settings and mappings below.
    - `ensure_index(es: Elasticsearch) -> None` creates the index if it is missing.
    - `recreate_index(es: Elasticsearch) -> None` deletes it if present, then creates it.
  - **Analyzer `folded`:** `standard` tokenizer, then the `lowercase` and `asciifolding` filters, so "Müller" matches "muller".
  - **Fields:**

    | Field | Type |
    |---|---|
    | `kind` | `keyword` (`customer` or `order`) |
    | `entity_id`, `customer_id`, `total_cents` | `integer` |
    | `customer_name` | `text` (analyzer `folded`) with a `keyword` sub-field `raw` |
    | `customer_phone`, `notes` | `text` (analyzer `folded`) |
    | `is_active` | `boolean` |
    | `delivery_date` | `date` |
    | `month`, `status`, `source` | `keyword` |
    | `items` | `nested`: `product_code` (`keyword`), `product_name` (`text`, `folded`), `quantity` (`integer`) |

  - **Test fixture `es_url`** (session scope): a Testcontainers Elasticsearch container with security off, single node and a 1 GB memory limit.
  - **Settings** (in `app/config.py`):
    - `search_backend: Literal["elasticsearch", "postgres"] = "postgres"`
    - `elasticsearch_url: str | None = None`
    - A validator raises if `search_backend == "elasticsearch"` and `elasticsearch_url` is empty.

- [ ] **Step 1: Add Elasticsearch to `docker-compose.yml`**
  Add this service and a named volume `esdata`:
```yaml
  search:
    image: docker.elastic.co/elasticsearch/elasticsearch:9.1.0
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
      ES_JAVA_OPTS: -Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - esdata:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -fs http://localhost:9200/_cluster/health || exit 1"]
      interval: 10s
      retries: 12
```
  Use the newest `9.x` tag from elastic.co if a later one exists. Pin the same version everywhere it appears (here and in the test fixture).

  Security is off **for local use only**. Port 9200 is reachable only from your own machine.

- [ ] **Step 2: Add the local settings to `backend/.env.example`**
```
SEARCH_BACKEND=elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
```

- [ ] **Step 3: Start it and check it**
  Run: `docker compose up -d search && curl -s localhost:9200/_cluster/health`
  Expected: JSON with `"status":"green"` or `"yellow"`. Yellow is normal for a single node.

  If it exits immediately, raise Docker Desktop's memory to at least 4 GB (Settings → Resources).

- [ ] **Step 4: Add the dependencies**
  Run: `cd backend && uv add "elasticsearch>=9,<10" && uv add --dev "testcontainers[elasticsearch]"`

  The client's major version must match the server's.

- [ ] **Step 5: Write the failing tests**
```python
def test_index_created_with_mapping(es_url):
    es = Elasticsearch(es_url)
    recreate_index(es)
    props = es.indices.get_mapping(index=INDEX_NAME)[INDEX_NAME]["mappings"]["properties"]
    assert props["items"]["type"] == "nested"
    assert props["status"]["type"] == "keyword"
    assert props["customer_name"]["fields"]["raw"]["type"] == "keyword"

def test_folding_analyzer(es_url):
    es = Elasticsearch(es_url); recreate_index(es)
    tokens = es.indices.analyze(index=INDEX_NAME, analyzer="folded", text="Müller Bäckerei")["tokens"]
    assert [t["token"] for t in tokens] == ["muller", "backerei"]

def test_ensure_index_is_idempotent(es_url):
    es = Elasticsearch(es_url); ensure_index(es); ensure_index(es)
    assert es.indices.exists(index=INDEX_NAME)

def test_elasticsearch_needs_url():
    with pytest.raises(ValidationError):
        Settings(search_backend="elasticsearch", elasticsearch_url=None, ...)
```

- [ ] **Step 6: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/search/test_mapping.py -v`
  Expected: FAIL (import errors).

- [ ] **Step 7: Implement `mapping.py`, the settings and the fixture**

- [ ] **Step 8: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest -v`
  Expected: PASS. The first run downloads the image, which is slow.

- [ ] **Step 9: Commit**
```bash
git add docker-compose.yml backend
git commit -m "feat(search): local elasticsearch and search index mapping"
```

---

# Group 3 — Backend

### BE-1: Backend scaffold, tooling and CI

**Learn first**

- **Concepts:**
  - FastAPI app factory (`create_app`) and routers.
  - Settings from environment variables with pydantic-settings.
  - uv for dependencies and lock files; ruff and mypy for quality; CI on every PR.
- **Why it's built this way:** An app factory lets tests build the app with fake dependencies; CI catches problems before merge.
- **Read:** [FastAPI tutorial: first steps](https://fastapi.tiangolo.com/tutorial/first-steps/) · [GitHub Actions quickstart](https://docs.github.com/en/actions/writing-workflows/quickstart)
- **Check yourself** (answer these in your learning note):
  1. What does `uv.lock` guarantee?
  2. Why does the health endpoint need no login?
- **After the task:** write `docs/learning/BE-1.md`, then ask me for **"walkthrough BE-1"**.


**Files:**
- Create:
  - `backend/pyproject.toml`
  - `backend/app/__init__.py`
  - `backend/app/config.py`
  - `backend/app/main.py`
  - `backend/app/api/routes/health.py`
  - `backend/tests/api/test_health.py`
  - `.pre-commit-config.yaml`
  - `.github/workflows/backend.yml`
  - `.github/workflows/security.yml`
  - `.github/dependabot.yml`
  - `README.md` (replace)

**Interfaces:**
- Produces:
  - **`class Settings(BaseSettings)`**, which reads environment variables and `.env`. Fields:
    - `environment: Literal["local", "demo", "prod"]`
    - `database_url: str`
    - `cors_origins: list[str]`
    - `auth_mode: Literal["cognito", "dev"] = "cognito"`
    - `cognito_issuer: str = ""`
    - `cognito_client_id: str = ""`
    - `bills_bucket: str`
    - `s3_endpoint_url: str | None = None`
    - `business_name: str`
    - `business_address: str`
    - `log_level: str = "INFO"`
  - **`def create_app(settings: Settings | None = None) -> FastAPI`.** BE-3 adds `jwks_provider` and BE-10 adds `bill_store` as keyword-only parameters.
  - `GET /api/v1/health` returns `{"status": "ok"}`.

- [ ] **Step 1: Create the project**
  - Run `cd backend && uv init --app --python 3.12`.
  - Add runtime dependencies: `fastapi`, `pydantic-settings`, `sqlalchemy>=2`, `alembic`, `psycopg[binary]`, `pyjwt[crypto]`, `boto3`, `weasyprint`, `jinja2`, `mangum`, `python-json-logger`, `uvicorn`.
  - Add dev dependencies with `--dev`: `pytest`, `pytest-cov`, `httpx`, `testcontainers[postgres]`, `moto[s3,ssm]`, `time-machine`, `pypdf`, `faker`, `ruff`, `mypy`, `bandit`, `pip-audit`, `boto3-stubs[s3,ssm]`.
  - In `pyproject.toml`, configure:
    - ruff: `line-length = 100`; rule sets `E, F, I, B, UP, S, SIM`; ignore `S101` in tests.
    - mypy: `strict = true`, `plugins = ["pydantic.mypy"]`.
    - pytest: `testpaths = ["tests"]`.
    - coverage: `source = ["app"]`, `fail_under = 85`.

- [ ] **Step 2: Write the failing test**
```python
def test_health_ok(anon_client):
    r = anon_client.get("/api/v1/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
```
  In `conftest.py`:
  - `test_settings` returns a `Settings` with `environment="local"`, `cors_origins=["http://localhost:4200"]`, `cognito_issuer="https://cognito-idp.eu-central-1.amazonaws.com/test-pool"`, `cognito_client_id="test-client"`, `bills_bucket="test-bills"`, `business_name="Test Bakery"`, `business_address="Teststraße 1, 60311 Frankfurt"`, and `database_url` from `pg_url` (until DB-2, use `"postgresql+psycopg://unused"`).
  - `anon_client` is a `TestClient(create_app(test_settings))`.

- [ ] **Step 3: Run it to verify it fails, then implement `config.py`, `main.py` and `health.py`**
  Run: `cd backend && uv run pytest tests/api/test_health.py -v`. Expected: FAIL. Then implement.
  `create_app` stores the settings on `app.state.settings` and mounts the routers under `/api/v1`.

- [ ] **Step 4: Run it to verify it passes**
  Run: `cd backend && uv run pytest -v && uv run ruff check . && uv run ruff format --check . && uv run mypy app`
  Expected: everything passes.

- [ ] **Step 5: Add `.pre-commit-config.yaml`**
  Hooks: ruff (lint and format) on `backend/`, gitleaks, `check-added-large-files`, `end-of-file-fixer`, `trailing-whitespace`.

- [ ] **Step 6: Add `.github/workflows/backend.yml`**
  - **Triggers:** `pull_request` and `push` to `main`, with paths `backend/**`, `docker-compose.yml` and the workflow file itself.
  - **One job, named `backend`,** running on `ubuntu-24.04`. Steps:
    1. Checkout.
    2. `astral-sh/setup-uv` with Python 3.12.
    3. `sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0` (needed by WeasyPrint).
    4. `uv sync --locked`.
    5. `ruff check`, then `ruff format --check`, then `mypy app`.
    6. `pytest --cov --cov-report=xml` (Testcontainers uses the runner's Docker).
    7. `pip-audit` (run as `uv run pip-audit`).
    8. `bandit -r app -q`.
  - Set `permissions: contents: read`.

- [ ] **Step 7: Add `.github/workflows/security.yml`**
  - **Triggers:** `pull_request`, `push` to `main`, and a weekly schedule.
  - **One job, named `security`.** It runs `gitleaks/gitleaks-action@v2` with `fetch-depth: 0`.

- [ ] **Step 8: Add `.github/dependabot.yml`**
  - Weekly updates for the ecosystems `uv` (`/backend`), `npm` (`/frontend`), `github-actions` (`/`) and `terraform` (`/infra/envs/demo`, `/infra/envs/prod`).

- [ ] **Step 9: Write `README.md`**
  - Title.
  - One-paragraph description.
  - Badge placeholders: `backend` workflow, `frontend` workflow, coverage, live demo.
  - Tech stack.
  - "Run locally": `docker compose up -d`, `cd backend && cp .env.example .env && uv run alembic upgrade head && uv run uvicorn app.main:app --reload`.
  - Links to the spec and plan.

- [ ] **Step 10: Commit and push**
```bash
git switch -c chore/be-1-scaffold
git add backend .pre-commit-config.yaml .github README.md
git commit -m "chore(backend): fastapi scaffold, tooling and CI"
git push -u origin chore/be-1-scaffold
```
  Open a pull request and merge it once `backend` and `security` are green. Then do **GIT-2**.

### BE-2: Platform — clock, money, errors, request IDs and logging

**Learn first**

- **Concepts:**
  - Time zones: store dates in Berlin time, not UTC.
  - Domain errors vs HTTP errors; one error format.
  - Middleware and context variables for request IDs; structured JSON logs.
- **Why it's built this way:** Consistent errors let the frontend show the right message; a request ID connects a user's error to a log line.
- **Read:** [FastAPI: handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/) · [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html)
- **Check yourself** (answer these in your learning note):
  1. Why did 23:30 UTC on 3 November count as 4 November?
  2. Why must a 500 response never include the exception text?
- **After the task:** write `docs/learning/BE-2.md`, then ask me for **"walkthrough BE-2"**.


**Files:**
- Create:
  - `backend/app/clock.py`
  - `backend/app/money.py`
  - `backend/app/errors.py`
  - `backend/app/api/errors.py`
  - `backend/app/api/middleware.py`
  - `backend/app/logging_config.py`
- Modify: `backend/app/main.py`
- Test:
  - `backend/tests/unit/test_clock.py`
  - `backend/tests/unit/test_money.py`
  - `backend/tests/api/test_errors.py`

**Interfaces:**
- Produces:
  - **`clock.py`:**
    - `BERLIN = ZoneInfo("Europe/Berlin")`
    - `today_berlin(now: datetime | None = None) -> date`
    - `month_start(d: date) -> date`
    - `next_month(m: date) -> date`
    - `prev_month(m: date) -> date`
    - `month_end(m: date) -> date`
    - `parse_month(s: str) -> date`: `"2026-10"` gives `date(2026, 10, 1)`; anything else raises `DomainError(VALIDATION_ERROR, field="month")`.
    - `format_month(m: date) -> str`
  - **`money.py`:** `format_eur(cents: int) -> str`.
  - **`errors.py`:**
    - `class ErrorCode(StrEnum)` with the codes from the Global Constraints table.
    - `HTTP_STATUS: dict[ErrorCode, int]`.
    - `class DomainError(Exception)` with `__init__(self, code: ErrorCode, message: str, field: str | None = None)`.
  - **`api/errors.py`:** `install_error_handlers(app: FastAPI) -> None`, which handles:
    - `DomainError` → the mapped status.
    - `RequestValidationError` → 422 `VALIDATION_ERROR`, with `field` set to the first error's `loc` minus the leading `"body"`/`"query"`, dot-joined (e.g. `items.0.quantity`).
    - Starlette `HTTPException` 404/405 → `NOT_FOUND`.
    - Any other `Exception` → 500 `INTERNAL_ERROR` with message `"Internal error"`, logged with its traceback.
  - **`api/middleware.py`:** `RequestIdMiddleware`. It reuses an incoming `X-Request-ID` if it is a valid UUID, otherwise generates `uuid4`. It sets the `request_id_var: ContextVar[str]` and adds the header to every response.
  - **`logging_config.py`:** `configure_logging(level: str) -> None`. JSON logs with the keys `timestamp`, `level`, `logger`, `message`, `request_id`.

- [ ] **Step 1: Write the failing tests**
```python
def test_today_berlin_after_midnight():  # Review Focus 1
    assert today_berlin(datetime(2026, 11, 3, 23, 30, tzinfo=UTC)) == date(2026, 11, 4)

def test_month_helpers():
    assert month_end(date(2026, 2, 1)) == date(2026, 2, 28)
    assert next_month(date(2026, 12, 1)) == date(2027, 1, 1)
    assert prev_month(date(2026, 1, 1)) == date(2025, 12, 1)
    assert parse_month("2026-10") == date(2026, 10, 1)
    with pytest.raises(DomainError):
        parse_month("2026-13")

@pytest.mark.parametrize("cents,text", [(55, "0,55 €"), (123456, "1.234,56 €"),
                                        (-500, "-5,00 €"), (0, "0,00 €")])
def test_format_eur(cents, text):
    assert format_eur(cents) == text

def test_domain_error_shape(anon_client_with_probe):   # probe route raises DomainError(PERIOD_LOCKED, "x", "paid_on")
    r = anon_client_with_probe.get("/api/v1/_probe/domain")
    assert r.status_code == 409
    assert r.json() == {"error": {"code": "PERIOD_LOCKED", "message": "x", "field": "paid_on"}}
    assert uuid.UUID(r.headers["X-Request-ID"])

def test_unexpected_error_hides_details(anon_client_with_probe):  # probe raises RuntimeError("secret")
    r = anon_client_with_probe.get("/api/v1/_probe/boom")
    assert r.status_code == 500 and "secret" not in r.text
    assert r.json()["error"]["code"] == "INTERNAL_ERROR"

def test_request_id_is_echoed(anon_client):
    rid = str(uuid.uuid4())
    assert anon_client.get("/api/v1/health", headers={"X-Request-ID": rid}).headers["X-Request-ID"] == rid
```
  `anon_client_with_probe` is a fixture that adds a test-only router to the app. It is never added in `create_app`.

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/unit tests/api/test_errors.py -v`
  Expected: FAIL (import errors).

- [ ] **Step 3: Implement the modules above and wire them up**
  In `create_app`, call `configure_logging`, add the middleware and call `install_error_handlers`.
  `TestClient` must use `raise_server_exceptions=False` for the 500 test.

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend
git commit -m "feat(backend): berlin clock, euro formatting, error format, request ids, json logs"
```

### BE-3: Authentication (Cognito access tokens, local dev mode)

**Learn first**

- **Concepts:**
  - JWT structure: header, payload, signature.
  - Verifying with a JWKS public key; checking issuer, expiry and token use.
  - FastAPI dependencies (`Depends`).
- **Why it's built this way:** The API trusts nothing from the browser except a token Cognito signed; dev mode is impossible outside local.
- **Read:** [Verifying a Cognito JWT](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html) · [PyJWT usage](https://pyjwt.readthedocs.io/en/stable/usage.html)
- **Check yourself** (answer these in your learning note):
  1. Access token vs ID token: which one does an API accept, and why?
  2. Where does the public key come from, and why can't an attacker forge a token?
- **After the task:** write `docs/learning/BE-3.md`, then ask me for **"walkthrough BE-3"**.


**Files:**
- Create:
  - `backend/app/auth.py`
  - `backend/app/api/deps.py`
  - `backend/app/api/routes/me.py`
- Modify:
  - `backend/app/main.py`
  - `backend/app/config.py`
  - `backend/tests/conftest.py`
- Test: `backend/tests/api/test_auth.py`

**Interfaces:**
- Produces:
  - **`auth.py`:**
    - `@dataclass(frozen=True) class CurrentUser: sub: str; username: str`
    - `class JwksProvider(Protocol): def get_signing_key(self, token: str) -> Any`
    - `class CognitoJwks`, which wraps `jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_keys=True)`.
    - `verify_access_token(token: str, *, jwks: JwksProvider, issuer: str, client_id: str) -> CurrentUser`. It checks:
      - an `RS256` signature;
      - `iss == issuer`;
      - `exp`;
      - `token_use == "access"`;
      - `client_id` claim `== client_id`. Cognito access tokens have no `aud`, so `client_id` is checked instead.
  - **`create_app(settings=None, *, jwks_provider: JwksProvider | None = None)`.**
  - **`api/deps.py`:**
    - `get_current_user(request: Request) -> CurrentUser`. It reads `Authorization: Bearer`; anything invalid or missing raises `DomainError(UNAUTHORIZED, "Not authenticated")`.
    - `SessionDep` and `UserDep` as `Annotated` aliases.
    - Every router except health is included with `dependencies=[Depends(get_current_user)]`.
  - **Dev mode:**
    - When `settings.auth_mode == "dev"`, the token `dev-token` resolves to `CurrentUser("dev", "dev")`.
    - A `Settings` validator raises if `auth_mode == "dev"` and `environment != "local"`.
  - **`GET /api/v1/me`** returns `{"username": ...}`.
  - **Test fixtures:**
    - `rsa_key`.
    - `make_token(**overrides) -> str`. Its default claims are `iss` = the test issuer, `client_id="test-client"`, `token_use="access"`, `sub="sub-1"`, `username="test-admin"`, `exp` = now + 1 hour.
    - `StaticJwks`.
    - `client`: a `TestClient` carrying `Authorization: Bearer <make_token()>`, with `get_session` overridden to yield the test `session`.

- [ ] **Step 1: Write the failing tests**
```python
def test_valid_token(client):
    assert client.get("/api/v1/me").json() == {"username": "test-admin"}

@pytest.mark.parametrize("overrides", [
    {"exp": 1}, {"client_id": "other"}, {"token_use": "id"},
    {"iss": "https://cognito-idp.eu-central-1.amazonaws.com/other"}])
def test_rejected_tokens(anon_client, make_token, overrides):
    r = anon_client.get("/api/v1/me", headers={"Authorization": f"Bearer {make_token(**overrides)}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHORIZED"

def test_missing_token(anon_client):
    assert anon_client.get("/api/v1/me").status_code == 401

def test_token_signed_by_other_key(anon_client, other_key_token):
    assert anon_client.get("/api/v1/me", headers={"Authorization": f"Bearer {other_key_token}"}).status_code == 401

def test_dev_mode_forbidden_outside_local():
    with pytest.raises(ValidationError):
        Settings(environment="prod", auth_mode="dev", ...)

def test_health_needs_no_token(anon_client):
    assert anon_client.get("/api/v1/health").status_code == 200
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/api/test_auth.py -v`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**
  Catch every `jwt.PyJWTError` and turn it into `UNAUTHORIZED`.

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend
git commit -m "feat(backend): cognito access-token verification and local dev auth"
```

### BE-4: Pure business rules

**Learn first**

- **Concepts:**
  - Pure functions: no I/O, same input gives the same output.
  - State machines for order status.
  - Test-driven development: red, green, refactor.
- **Why it's built this way:** The most important rules (prices, status, money) are the easiest to test and change.
- **Read:** [pytest: get started](https://docs.pytest.org/en/stable/getting-started.html) · [pytest parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html)
- **Check yourself** (answer these in your learning note):
  1. Why keep these modules free of database imports?
  2. Which transitions are allowed, and how does the test prove the rest are not?
- **After the task:** write `docs/learning/BE-4.md`, then ask me for **"walkthrough BE-4"**.


**Files:**
- Create:
  - `backend/app/domain/pricing.py`
  - `backend/app/domain/order_status.py`
  - `backend/app/domain/statements.py`
- Test: `backend/tests/unit/test_pricing.py`, `test_order_status.py`, `test_statements.py`

**Interfaces:**
- Produces:
  - **`pricing.py`:** `resolve_rate(rates: Iterable[tuple[date, int]], on: date) -> int`. It returns the price with the latest `effective_from` on or before `on`, and raises `DomainError(NO_RATE_FOR_DATE, "No price set for <dd.mm.yyyy>", field="delivery_date")` if there is none.
  - **`order_status.py`:**
    - `ALLOWED: dict[OrderStatus, frozenset[OrderStatus]]`
    - `check_transition(current: OrderStatus, target: OrderStatus) -> None`, which raises `INVALID_STATUS_TRANSITION`.
    - `is_editable(status: OrderStatus) -> bool`
  - **`statements.py`:**
    - `@dataclass(frozen=True) StatementTotals(opening_cents, orders_cents, payments_cents, adjustments_cents, closing_cents)`
    - `compute_statement(opening_cents: int, order_line_totals: Iterable[int], payments: Iterable[int], adjustments: Iterable[int]) -> StatementTotals`
    - `@dataclass(frozen=True) StatementLine(delivery_date: date, order_id: int, product_name: str, quantity: int, unit_price_cents: int, line_total_cents: int)`

- [ ] **Step 1: Write the failing tests**
```python
RATES = [(date(2026, 1, 1), 55), (date(2026, 11, 10), 60)]

def test_rate_before_and_on_change():
    assert resolve_rate(RATES, date(2026, 11, 9)) == 55
    assert resolve_rate(RATES, date(2026, 11, 10)) == 60

def test_no_rate_before_first():
    with pytest.raises(DomainError) as e:
        resolve_rate(RATES, date(2025, 12, 31))
    assert e.value.code == ErrorCode.NO_RATE_FOR_DATE

@pytest.mark.parametrize("a,b", [("pending", "confirmed"), ("confirmed", "in_prep"),
    ("in_prep", "delivered"), ("pending", "cancelled"), ("confirmed", "cancelled"), ("in_prep", "cancelled")])
def test_allowed_transitions(a, b):
    check_transition(OrderStatus(a), OrderStatus(b))

@pytest.mark.parametrize("a,b", [("delivered", "cancelled"), ("pending", "in_prep"),
    ("cancelled", "pending"), ("pending", "delivered"), ("delivered", "pending")])
def test_rejected_transitions(a, b):
    with pytest.raises(DomainError):
        check_transition(OrderStatus(a), OrderStatus(b))

def test_editable_only_before_prep():
    assert [s for s in OrderStatus if is_editable(s)] == [OrderStatus.PENDING, OrderStatus.CONFIRMED]

def test_statement_totals():
    t = compute_statement(1000, [400, 550], [500], [-100])
    assert (t.orders_cents, t.payments_cents, t.adjustments_cents, t.closing_cents) == (950, 500, -100, 1350)

def test_credit_carries_forward():
    assert compute_statement(-200, [], [], []).closing_cents == -200
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/unit -v`
  Expected: FAIL.

- [ ] **Step 3: Implement the three modules** (no database or framework imports)

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest tests/unit -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend/app/domain backend/tests/unit
git commit -m "feat(domain): rate lookup, order status rules, statement maths"
```

### BE-5: Customers API

**Learn first**

- **Concepts:**
  - REST resources and status codes (201, 404, 409, 422).
  - Pydantic request and response models.
  - Layers: route → service → repository.
- **Why it's built this way:** Thin routes and testable services; soft delete and anonymisation instead of hard deletes keep bills intact (GDPR).
- **Read:** [FastAPI: request body](https://fastapi.tiangolo.com/tutorial/body/) · [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/)
- **Check yourself** (answer these in your learning note):
  1. Why `POST /customers/{id}/deactivate` instead of `DELETE`?
  2. Why can't an anonymised customer be reactivated?
- **After the task:** write `docs/learning/BE-5.md`, then ask me for **"walkthrough BE-5"**.


**Files:**
- Create:
  - `backend/app/schemas/common.py`
  - `backend/app/schemas/customers.py`
  - `backend/app/repositories/customers.py`
  - `backend/app/services/customers.py`
  - `backend/app/api/routes/customers.py`
  - `backend/tests/factories.py`
- Test: `backend/tests/api/test_customers.py`

**Interfaces:**
- Produces:
  - **Schemas:**
    - `Page[T]` (`items: list[T]`, `total: int`).
    - `CustomerIn`: `name` 1–200 characters, stripped; `phone` ≤ 50, optional; `address` optional; `notes` optional.
    - `CustomerPatch`: all fields optional.
    - `CustomerOut`: `id`, `name`, `phone`, `address`, `notes`, `is_active`, `anonymised_at`, `created_at`, `created_by`.
  - **Routes:**

    | Method | Path | Notes |
    |---|---|---|
    | `GET` | `/customers` | Params `q` (case-insensitive match on name or phone), `include_inactive=false`, `limit` (default 50, max 200), `offset`. Ordered by name. |
    | `POST` | `/customers` | Returns 201. |
    | `GET` | `/customers/{id}` | |
    | `PATCH` | `/customers/{id}` | |
    | `POST` | `/customers/{id}/deactivate` | |
    | `POST` | `/customers/{id}/activate` | |
    | `POST` | `/customers/{id}/anonymise` | |

  - **`services/customers.py`:**
    - `get_active_customer(session, customer_id) -> Customer`. It raises `NOT_FOUND` or `CUSTOMER_INACTIVE` and is used by BE-7.
    - `anonymise(session, customer_id, username) -> Customer`. It sets `name = f"Anonymised customer #{id}"`, clears `phone`, `address` and `notes`, and sets `is_active=False` and `anonymised_at=now()`.
    - Anonymised customers cannot be patched or activated (`CUSTOMER_INACTIVE`).
  - **`tests/factories.py`:**
    - `product_id(session, code: str) -> int`
    - `make_customer(session, name="Test Customer", is_active=True) -> Customer`

- [ ] **Step 1: Write the failing tests**
```python
def test_create_and_get(client):
    r = client.post("/api/v1/customers", json={"name": "Asha Patil", "phone": "+49 151 1234567",
                                               "address": "Hauptstr. 5, 60311 Frankfurt"})
    assert r.status_code == 201
    body = r.json()
    assert body["is_active"] is True and body["created_by"] == "test-admin"
    assert client.get(f"/api/v1/customers/{body['id']}").json()["name"] == "Asha Patil"

def test_name_required(client):
    r = client.post("/api/v1/customers", json={"name": "  "})
    assert r.status_code == 422 and r.json()["error"]["field"] == "name"

def test_search_and_inactive_filter(client, session): ...
    # two customers, one deactivated; ?q=ash finds Asha; default list excludes deactivated;
    # include_inactive=true includes it

def test_unknown_customer_404(client):
    assert client.get("/api/v1/customers/999999").json()["error"]["code"] == "NOT_FOUND"

def test_anonymise(client, session):
    c = make_customer(session, name="Ravi")
    body = client.post(f"/api/v1/customers/{c.id}/anonymise").json()
    assert body["name"] == f"Anonymised customer #{c.id}"
    assert body["phone"] is None and body["is_active"] is False and body["anonymised_at"]
    r = client.patch(f"/api/v1/customers/{c.id}", json={"name": "x"})
    assert r.json()["error"]["code"] == "CUSTOMER_INACTIVE"
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/api/test_customers.py -v`
  Expected: FAIL (404s).

- [ ] **Step 3: Implement the schemas, repository, service and router**
  Every create and update calls `touch(obj, user.username)`.

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend
git commit -m "feat(api): customers CRUD, deactivate and anonymise"
```

### BE-6: Products and rates API

**Learn first**

- **Concepts:**
  - Effective-dated data (a price valid from a date).
  - Handling unique-constraint violations as a 409.
  - Query parameters with defaults.
- **Why it's built this way:** Rates change over time without touching old orders; the database guarantees one price per product per date.
- **Read:** [FastAPI: query parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- **Check yourself** (answer these in your learning note):
  1. How does the query find the rate for a given date?
  2. Why use a savepoint around the insert?
- **After the task:** write `docs/learning/BE-6.md`, then ask me for **"walkthrough BE-6"**.


**Files:**
- Create:
  - `backend/app/schemas/products.py`
  - `backend/app/repositories/products.py`
  - `backend/app/services/rates.py`
  - `backend/app/api/routes/products.py`
- Test: `backend/tests/api/test_rates.py`

**Interfaces:**
- Consumes: `resolve_rate` (BE-4), `today_berlin` (BE-2).
- Produces:
  - **`GET /products?on=YYYY-MM-DD`** (default: today in Berlin) returns a list of `ProductOut` (`id`, `code`, `name`, `sort_order`, `price_cents: int | None` for that date) for active products, ordered by `sort_order`.
  - **`GET /products/{id}/rates`** returns a list of `RateOut` (`id`, `price_cents`, `effective_from`), newest first.
  - **`POST /rates`** takes `{product_id, price_cents > 0, effective_from}` and returns 201 with `RateOut`.
    - A duplicate gives 409 `RATE_EXISTS` with `field="effective_from"`. Catch the `IntegrityError` inside a savepoint.
    - An unknown product gives `NOT_FOUND`.
  - **`services/rates.py`:**
    - `rate_for(session, product_id: int, on: date) -> int` (used by orders and factories).
    - `prices_on(session, on: date) -> dict[int, int | None]`.

- [ ] **Step 1: Write the failing tests**
```python
@time_machine.travel(datetime(2026, 11, 3, 10, tzinfo=UTC), tick=False)
def test_initial_prices(client):
    assert [(p["code"], p["price_cents"]) for p in client.get("/api/v1/products").json()] == [
        ("MINI_PAV", 40), ("MEDIUM_PAV", 55), ("NORMAL_PAV", 60), ("BROWNIE", 100), ("ROTI", 100)]

def test_new_rate_applies_from_its_date(client, session):
    pid = product_id(session, "MEDIUM_PAV")
    assert client.post("/api/v1/rates", json={"product_id": pid, "price_cents": 58,
                                              "effective_from": "2026-11-10"}).status_code == 201
    def price(d): return next(p["price_cents"] for p in client.get(f"/api/v1/products?on={d}").json()
                              if p["code"] == "MEDIUM_PAV")
    assert price("2026-11-09") == 55 and price("2026-11-10") == 58

def test_duplicate_rate_date(client, session):
    body = {"product_id": product_id(session, "ROTI"), "price_cents": 110, "effective_from": "2026-01-01"}
    r = client.post("/api/v1/rates", json=body)
    assert r.status_code == 409 and r.json()["error"]["code"] == "RATE_EXISTS"

def test_price_must_be_positive(client, session):
    r = client.post("/api/v1/rates", json={"product_id": product_id(session, "ROTI"),
                                           "price_cents": 0, "effective_from": "2026-12-01"})
    assert r.status_code == 422 and r.json()["error"]["field"] == "price_cents"

def test_price_is_null_before_first_rate(client):
    assert all(p["price_cents"] is None for p in client.get("/api/v1/products?on=2025-12-31").json())
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/api/test_rates.py -v`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend
git commit -m "feat(api): products with price for a date, rate history, new rates"
```

### BE-7: Orders API and the billing-period lock

**Learn first**

- **Concepts:**
  - Aggregates: an order and its items saved together in one transaction.
  - Snapshot pricing.
  - Business invariants enforced in services (period lock).
  - Avoiding N+1 queries with `selectinload`.
- **Why it's built this way:** The order is the heart of the app; every rule from the spec meets here, so the tests are the most thorough.
- **Read:** [SQLAlchemy relationship loading](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- **Check yourself** (answer these in your learning note):
  1. What is an N+1 query and how do you spot it?
  2. Why reject a delivery into a locked month instead of silently moving it?
- **After the task:** write `docs/learning/BE-7.md`, then ask me for **"walkthrough BE-7"**.


**Files:**
- Create:
  - `backend/app/schemas/orders.py`
  - `backend/app/repositories/orders.py`
  - `backend/app/services/orders.py`
  - `backend/app/services/period_lock.py`
  - `backend/app/api/routes/orders.py`
- Modify: `backend/tests/factories.py`
- Test: `backend/tests/api/test_orders.py`

**Interfaces:**
- Consumes: `rate_for` (BE-6), `get_active_customer` (BE-5), `check_transition`, `is_editable` (BE-4), `month_start`, `next_month` (BE-2).
- Produces:
  - **`period_lock.py`:**
    - `is_period_locked(session, customer_id: int, month: date) -> bool`, following the rule in Global Constraints.
    - `assert_period_open(session, customer_id: int, on: date, field: str) -> None`, which raises `PERIOD_LOCKED`.
  - **Schemas:**
    - `OrderItemIn {product_id, quantity: int >= 1}`.
    - `OrderIn {customer_id, delivery_date, source: OrderSource = "whatsapp", notes: str | None, items: list[OrderItemIn] (min_length=1)}`. A model validator rejects a repeated `product_id` with field `items`.
    - `OrderItemOut {product_id, product_code, product_name, quantity, unit_price_cents, line_total_cents}`.
    - `OrderOut {id, customer_id, customer_name, delivery_date, source, status, notes, items, total_cents, created_at, created_by}`.
    - `StatusChange {status: OrderStatus}`.
  - **Routes:**

    | Method | Path | Notes |
    |---|---|---|
    | `GET` | `/orders` | Params `date_from`, `date_to`, `status` (repeatable), `customer_id`, `limit`, `offset`. Ordered by `delivery_date` desc, then `id` desc. |
    | `POST` | `/orders` | Returns 201. The customer must be active; each item's price is copied from `rate_for(product, delivery_date)`. |
    | `GET` | `/orders/{id}` | |
    | `PUT` | `/orders/{id}` | Takes the full `OrderIn`. Only when `is_editable`, otherwise `ORDER_NOT_EDITABLE`. Replaces the items and re-copies prices for the (possibly new) date. |
    | `POST` | `/orders/{id}/status` | Calls `check_transition`. When the target is `delivered`, also calls `assert_period_open(customer, delivery_date, "status")`. |

  - **Factories:**
    - `make_order(session, customer, delivery_date: date, items: dict[str, int], status=OrderStatus.PENDING) -> Order`
    - `make_statement(session, customer, month: date, status=StatementStatus.ISSUED, closing_cents=0) -> MonthlyStatement`
    - `make_billing_month(session, month: date) -> BillingMonth`

- [ ] **Step 1: Write the failing tests**
```python
def new_order(session, c, **kw):
    return {"customer_id": c.id, "delivery_date": "2026-11-05", "source": "whatsapp",
            "items": [{"product_id": product_id(session, "MINI_PAV"), "quantity": 20},
                      {"product_id": product_id(session, "MEDIUM_PAV"), "quantity": 10}], **kw}

def test_create_order_copies_prices(client, session):
    c = make_customer(session)
    r = client.post("/api/v1/orders", json=new_order(session, c))
    assert r.status_code == 201
    o = r.json()
    assert [i["unit_price_cents"] for i in o["items"]] == [40, 55]
    assert o["total_cents"] == 1350 and o["status"] == "pending"
    client.post("/api/v1/rates", json={"product_id": product_id(session, "MINI_PAV"),
                                       "price_cents": 45, "effective_from": "2026-11-01"})
    assert client.get(f"/api/v1/orders/{o['id']}").json()["items"][0]["unit_price_cents"] == 40

def test_no_rate_for_date(client, session):
    r = client.post("/api/v1/orders", json=new_order(session, make_customer(session), delivery_date="2025-12-31"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "NO_RATE_FOR_DATE"

@pytest.mark.parametrize("items,field", [            # Review Focus 5
    ([], "items"), ([{"product_id": "MINI_PAV", "quantity": 0}], "items.0.quantity"),
    ([{"product_id": "MINI_PAV", "quantity": 1}, {"product_id": "MINI_PAV", "quantity": 2}], "items")])
def test_bad_items(client, session, items, field):
    for i in items: i["product_id"] = product_id(session, i["product_id"])
    r = client.post("/api/v1/orders", json=new_order(session, make_customer(session), items=items))
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR" and r.json()["error"]["field"] == field

@pytest.mark.parametrize("action", ["deactivate", "anonymise"])   # Review Focus 3
def test_inactive_customer_cannot_order(client, session, action):
    c = make_customer(session)
    client.post(f"/api/v1/customers/{c.id}/{action}")
    assert client.post("/api/v1/orders", json=new_order(session, c)).json()["error"]["code"] == "CUSTOMER_INACTIVE"

def test_status_flow(client, session):
    o = make_order(session, make_customer(session), date(2026, 11, 5), {"ROTI": 5})
    for s in ["confirmed", "in_prep", "delivered"]:
        assert client.post(f"/api/v1/orders/{o.id}/status", json={"status": s}).json()["status"] == s
    r = client.post(f"/api/v1/orders/{o.id}/status", json={"status": "cancelled"})
    assert r.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

def test_not_editable_in_prep(client, session):
    c = make_customer(session)
    o = make_order(session, c, date(2026, 11, 5), {"ROTI": 5}, status=OrderStatus.IN_PREP)
    assert client.put(f"/api/v1/orders/{o.id}", json=new_order(session, c)).json()["error"]["code"] == "ORDER_NOT_EDITABLE"

def test_edit_confirmed_recopies_price_for_new_date(client, session): ...
    # rate MINI 45 from 2026-11-20; PUT with delivery_date 2026-11-21 -> MINI unit price 45

@pytest.mark.parametrize("lock", ["issued_statement", "later_month_generated"])  # Review Focus 4
def test_deliver_into_locked_month(client, session, lock):
    c = make_customer(session)
    o = make_order(session, c, date(2026, 10, 30), {"ROTI": 5}, status=OrderStatus.IN_PREP)
    if lock == "issued_statement":
        make_statement(session, c, date(2026, 10, 1))
    else:
        make_billing_month(session, date(2026, 11, 1))
    r = client.post(f"/api/v1/orders/{o.id}/status", json={"status": "delivered"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "PERIOD_LOCKED"
    assert client.get(f"/api/v1/orders/{o.id}").json()["status"] == "in_prep"

def test_list_filters(client, session): ...
    # orders on 11-04 and 11-05 with different statuses; date_from=date_to=2026-11-05&status=pending returns only that one
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/api/test_orders.py -v`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**
  Load items and products in one query with `selectinload` to avoid N+1 queries.

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend
git commit -m "feat(api): orders with price snapshots, status workflow and billing-period lock"
```

### BE-8: Payments and adjustments API

**Learn first**

- **Concepts:**
  - Validation that depends on 'today' (no future payments).
  - Reusing a guard (`assert_period_open`) across services.
- **Why it's built this way:** One lock rule, used everywhere, so bills can never change after they're issued.
- **Read:** [Pydantic validators](https://docs.pydantic.dev/latest/concepts/validators/)
- **Check yourself** (answer these in your learning note):
  1. Why are payments for inactive customers allowed?
  2. What is an adjustment, and why is it the only way to correct an issued month?
- **After the task:** write `docs/learning/BE-8.md`, then ask me for **"walkthrough BE-8"**.


**Files:**
- Create:
  - `backend/app/schemas/payments.py`
  - `backend/app/repositories/payments.py`
  - `backend/app/services/payments.py`
  - `backend/app/api/routes/payments.py`
  - `backend/app/api/routes/adjustments.py`
- Modify: `backend/tests/factories.py`
- Test: `backend/tests/api/test_payments.py`

**Interfaces:**
- Consumes: `assert_period_open` (BE-7), `parse_month`, `today_berlin` (BE-2).
- Produces:
  - **Payments:**
    - `PaymentIn {customer_id, amount_cents > 0, paid_on (not after today in Berlin, else 422 field paid_on), method: PaymentMethod, note}`.
    - `PaymentOut` = `PaymentIn` fields + `id`, `customer_name`, `created_by`.
    - `GET /payments?customer_id=&month=YYYY-MM`, `POST /payments` (201), `DELETE /payments/{id}` (204).
    - Create and delete call `assert_period_open(customer, paid_on, "paid_on")`.
    - Payments for inactive customers are allowed.
  - **Adjustments:**
    - `AdjustmentIn {customer_id, amount_cents != 0, applies_to_month: "YYYY-MM", reason (3–500 characters)}`.
    - `AdjustmentOut` = `AdjustmentIn` fields + `id`.
    - `GET /adjustments?customer_id=&month=`, `POST /adjustments`, `DELETE /adjustments/{id}`.
    - Lock check with field `applies_to_month`.
  - **Factory:** `make_payment(session, customer, amount_cents, paid_on) -> Payment`.

- [ ] **Step 1: Write the failing tests**
```python
@time_machine.travel(datetime(2026, 11, 3, 10, tzinfo=UTC), tick=False)
def test_record_and_list_payment(client, session):
    c = make_customer(session)
    r = client.post("/api/v1/payments", json={"customer_id": c.id, "amount_cents": 850,
                                              "paid_on": "2026-11-02", "method": "bank_transfer"})
    assert r.status_code == 201
    assert [p["amount_cents"] for p in client.get(f"/api/v1/payments?customer_id={c.id}&month=2026-11").json()] == [850]

@time_machine.travel(datetime(2026, 11, 3, 10, tzinfo=UTC), tick=False)
def test_future_payment_rejected(client, session):
    r = client.post("/api/v1/payments", json={"customer_id": make_customer(session).id, "amount_cents": 1,
                                              "paid_on": "2026-11-04", "method": "cash"})
    assert r.status_code == 422 and r.json()["error"]["field"] == "paid_on"

def test_payment_in_locked_month(client, session):
    c = make_customer(session); make_statement(session, c, date(2026, 10, 1))
    r = client.post("/api/v1/payments", json={"customer_id": c.id, "amount_cents": 100,
                                              "paid_on": "2026-10-15", "method": "cash"})
    assert r.json()["error"]["code"] == "PERIOD_LOCKED"

def test_delete_payment_in_locked_month(client, session): ...   # 409 PERIOD_LOCKED; row still listed
def test_adjustment_create_and_lock(client, session): ...       # -100 for 2026-12 ok; for locked 2026-10 → PERIOD_LOCKED
def test_adjustment_zero_rejected(client, session): ...         # 422 field amount_cents
def test_bad_month_param(client): ...                           # ?month=2026-13 → 422 field month
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/api/test_payments.py -v`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend
git commit -m "feat(api): payments and adjustments with period lock"
```

### BE-9: Monthly statements (generate, list, balances)

**Learn first**

- **Concepts:**
  - SQL aggregation with `GROUP BY` and `SUM`.
  - Running balances and carry-forward.
  - Idempotent regeneration of drafts.
- **Why it's built this way:** One query per kind instead of one per customer keeps it fast; months in sequence mean nothing is skipped.
- **Read:** [PostgreSQL aggregate functions](https://www.postgresql.org/docs/current/functions-aggregate.html)
- **Check yourself** (answer these in your learning note):
  1. Walk through the carry-forward example in the architecture §5.4.
  2. Why does generating November require October to be fully issued?
- **After the task:** write `docs/learning/BE-9.md`, then ask me for **"walkthrough BE-9"**.


**Files:**
- Create:
  - `backend/app/schemas/statements.py`
  - `backend/app/repositories/statements.py`
  - `backend/app/services/statements.py`
  - `backend/app/api/routes/statements.py`
- Modify:
  - `backend/app/schemas/customers.py` (add `CustomerDetail`)
  - `backend/app/api/routes/customers.py`
- Test: `backend/tests/api/test_statements.py`

**Interfaces:**
- Consumes: `compute_statement`, `StatementLine` (BE-4), `prev_month`, `next_month`, `parse_month`, `format_month` (BE-2).
- Produces:
  - **`generate_month(session, month: date, username: str) -> list[MonthlyStatement]`.** It runs these steps in order:
    1. If a `billing_months` row exists later than `month`, raise `LATER_MONTH_GENERATED`.
    2. If any `billing_months` row exists and either there is no row for `prev_month(month)` or any statement for `prev_month(month)` is a draft, raise `PREVIOUS_MONTH_NOT_ISSUED`.
    3. Delete the drafts for `month`.
    4. For each customer without an issued statement for `month`, compute:
       - `opening` = their closing for `prev_month`, or 0;
       - `orders` = the sum of line totals of delivered orders with `delivery_date` in the month;
       - `payments` = the sum of payments with `paid_on` in the month;
       - `adjustments` = the sum of adjustments for the month.
    5. Create a draft only if at least one of orders, payments or adjustments is non-empty, or `opening != 0`.
    6. Insert the `billing_months` row if it is missing.
  - **`statement_lines(session, customer_id: int, month: date) -> list[StatementLine]`:** delivered order items in the month, ordered by `delivery_date`, `order_id`, then product `sort_order`.
  - **`current_balance(session, customer_id: int) -> int`.**
    - Ledger start = the earliest `billing_months.month`; if there are none, there is no start limit.
    - Result = delivered order totals on or after the start − payments on or after the start + adjustments on or after the start.
  - **`outstanding_total(session) -> int`:** the sum of `max(current_balance, 0)` over all customers.
  - **Schemas:**
    - `StatementOut {id, customer_id, customer_name, month: "YYYY-MM", invoice_number: "YYYY-MM-<customer_id>", opening_cents, orders_cents, payments_cents, adjustments_cents, closing_cents, status, issued_at, has_pdf}`.
    - `StatementDetail` = `StatementOut` + `lines`.
    - `CustomerDetail` = `CustomerOut` + `balance_cents`.
  - **Routes:**
    - `POST /statements/generate {month}` returns `list[StatementOut]`.
    - `GET /statements?month=&customer_id=`.
    - `GET /statements/{id}` returns `StatementDetail`.
    - `GET /customers/{id}` now returns `CustomerDetail`.

- [ ] **Step 1: Write the failing tests**
```python
def setup_october(session):
    a, b = make_customer(session, name="A"), make_customer(session, name="B")
    make_order(session, a, date(2026, 10, 5), {"MINI_PAV": 20, "MEDIUM_PAV": 10}, status=OrderStatus.DELIVERED)  # 1350
    make_order(session, a, date(2026, 10, 6), {"ROTI": 5}, status=OrderStatus.CANCELLED)
    make_order(session, a, date(2026, 10, 7), {"ROTI": 5}, status=OrderStatus.PENDING)
    make_payment(session, a, 500, date(2026, 10, 20))
    return a, b

def test_generate_first_month(client, session):
    a, b = setup_october(session)
    st = client.post("/api/v1/statements/generate", json={"month": "2026-10"}).json()
    assert len(st) == 1                                    # B has no activity → no statement
    s = st[0]
    assert (s["opening_cents"], s["orders_cents"], s["payments_cents"], s["closing_cents"]) == (0, 1350, 500, 850)
    assert s["status"] == "draft" and s["invoice_number"] == f"2026-10-{a.id}"

def test_next_month_needs_previous_issued(client, session):
    setup_october(session); client.post("/api/v1/statements/generate", json={"month": "2026-10"})
    r = client.post("/api/v1/statements/generate", json={"month": "2026-11"})
    assert r.json()["error"]["code"] == "PREVIOUS_MONTH_NOT_ISSUED"

def test_carry_forward(client, session):
    a, _ = setup_october(session)
    client.post("/api/v1/statements/generate", json={"month": "2026-10"})
    session.execute(update(MonthlyStatement).values(status="issued"))
    make_order(session, a, date(2026, 11, 3), {"NORMAL_PAV": 10}, status=OrderStatus.DELIVERED)  # 600
    make_payment(session, a, 850, date(2026, 11, 4))
    s = client.post("/api/v1/statements/generate", json={"month": "2026-11"}).json()[0]
    assert (s["opening_cents"], s["closing_cents"]) == (850, 600)
    make_order(session, a, date(2026, 12, 1), {"ROTI": 2}, status=OrderStatus.DELIVERED)          # unbilled 200
    assert client.get(f"/api/v1/customers/{a.id}").json()["balance_cents"] == 800

def test_credit_carries_and_zero_balance_skipped(client, session): ...
    # overpayment → negative closing appears as next opening; customer with closing 0 and no activity gets no statement

def test_regenerate_replaces_drafts(client, session): ...
    # add a delivered October order after first generate; regenerate → orders_cents includes it, still 1 statement

def test_regenerate_after_later_month_rejected(client, session): ...   # LATER_MONTH_GENERATED

def test_detail_lines(client, session): ...
    # GET /statements/{id} lines: 2 lines on 2026-10-05: Mini pav 20×40=800, Medium pav 10×55=550
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/api/test_statements.py -v`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**
  Do the sums with SQL aggregates per customer (one query per kind, grouped by `customer_id`), not one query per customer.

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest -v`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add backend
git commit -m "feat(api): monthly statement generation, carry-forward and balances"
```

### BE-10: PDF bills, issuing and download

**Learn first**

- **Concepts:**
  - HTML-to-PDF rendering with Jinja2 and WeasyPrint.
  - Object storage and presigned URLs.
  - Testing AWS code with moto.
- **Why it's built this way:** PDFs are created once at issue and never change; short-lived links mean the bucket stays private.
- **Read:** [WeasyPrint tutorial](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) · [S3 presigned URLs](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html)
- **Check yourself** (answer these in your learning note):
  1. Why does the link expire after 5 minutes?
  2. Why must issuing wait until the month has ended?
- **After the task:** write `docs/learning/BE-10.md`, then ask me for **"walkthrough BE-10"**.


**Files:**
- Create:
  - `backend/app/pdf/render.py`
  - `backend/app/pdf/templates/bill.html`
  - `backend/app/storage.py`
- Modify:
  - `backend/app/services/statements.py`
  - `backend/app/api/routes/statements.py`
  - `backend/app/main.py`
  - `backend/tests/conftest.py`
- Test: `backend/tests/unit/test_pdf.py`, `backend/tests/api/test_issue.py`

**Interfaces:**
- Consumes: `StatementTotals`, `StatementLine` (BE-4), `statement_lines` (BE-9), `format_eur` (BE-2).
- Produces:
  - **`render.py`:**
    - `@dataclass BillData(business_name, business_address, customer_name, customer_address: str | None, invoice_number, issue_date: date, period_start: date, period_end: date, lines: list[StatementLine], totals: StatementTotals)`
    - `render_bill_pdf(data: BillData) -> bytes`. It renders the Jinja2 template, then WeasyPrint `HTML(string=...).write_pdf()`.
    - The template: A4 page; dates as `dd.mm.yyyy`; amounts through `format_eur`; lines grouped by delivery date; a totals block (Opening balance, Orders, Payments, Adjustments, **Amount due** / **Credit** when negative); and the exact §19 note.
  - **`storage.py`:**
    - `class BillStore(Protocol)` with `put(key: str, data: bytes) -> None` and `presigned_url(key: str, expires_seconds: int = 300) -> str`.
    - `S3BillStore(bucket: str, client)`. `put` uses `ContentType="application/pdf"` and `ServerSideEncryption="AES256"`.
    - `make_bill_store(settings) -> S3BillStore`, which uses `s3_endpoint_url` when it is set.
  - **`create_app(..., bill_store: BillStore | None = None)`.**
  - **`issue_statement(session, statement_id: int, username: str, store: BillStore, settings: Settings) -> MonthlyStatement`.** In order, it:
    1. raises `STATEMENT_ALREADY_ISSUED` if the statement is not a draft;
    2. raises `MONTH_NOT_ENDED` unless `today_berlin() > month_end(month)`;
    3. renders and stores the PDF at `statements/YYYY-MM/<customer_id>.pdf`;
    4. sets `status=issued`, `issued_at` and `pdf_s3_key`.
  - **Routes:**
    - `POST /statements/{id}/issue` returns `StatementOut`.
    - `GET /statements/{id}/pdf` returns `{"url": str}`, or `STATEMENT_NOT_ISSUED` for a draft.
  - **Test fixture:** `bill_store` is a moto `mock_aws` S3 bucket `test-bills`, passed into `create_app` for `client`.

- [ ] **Step 1: Write the failing tests**
```python
def test_pdf_contains_required_content():
    pdf = render_bill_pdf(BillData("Test Bakery", "Teststraße 1, 60311 Frankfurt", "Asha Patil", None,
        "2026-10-7", date(2026, 11, 1), date(2026, 10, 1), date(2026, 10, 31),
        [StatementLine(date(2026, 10, 5), 1, "Mini pav", 20, 40, 800)],
        StatementTotals(0, 800, 0, 50, 850)))
    text = "".join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages)
    for s in ["2026-10-7", "Asha Patil", "05.10.2026", "8,00 €", "8,50 €",
              "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."]:
        assert s in text

def draft_october(client, session): ...   # setup_october from BE-9 + generate → returns statement id

@time_machine.travel(datetime(2026, 10, 31, 21, 0, tzinfo=UTC), tick=False)   # 22:00 Berlin, 31 Oct
def test_issue_before_month_end_rejected(client, session):                     # Review Focus 2
    sid = draft_october(client, session)
    assert client.post(f"/api/v1/statements/{sid}/issue").json()["error"]["code"] == "MONTH_NOT_ENDED"

@time_machine.travel(datetime(2026, 10, 31, 23, 30, tzinfo=UTC), tick=False)   # 00:30 Berlin, 1 Nov
def test_issue_locks_and_stores_pdf(client, session, bill_store):
    sid = draft_october(client, session)
    s = client.post(f"/api/v1/statements/{sid}/issue").json()
    assert s["status"] == "issued" and s["has_pdf"] is True
    key = f"statements/2026-10/{s['customer_id']}.pdf"
    assert bill_store.client.head_object(Bucket="test-bills", Key=key)["ContentType"] == "application/pdf"
    assert client.post(f"/api/v1/statements/{sid}/issue").json()["error"]["code"] == "STATEMENT_ALREADY_ISSUED"
    r = client.post("/api/v1/payments", json={"customer_id": s["customer_id"], "amount_cents": 100,
                                              "paid_on": "2026-10-15", "method": "cash"})
    assert r.json()["error"]["code"] == "PERIOD_LOCKED"
    url = client.get(f"/api/v1/statements/{sid}/pdf").json()["url"]
    assert key in url and "X-Amz-Expires=300" in url

def test_pdf_of_draft_rejected(client, session): ...   # STATEMENT_NOT_ISSUED
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/unit/test_pdf.py tests/api/test_issue.py -v`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**
  Keep CSS inside the template. Use no external fonts or images, so Lambda needs no network access to render.

- [ ] **Step 4: Run the tests to verify they pass, and look at a real PDF**
  Run: `cd backend && uv run pytest -v`. Expected: PASS.
  Then write one sample PDF to `/tmp/bill.pdf` and open it. Check that it is readable on a phone screen at 100% zoom.

- [ ] **Step 5: Commit**
```bash
git add backend
git commit -m "feat(api): PDF bills, issuing locks the month, presigned downloads"
```

### BE-11: Dashboard API

**Learn first**

- **Concepts:**
  - Read models: an endpoint shaped for one screen.
  - Combining several queries into one response.
- **Why it's built this way:** The dashboard answers the morning question 'what do I bake today?' in one request.
- **Read:** [FastAPI: response model](https://fastapi.tiangolo.com/tutorial/response-model/)
- **Check yourself** (answer these in your learning note):
  1. Why are cancelled orders excluded from baking totals but counted in the status chips?
- **After the task:** write `docs/learning/BE-11.md`, then ask me for **"walkthrough BE-11"**.


**Files:**
- Create:
  - `backend/app/schemas/dashboard.py`
  - `backend/app/services/dashboard.py`
  - `backend/app/api/routes/dashboard.py`
- Test: `backend/tests/api/test_dashboard.py`

**Interfaces:**
- Consumes: `today_berlin` (BE-2), `outstanding_total` (BE-9).
- Produces: **`GET /dashboard`** returns `DashboardOut`:
  - `date: date` — today in Berlin.
  - `orders_by_status: dict[OrderStatus, int]` — today's orders; every status is present, with 0 when there are none.
  - `baking_totals: list[{product_code, product_name, quantity}]` — today's orders in `pending`, `confirmed` or `in_prep`, ordered by `sort_order`, with zero quantities left out.
  - `outstanding_cents: int`.

- [ ] **Step 1: Write the failing tests**
```python
@time_machine.travel(datetime(2026, 11, 3, 23, 30, tzinfo=UTC), tick=False)   # Review Focus 1
def test_dashboard_uses_berlin_today(client, session):
    c = make_customer(session); d = date(2026, 11, 4)
    make_order(session, c, d, {"MINI_PAV": 20}, status=OrderStatus.CONFIRMED)
    make_order(session, c, d, {"MINI_PAV": 10, "ROTI": 5})
    make_order(session, c, d, {"MINI_PAV": 99}, status=OrderStatus.CANCELLED)
    make_order(session, c, date(2026, 11, 3), {"MINI_PAV": 7})
    body = client.get("/api/v1/dashboard").json()
    assert body["date"] == "2026-11-04"
    assert [(t["product_code"], t["quantity"]) for t in body["baking_totals"]] == [("MINI_PAV", 30), ("ROTI", 5)]
    assert body["orders_by_status"] == {"pending": 1, "confirmed": 1, "in_prep": 0, "delivered": 0, "cancelled": 1}

def test_outstanding_ignores_credit(client, session): ...
    # A owes 600 (delivered order), B has credit -300 (payment only) → outstanding_cents == 600
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/api/test_dashboard.py -v`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest -v`
  Expected: PASS, with coverage at least 85%.

- [ ] **Step 5: Commit**
```bash
git add backend
git commit -m "feat(api): dashboard with Berlin-day baking totals and outstanding balance"
```

### BE-12: Lambda packaging, secrets, demo seed and OpenAPI export

**Learn first**

- **Concepts:**
  - Serverless: Lambda with a container image, the Mangum adapter.
  - Secrets from SSM at cold start.
  - OpenAPI as a contract between backend and frontend.
- **Why it's built this way:** The same app runs locally with uvicorn and on Lambda; the exported schema keeps frontend types in sync.
- **Read:** [Lambda container images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html) · [Mangum](https://github.com/Kludex/mangum)
- **Check yourself** (answer these in your learning note):
  1. What is a cold start and why read secrets then?
  2. Why fail CI when `openapi.json` changes without being committed?
- **After the task:** write `docs/learning/BE-12.md`, then ask me for **"walkthrough BE-12"**.


**Files:**
- Create:
  - `backend/app/lambda_handler.py`
  - `backend/app/secrets.py`
  - `backend/app/seed_demo.py`
  - `backend/app/export_openapi.py`
  - `backend/Dockerfile`
  - `backend/.dockerignore`
  - `backend/openapi.json` (generated)
- Modify:
  - `.github/workflows/backend.yml`
  - `README.md`
- Test: `backend/tests/unit/test_lambda.py`, `backend/tests/db/test_seed_demo.py`

**Interfaces:**
- Produces:
  - **`secrets.py`:** `load_ssm_parameters() -> None`. For each environment variable starting with `SSM_` (e.g. `SSM_DATABASE_URL=/bread/prod/database_url`), it reads the SecureString with decryption and sets `os.environ["DATABASE_URL"]`. It does nothing when no `SSM_` variables are set.
  - **`lambda_handler.py`:** calls `load_ssm_parameters()`, then `handler = Mangum(create_app(), lifespan="off")`.
  - **`seed_demo.py`:**
    - `seed_demo(session, today: date) -> None`. It raises `RuntimeError` if `get_settings().environment == "prod"`. It deletes all business data (everything except `products`, `product_rates` and the seeded rates), then creates, with Faker `de_DE` seed 42:
      - 8 customers;
      - orders across the previous month (delivered) and today to today+3 (every status present);
      - payments in the previous month;
      - drafts for the previous month via `generate_month`, left as drafts.
    - `reset_handler(event, context) -> dict` (Lambda entry point) calls `load_ssm_parameters()`, then `seed_demo`.
    - `main()` for `python -m app.seed_demo`.
  - **`export_openapi.py`:** `python -m app.export_openapi` writes `backend/openapi.json` (sorted keys, 2-space indent).
  - **`Dockerfile`:**
    - Based on `public.ecr.aws/lambda/python:3.12` (x86_64).
    - `dnf install -y pango` for WeasyPrint.
    - Copies `uv` from `ghcr.io/astral-sh/uv`; `uv export --frozen --no-dev > requirements.txt`; `pip install -r requirements.txt -t ${LAMBDA_TASK_ROOT}`.
    - Copies `app/`, `migrations/` and `alembic.ini`.
    - `CMD ["app.lambda_handler.handler"]`.

- [ ] **Step 1: Write the failing tests**
```python
def test_lambda_health(monkeypatch, test_env):          # test_env sets the Settings env vars
    from app.lambda_handler import handler
    event = {"version": "2.0", "routeKey": "$default", "rawPath": "/api/v1/health", "rawQueryString": "",
             "headers": {"host": "x"}, "requestContext": {"http": {"method": "GET", "path": "/api/v1/health",
             "sourceIp": "1.1.1.1", "protocol": "HTTP/1.1"}, "stage": "$default"}, "isBase64Encoded": False}
    assert handler(event, LambdaContext())["statusCode"] == 200

@mock_aws
def test_load_ssm_parameters(monkeypatch):
    boto3.client("ssm", region_name="eu-central-1").put_parameter(
        Name="/bread/demo/database_url", Value="postgresql+psycopg://x", Type="SecureString")
    monkeypatch.setenv("SSM_DATABASE_URL", "/bread/demo/database_url")
    load_ssm_parameters()
    assert os.environ["DATABASE_URL"] == "postgresql+psycopg://x"

@time_machine.travel(datetime(2026, 11, 3, 10, tzinfo=UTC), tick=False)
def test_seed_demo_is_repeatable(session):
    seed_demo(session, date(2026, 11, 3)); seed_demo(session, date(2026, 11, 3))
    assert session.scalar(select(func.count()).select_from(Customer)) == 8
    statuses = set(session.scalars(select(Order.status).where(Order.delivery_date >= date(2026, 11, 3))))
    assert statuses == set(OrderStatus)
    assert session.scalar(select(func.count()).select_from(MonthlyStatement)
                          .where(MonthlyStatement.month == date(2026, 10, 1))) > 0

def test_seed_demo_refuses_prod(session, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "prod"); get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        seed_demo(session, date(2026, 11, 3))
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/unit/test_lambda.py tests/db/test_seed_demo.py -v`
  Expected: FAIL.

- [ ] **Step 3: Implement the modules and Dockerfile**
  - Generate `openapi.json` and commit it.
  - In `backend.yml`, add the steps:
    - `uv run python -m app.export_openapi && git diff --exit-code openapi.json`
    - `docker build -t bread-api backend`
  - In `README.md`, add "Load demo data locally: `uv run python -m app.seed_demo`".

- [ ] **Step 4: Run all checks and verify they pass**
  Run: `cd backend && uv run pytest -v && docker build -t bread-api .`
  Expected: tests PASS and the image builds.

- [ ] **Step 5: Commit**
```bash
git add backend .github README.md
git commit -m "feat(backend): lambda container, ssm secrets, demo seed, openapi export"
```

---

### BE-13: Search API, index sync and the Postgres fallback

**Learn first**

- **Concepts:**
  - Adapter pattern: one interface, two implementations.
  - Contract tests run against both.
  - Eventual consistency: index after commit, reindex to repair.
  - Full-text queries, fuzziness, nested aggregations, highlighting.
- **Why it's built this way:** Elasticsearch on your laptop, free Postgres on AWS, same behaviour; writes never fail because search is down.
- **Read:** [Full-text queries](https://www.elastic.co/guide/en/elasticsearch/reference/current/full-text-queries.html) · [Aggregations](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations.html)
- **Check yourself** (answer these in your learning note):
  1. Why is Postgres the source of truth and not Elasticsearch?
  2. What does the HTML encoder in highlighting protect against?
- **After the task:** write `docs/learning/BE-13.md`, then ask me for **"walkthrough BE-13"**.


**Files:**
- Create:
  - `backend/app/search/base.py`
  - `backend/app/search/documents.py`
  - `backend/app/search/es_backend.py`
  - `backend/app/search/pg_backend.py`
  - `backend/app/search/sync.py`
  - `backend/app/search/reindex.py`
  - `backend/app/schemas/search.py`
  - `backend/app/api/routes/search.py`
- Modify:
  - `backend/app/db.py` (`get_session`)
  - `backend/app/main.py` (`create_app` gains `search_backend`)
  - `backend/app/services/customers.py`, `backend/app/services/orders.py` (call `mark_dirty`)
  - `backend/app/seed_demo.py` (rebuild the index after seeding)
  - `backend/tests/conftest.py`
- Test: `backend/tests/search/test_search_contract.py`, `backend/tests/search/test_sync.py`

**Interfaces:**
- Consumes: `INDEX_NAME`, `ensure_index`, `recreate_index` (DB-5); `Customer`, `Order` models (DB-3); `parse_month`, `format_month` (BE-2).
- Produces:
  - **`schemas/search.py`:**
    - `DocKind = Literal["customer", "order"]`
    - `SearchQuery {q: str = "" (max 200, stripped), kind: DocKind | None, status: OrderStatus | None, month: str | None ("YYYY-MM"), limit: int = 20 (1–50)}`
    - `SearchHit {kind, id, title, subtitle, delivery_date: date | None, status: OrderStatus | None, total_cents: int | None, highlight: str | None}`
      - A customer hit has title = name and subtitle = phone.
      - An order hit has title `"Order #<id> · <customer name>"` and subtitle = the item summary `"20× Mini pav, 10× Medium pav"`.
    - `ProductTotal {product_code, product_name, quantity}`
    - `SearchResult {total: int, hits: list[SearchHit], facets: {kind: dict[str, int], status: dict[str, int], month: dict[str, int]}, product_totals: list[ProductTotal]}`
    - `product_totals` covers only the matching **orders**, ordered by product `sort_order`.
  - **`base.py`:** `class SearchBackend(Protocol)` with:
    - `index_customer(self, session: Session, customer: Customer) -> None`. It also re-indexes that customer's orders, because the orders carry the customer's name and phone.
    - `index_order(self, order: Order) -> None`
    - `search(self, session: Session, query: SearchQuery) -> SearchResult`
    - `rebuild(self, session: Session) -> int` returns the number of documents indexed.
  - **`documents.py`:** `customer_doc(c: Customer) -> dict` and `order_doc(o: Order) -> dict`, following the DB-5 fields. Document IDs are `customer-<id>` and `order-<id>`.
  - **`es_backend.py`:** `ElasticsearchBackend(es: Elasticsearch)`.
    - **Query:**
      - `bool.should` of a `multi_match` on `customer_name^3`, `customer_phone` and `notes` (`fuzziness: "AUTO"`), plus a `nested` `match` on `items.product_name`.
      - `minimum_should_match: 1`.
      - `match_all` when `q` is empty.
      - Filters are `term` queries.
    - **Aggregations:**
      - `terms` on `kind`, `status` and `month` (size 24);
      - `nested` on `items`, then `terms` on `items.product_code`, then `sum` of `items.quantity`.
    - **Highlight:** on `customer_name` and `notes`, with `encoder: "html"`, so text from the database is escaped and only `<em>` tags are added.
    - Writes use `refresh="wait_for"`, so a change is searchable as soon as the request returns.
  - **`pg_backend.py`:** `PostgresBackend()`.
    - The index methods do nothing, and `rebuild` returns 0.
    - `search` uses `ILIKE '%q%'` on customer name, phone and notes, plus `EXISTS` on product names.
    - Facets are `GROUP BY` counts, and product totals are `SUM(quantity)`.
    - It returns the same `SearchResult` shape, with `highlight=None`.
  - **`sync.py`:**
    - `mark_dirty(session: Session, kind: DocKind, entity_id: int) -> None` adds the ID to `session.info["search_dirty"]`.
    - `apply_pending(session: Session, backend: SearchBackend) -> None` loads each dirty entity and indexes it. It catches **every** exception and logs a warning `search_sync_failed` with the kind and ID. It never raises.
  - **`get_session`** now calls `apply_pending(session, request.app.state.search)` after a successful commit.
  - **Calls to `mark_dirty`:**
    - **Customers** (BE-5): create, update, deactivate, activate and anonymise.
    - **Orders** (BE-7): create, update and status change.
  - **`create_app(..., search_backend: SearchBackend | None = None)`.** The default comes from settings:
    - `elasticsearch` gives an `ElasticsearchBackend` (and calls `ensure_index` at startup);
    - `postgres` gives a `PostgresBackend`.
  - **Routes:**
    - `GET /search` with `SearchQuery` as query parameters returns `SearchResult`.
    - `POST /search/reindex` returns `{"indexed": int}`. It calls `recreate_index` and then indexes everything.
  - **`reindex.py`:** `python -m app.search.reindex` runs the same rebuild from the command line.
  - **Test fixtures:**
    - `search_client`: parametrised over `["postgres", "elasticsearch"]`. Each run builds a `client` with that backend. For Elasticsearch it calls `recreate_index` first.
    - `es_client`: the Elasticsearch variant only.

- [ ] **Step 1: Write the failing contract tests** (each runs once per backend)
```python
def seed(client, session):
    asha = make_customer(session, name="Asha Patil")
    ravi = make_customer(session, name="Ravi Kumar")
    for c in (asha, ravi):
        client.patch(f"/api/v1/customers/{c.id}", json={"notes": "Weekend regular"})  # marks dirty via API
    o1 = client.post("/api/v1/orders", json={"customer_id": asha.id, "delivery_date": "2026-11-05",
        "items": [{"product_id": product_id(session, "MINI_PAV"), "quantity": 20}]}).json()
    client.post("/api/v1/orders", json={"customer_id": asha.id, "delivery_date": "2026-10-20",
        "items": [{"product_id": product_id(session, "MINI_PAV"), "quantity": 10},
                  {"product_id": product_id(session, "ROTI"), "quantity": 5}]})
    client.post("/api/v1/orders", json={"customer_id": ravi.id, "delivery_date": "2026-11-06",
        "items": [{"product_id": product_id(session, "BROWNIE"), "quantity": 4}]})
    return asha, ravi, o1

def test_finds_customer_and_their_orders(search_client, session):
    asha, *_ = seed(search_client, session)
    r = search_client.get("/api/v1/search?q=asha").json()
    assert r["facets"]["kind"] == {"customer": 1, "order": 2}
    assert {h["title"] for h in r["hits"] if h["kind"] == "customer"} == {"Asha Patil"}

def test_finds_orders_by_product(search_client, session):
    seed(search_client, session)
    r = search_client.get("/api/v1/search?q=brownie&kind=order").json()
    assert [h["subtitle"] for h in r["hits"]] == ["4× Brownie"]

def test_filters_and_product_totals(search_client, session):
    seed(search_client, session)
    r = search_client.get("/api/v1/search?q=asha&kind=order&month=2026-11").json()
    assert r["total"] == 1
    r = search_client.get("/api/v1/search?kind=order").json()
    assert [(p["product_code"], p["quantity"]) for p in r["product_totals"]] == [
        ("MINI_PAV", 30), ("BROWNIE", 4), ("ROTI", 5)]
    assert r["facets"]["month"] == {"2026-11": 2, "2026-10": 1}

def test_anonymised_customer_not_findable(search_client, session):
    asha, *_ = seed(search_client, session)
    search_client.post(f"/api/v1/customers/{asha.id}/anonymise")
    assert search_client.get("/api/v1/search?q=asha").json()["total"] == 0

def test_status_change_is_searchable(search_client, session):
    _, _, o1 = seed(search_client, session)
    search_client.post(f"/api/v1/orders/{o1['id']}/status", json={"status": "confirmed"})
    assert search_client.get("/api/v1/search?status=confirmed").json()["total"] == 1

def test_bad_params(search_client):
    assert search_client.get("/api/v1/search?month=2026-13").json()["error"]["field"] == "month"
    assert search_client.get("/api/v1/search?limit=500").status_code == 422
```
  Product totals are ordered by `sort_order`: Mini pav (1), Brownie (4), Roti (5).

- [ ] **Step 2: Write the failing Elasticsearch-only and sync tests**
```python
def test_typo_tolerance(es_client, session):           # Elasticsearch only
    seed(es_client, session)
    assert any(h["title"] == "Asha Patil" for h in es_client.get("/api/v1/search?q=ahsa").json()["hits"])

def test_highlight_is_escaped(es_client, session):
    es_client.post("/api/v1/customers", json={"name": "<script>x</script> Asha"})
    h = es_client.get("/api/v1/search?q=asha").json()["hits"][0]["highlight"]
    assert "<script>" not in h and "&lt;script&gt;" in h and "<em>" in h

def test_index_down_does_not_block_writes(client_with_dead_es, caplog):
    r = client_with_dead_es.post("/api/v1/customers", json={"name": "Asha"})
    assert r.status_code == 201
    assert "search_sync_failed" in caplog.text

def test_reindex_rebuilds(es_client, session, es_url):
    seed(es_client, session)
    Elasticsearch(es_url).indices.delete(index=INDEX_NAME)
    assert es_client.post("/api/v1/search/reindex").json()["indexed"] == 5   # 2 customers + 3 orders
    assert es_client.get("/api/v1/search?q=asha").json()["total"] == 3
```
  `client_with_dead_es` uses `ElasticsearchBackend(Elasticsearch("http://localhost:1", request_timeout=1))`.

- [ ] **Step 3: Run the tests to verify they fail**
  Run: `cd backend && uv run pytest tests/search -v`
  Expected: FAIL.

- [ ] **Step 4: Implement the interfaces above**
  Start with `PostgresBackend` until the contract tests pass for `postgres`, then add `ElasticsearchBackend`.
  Map aggregation buckets to the same dict shape in both backends; leave out empty buckets.

- [ ] **Step 5: Run the tests to verify they pass**
  Run: `cd backend && uv run pytest -v`
  Expected: PASS, with coverage still at least 85%.

- [ ] **Step 6: Regenerate the API schema and update the README**
  - Run `uv run python -m app.export_openapi`.
  - In the README, add "Search locally: `docker compose up -d search`, then `uv run python -m app.search.reindex`".
  - Also note in the README that deployed environments use the Postgres search backend.

- [ ] **Step 7: Commit**
```bash
git add backend README.md
git commit -m "feat(search): search API with facets, elasticsearch sync and postgres fallback"
```

---

# Group 4 — Frontend (Angular)

**Conventions for every frontend task:**
- **Components:** standalone only (no NgModules), `ChangeDetectionStrategy.OnPush`, signals for component state, `inject()` instead of constructor injection, and built-in control flow (`@if`, `@for` with `track`).
- **Services:** return `Observable`s from `HttpClient`. Components turn them into signals with `toSignal`, or use the `async` pipe.
- **Pages:** lazy-loaded with `loadComponent`.
- **Unit tests:**
  - Components are tested with Angular Testing Library (`render`, `screen`, `userEvent`).
  - HTTP is tested with `provideHttpClient()` plus `provideHttpClientTesting()` and `HttpTestingController`.
  - Every spec ends with `httpMock.verify()`.
- **Paths:** all under `frontend/src/app/` unless stated otherwise.

### FE-1: Angular scaffold, Material, tooling and CI

**Learn first**

- **Concepts:**
  - Angular CLI workspace, standalone components, strict mode.
  - Angular Material themes; self-hosted fonts.
  - Frontend CI: lint, test, build.
- **Why it's built this way:** Strict templates catch errors at build time; no Google Fonts avoids a known GDPR problem in Germany.
- **Read:** [Angular: installation](https://angular.dev/installation) · [Angular Material: getting started](https://material.angular.dev/guide/getting-started)
- **Check yourself** (answer these in your learning note):
  1. What does `strictTemplates` check?
  2. Why proxy `/api` in development instead of enabling CORS?
- **After the task:** write `docs/learning/FE-1.md`, then ask me for **"walkthrough FE-1"**.


**Files:**
- Create:
  - `frontend/` (Angular CLI)
  - `frontend/proxy.conf.json`
  - `frontend/public/config.json`
  - `frontend/.prettierrc`
  - `.github/workflows/frontend.yml`
- Test: `frontend/src/app/app.spec.ts`

**Interfaces:**
- Produces:
  - **npm scripts:**

    | Script | Runs |
    |---|---|
    | `start` | `ng serve --proxy-config proxy.conf.json` |
    | `build` | `ng build` |
    | `test` | `ng test --no-watch --coverage` |
    | `lint` | `ng lint` |
    | `format:check` | `prettier --check "src/**/*.{ts,html,scss}"` |
    | `gen:api` | `openapi-typescript ../backend/openapi.json -o src/app/core/api/schema.d.ts` |
    | `e2e` | `playwright test` |

  - **Dev proxy (`proxy.conf.json`):** `{"/api": {"target": "http://localhost:8000", "secure": false}}`.
  - **Build output:** `dist/frontend/browser/`.
  - **Local runtime config (`public/config.json`):**
```json
{ "apiBaseUrl": "/api/v1", "authMode": "dev", "cognitoUserPoolId": "", "cognitoClientId": "", "demo": false }
```

- [ ] **Step 1: Create the project**
  - Run from the repo root: `npx @angular/cli@latest new frontend --routing --style=scss --ssr=false --skip-git`.
  - If the CLI asks for a test runner, choose **Vitest**.
  - Keep the default strict mode: `strict`, `strictTemplates` and `strictInjectionParameters` must be `true` in `tsconfig.json`.

- [ ] **Step 2: Add libraries**
  - **Angular Material:** run `cd frontend && npx ng add @angular/material`.
    - Pick a theme.
    - Answer **No** to "global typography" and the Google Fonts links (GDPR, see below).
  - **Fonts and icons, self-hosted:**
    - Run `npm i @fontsource/roboto material-symbols`.
    - Import them in `src/styles.scss`.
    - Remove any `fonts.googleapis.com` links from `index.html`.

    In Germany, loading Google Fonts from Google's servers has been ruled a GDPR violation (LG München, 2022), and the CSP from AWS-4 would block them anyway.
  - **Linting:** run `npx ng add @angular-eslint/schematics`.
  - **Runtime dependencies:** `npm i aws-amplify angularx-qrcode date-fns date-fns-tz`.
  - **Dev dependencies:** `npm i -D @testing-library/angular @testing-library/user-event @testing-library/jest-dom openapi-typescript prettier @playwright/test`.

- [ ] **Step 3: Global styles for phones**
  In `src/styles.scss`:
  - set `html { -webkit-text-size-adjust: 100%; }`;
  - set the font size of `input, select, textarea` to `16px` (stops iOS zooming in);
  - add `.touch { min-width: 44px; min-height: 44px; }`.

- [ ] **Step 4: Write the failing smoke test**
```ts
it("shows the app title", async () => {
  await render(App);
  expect(screen.getByRole("heading", { name: "Daily Loaf" })).toBeInTheDocument();
});
```

- [ ] **Step 5: Run it to verify it fails, then make it pass**
  Run: `cd frontend && npm test`. Expected: FAIL.
  Replace the CLI's demo template in `app.html` with `<h1>Daily Loaf</h1>` and `<router-outlet />`, then run `npm test` again. Expected: PASS.

- [ ] **Step 6: Add `.github/workflows/frontend.yml`**
  - **Triggers:** pull requests and pushes to `main`, for `frontend/**` and `backend/openapi.json`.
  - **One job, named `frontend`.** Steps:
    1. `actions/setup-node` with `node-version: 26` and npm cache.
    2. `npm ci`.
    3. `npm run gen:api && git diff --exit-code src/app/core/api/schema.d.ts`.
    4. `npm run lint`, then `npm run format:check`, then `npm test`.
    5. `npm audit --audit-level=high --omit=dev`.
    6. `npm run build`. The build type-checks the templates.
  - Run every step with `working-directory: frontend`.

- [ ] **Step 7: Run every check and verify it passes**
  Run: `cd frontend && npm run gen:api && npm run lint && npm test && npm run build`
  Expected: all pass. `npm start` serves http://localhost:4200.

- [ ] **Step 8: Commit**
```bash
git add frontend .github/workflows/frontend.yml
git commit -m "chore(frontend): angular scaffold with material, eslint, vitest and CI"
```
  After merging, add `frontend` to the required checks (GIT-2, Step 2).

### FE-2: Core — runtime config, formatting, error handling and interceptors

**Learn first**

- **Concepts:**
  - Runtime config loaded before bootstrap; InjectionTokens.
  - Pure pipes for formatting.
  - Functional HTTP interceptors; `HttpContext`; testing with `HttpTestingController`.
- **Why it's built this way:** Cross-cutting concerns (tokens, errors, toasts) live in one place, so pages stay simple.
- **Read:** [Interceptors](https://angular.dev/guide/http/interceptors) · [Testing HTTP requests](https://angular.dev/guide/http/testing) · [Dependency injection](https://angular.dev/guide/di)
- **Check yourself** (answer these in your learning note):
  1. In which order do interceptors run on the request and on the response?
  2. Why load `config.json` at runtime instead of using environment files?
- **After the task:** write `docs/learning/FE-2.md`, then ask me for **"walkthrough FE-2"**.


**Files:**
- Create:
  - `core/config/app-config.ts`
  - `core/format/{money.ts, dates.ts, eur.pipe.ts, de-date.pipe.ts}`
  - `core/api/{api-error.ts, error-messages.ts, api-types.ts, interceptors.ts}`
- Modify: `frontend/src/main.ts`, `app.config.ts`
- Test: `core/format/money.spec.ts`, `dates.spec.ts`, `core/api/interceptors.spec.ts`

**Interfaces:**
- Produces:
  - **`app-config.ts`:**
    - `interface AppConfig { apiBaseUrl: string; authMode: "cognito" | "dev"; cognitoUserPoolId: string; cognitoClientId: string; demo: boolean }`
    - `const APP_CONFIG = new InjectionToken<AppConfig>("APP_CONFIG")`
    - `loadAppConfig(fetchFn = fetch): Promise<AppConfig>` fetches `/config.json` with `cache: "no-store"`.
    - `main.ts` awaits `loadAppConfig()` and then calls `bootstrapApplication(App, appConfig(config))`. `appConfig` becomes a function of `AppConfig` that returns the `ApplicationConfig`.
  - **Formatting:**
    - `money.ts`:
      - `formatEur(cents: number): string`, the same output as the backend's `format_eur`.
      - `parseEurToCents(input: string): number | null`. It accepts `,` or `.` as the decimal separator with at most 2 decimals, and returns `null` for anything else.
    - `dates.ts`:
      - `todayBerlin(now?: Date): string` (`YYYY-MM-DD`)
      - `addDays(iso: string, n: number): string`
      - `formatDate(iso: string): string` (`dd.MM.yyyy`)
      - `formatMonth(month: string): string` (`"October 2026"`)
      - `prevMonth(month: string): string`
      - `monthOf(iso: string): string`
    - Pipes: `EurPipe` (name `eur`) and `DeDatePipe` (name `deDate`), both standalone and pure.
  - **`api-types.ts`:** `type Schemas = components["schemas"]` and readable aliases, e.g. `type Customer = Schemas["CustomerOut"]`, `type Order = Schemas["OrderOut"]`.
  - **`api-error.ts`:** `class ApiError extends Error { code: string; field: string | null; status: number; requestId: string | null }`, plus `toApiError(e: HttpErrorResponse): ApiError`.
  - **`error-messages.ts`:** `messageFor(e: unknown): string`, using the error-code table in Global Constraints.
  - **`interceptors.ts`** (all functional `HttpInterceptorFn`s):
    - `TOKEN_PROVIDER = new InjectionToken<() => Promise<string | null>>("TOKEN_PROVIDER")` and `UNAUTHORIZED_HANDLER = new InjectionToken<() => void>("UNAUTHORIZED_HANDLER")`. FE-3 provides both.
    - `authTokenInterceptor` adds `Authorization: Bearer <token>`, but only to URLs that start with `apiBaseUrl`. It uses `from(getToken()).pipe(switchMap(...))`.
    - `apiErrorInterceptor` turns an `HttpErrorResponse` into `ApiError` with `catchError` and calls the unauthorized handler on a 401.
    - `SKIP_ERROR_TOAST = new HttpContextToken<boolean>(() => false)`.
    - `errorToastInterceptor`: for non-GET requests, it shows `messageFor(err)` in a `MatSnackBar` unless the request's context has `SKIP_ERROR_TOAST` set. Pages that show the error next to a field set it.
  - **`app.config.ts`** provides:
    - `provideHttpClient(withInterceptors([authTokenInterceptor, apiErrorInterceptor, errorToastInterceptor]))`
    - `provideZonelessChangeDetection()`
    - `provideRouter(routes, withComponentInputBinding())`
    - `provideAnimationsAsync()`
    - `{ provide: APP_CONFIG, useValue: config }`
    - `{ provide: LOCALE_ID, useValue: "de-DE" }` (register `localeDe`)

- [ ] **Step 1: Write the failing tests**
```ts
it.each([[55, "0,55 €"], [123456, "1.234,56 €"], [-500, "-5,00 €"]])("formatEur(%i)", (c, t) =>
  expect(formatEur(c)).toBe(t));
it.each([["0,55", 55], ["0.55", 55], ["1", 100], ["12,5", 1250], ["abc", null], ["1,234", null], ["", null]])(
  "parseEurToCents(%s)", (i, c) => expect(parseEurToCents(i)).toBe(c));
it("todayBerlin after midnight", () => expect(todayBerlin(new Date("2026-11-03T23:30:00Z"))).toBe("2026-11-04"));
it("formatDate", () => expect(formatDate("2026-11-05")).toBe("05.11.2026"));

describe("interceptors", () => {
  // TestBed: provideHttpClient(withInterceptors([...])), provideHttpClientTesting(),
  // APP_CONFIG {apiBaseUrl: "/api/v1"}, TOKEN_PROVIDER () => Promise.resolve("t-1"), UNAUTHORIZED_HANDLER spy
  it("adds the bearer token to API calls only", async () => {
    http.get("/api/v1/me").subscribe(); http.get("/config.json").subscribe();
    await flushMicrotasks();
    expect(httpMock.expectOne("/api/v1/me").request.headers.get("Authorization")).toBe("Bearer t-1");
    expect(httpMock.expectOne("/config.json").request.headers.has("Authorization")).toBe(false);
  });
  it("turns a 409 into ApiError", async () => {
    // flush {"error":{"code":"PERIOD_LOCKED","message":"x","field":"paid_on"}}, status 409, header X-Request-ID abc
    // expect error instanceof ApiError, code PERIOD_LOCKED, field paid_on, requestId "abc"
    // and messageFor(error) === "This month is already billed for this customer."
  });
  it("calls the unauthorized handler on 401", async () => { /* spy called once */ });
  it("toasts mutation errors but not GETs or SKIP_ERROR_TOAST", async () => { /* MatSnackBar.open spy */ });
});
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd frontend && npm test`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd frontend && npm test && npm run build`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add frontend/src
git commit -m "feat(frontend): runtime config, euro/date pipes, api errors and http interceptors"
```

### FE-3: Sign-in (Cognito with MFA, local dev mode)

**Learn first**

- **Concepts:**
  - Route guards returning a `UrlTree`.
  - Abstract classes as DI tokens; factory providers.
  - Signals for UI state; Cognito sign-in steps and TOTP MFA.
- **Why it's built this way:** Swapping `AuthApi` for a fake makes the login page testable without AWS.
- **Read:** [Route guards](https://angular.dev/guide/routing/route-guards) · [Signals](https://angular.dev/guide/signals)
- **Check yourself** (answer these in your learning note):
  1. Why does the guard return a UrlTree instead of calling `router.navigate`?
  2. Why is the MFA input `inputmode=numeric` with `autocomplete=one-time-code`?
- **After the task:** write `docs/learning/FE-3.md`, then ask me for **"walkthrough FE-3"**.


**Files:**
- Create: `core/auth/{auth-api.ts, amplify-auth-api.ts, dev-auth-api.ts, auth.service.ts, auth.guard.ts, login.page.ts, login.page.html}`
- Modify: `app.config.ts`, `app.routes.ts`
- Test: `core/auth/login.page.spec.ts`, `core/auth/auth.guard.spec.ts`

**Interfaces:**
- Consumes: `APP_CONFIG`, `TOKEN_PROVIDER`, `UNAUTHORIZED_HANDLER` (FE-2).
- Produces:
  - **`auth-api.ts`:** `abstract class AuthApi`, used as the DI token:
    - `type SignInStep = "DONE" | "MFA_CODE" | "MFA_SETUP" | "NEW_PASSWORD"`
    - `signIn(email, password): Promise<SignInStep>`
    - `confirmMfa(code): Promise<SignInStep>`
    - `totpSetupUri(): Promise<string>`
    - `newPassword(pw): Promise<SignInStep>`
    - `accessToken(): Promise<string | null>`
    - `signOut(): Promise<void>`
  - **Implementations:**
    - `AmplifyAuthApi` is the only file that imports `aws-amplify`. It calls `Amplify.configure` with the pool and client IDs from `APP_CONFIG`.
    - `DevAuthApi` returns `"DONE"` and the token `"dev-token"`.
    - Provider: `{ provide: AuthApi, useFactory: () => inject(APP_CONFIG).authMode === "dev" ? new DevAuthApi() : new AmplifyAuthApi(inject(APP_CONFIG)) }`.
  - **`AuthService`** (`providedIn: "root"`):
    - `status = signal<"loading" | "signedIn" | "signedOut">("loading")`
    - `init(): Promise<void>`, run with `provideAppInitializer`
    - `signOut(): Promise<void>`, which navigates to `/login`
    - `handleUnauthorized(): void`
    - `app.config.ts` provides `TOKEN_PROVIDER` as `() => inject(AuthApi).accessToken()` and `UNAUTHORIZED_HANDLER` as `() => inject(AuthService).handleUnauthorized()`. Bind them through `useFactory`.
  - **`authGuard: CanActivateFn`** returns `true` when signed in, otherwise `router.createUrlTree(["/login"], { queryParams: { next: state.url } })`.
  - **`LoginPage`:**
    - A step signal drives the screens: email and password, then a new password, then MFA setup (`<qrcode>` from `angularx-qrcode` plus the secret as text), then the MFA code.
    - The MFA input has `inputmode="numeric"`, `autocomplete="one-time-code"`, `maxlength="6"` and the label "6-digit code".
    - Error messages:
      - wrong credentials: "Incorrect email or password."
      - wrong code: "That code didn't work. Try the newest code."
    - On `DONE`, navigate to `next` or `/`.

- [ ] **Step 1: Write the failing tests** (provide a fake `AuthApi` with `useValue`, which is Angular DI in place of module mocking)
```ts
it("wrong password shows message", async () => {
  await render(LoginPage, { providers: [{ provide: AuthApi, useValue: fakeAuth({ signIn: reject("NotAuthorizedException") }) }] });
  await userEvent.type(screen.getByLabelText("Email"), "a@b.de");
  await userEvent.type(screen.getByLabelText("Password"), "wrong-password");
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
  expect(await screen.findByText("Incorrect email or password.")).toBeInTheDocument();
});
it("MFA step shows a numeric one-time-code input", async () => {
  // signIn resolves "MFA_CODE"
  const input = await screen.findByLabelText("6-digit code");
  expect(input).toHaveAttribute("inputmode", "numeric");
  expect(input).toHaveAttribute("autocomplete", "one-time-code");
});
it("success navigates to next", async () => { /* route /login?next=/orders → Router.navigateByUrl("/orders") */ });
it("guard redirects signed-out users", () => {
  // TestBed.runInInjectionContext(() => authGuard(route, { url: "/customers" } as RouterStateSnapshot))
  // → UrlTree "/login?next=%2Fcustomers"
});
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd frontend && npm test`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**
  The login form is a typed Reactive Form: `fb.nonNullable.group({ email: ["", [Validators.required, Validators.email]], password: ["", Validators.required] })`.

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd frontend && npm test`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add frontend/src
git commit -m "feat(frontend): cognito sign-in with TOTP MFA, auth guard and dev mode"
```

### FE-4: App shell, mobile navigation and shared components

**Learn first**

- **Concepts:**
  - Layout with CDK `BreakpointObserver`.
  - Content projection and `ngTemplateOutlet`.
  - `ControlValueAccessor` and `NG_VALIDATORS` for custom form controls.
- **Why it's built this way:** Phone-first navigation, and reusable building blocks that every page uses.
- **Read:** [CDK layout](https://material.angular.dev/cdk/layout/overview) · [ControlValueAccessor](https://angular.dev/api/forms/ControlValueAccessor)
- **Check yourself** (answer these in your learning note):
  1. Which four methods does a ControlValueAccessor implement, and when is each called?
  2. Why decide the layout in CSS for the list, but in code for the navigation?
- **After the task:** write `docs/learning/FE-4.md`, then ask me for **"walkthrough FE-4"**.


**Files:**
- Create:
  - `layout/{shell.component.ts, shell.component.html, more-sheet.component.ts, demo-banner.component.ts, nav-items.ts}`
  - `shared/{responsive-list.component.ts, card-template.directive.ts, money-input.component.ts, confirm.service.ts, confirm-dialog.component.ts, validators.ts}`
- Modify: `app.routes.ts`
- Test: `layout/shell.component.spec.ts`, `shared/responsive-list.component.spec.ts`, `shared/money-input.component.spec.ts`

**Interfaces:**
- Produces:
  - **Routes:**
    - `/login` sits outside the shell.
    - Every other route sits inside `ShellComponent`, with `canActivate: [authGuard]`, and is lazy-loaded: `/`, `/orders`, `/orders/new`, `/orders/:id`, `/customers`, `/customers/new`, `/customers/:id`, `/rates`, `/payments`, `/bills`, `/search`.
  - **`nav-items.ts`:**
    - `PRIMARY`: Dashboard `/`, Orders `/orders`, Customers `/customers`.
    - `MORE`: Search `/search`, Rates `/rates`, Payments `/payments`, Bills `/bills`.
  - **`ShellComponent`:**
    - `isDesktop = toSignal(inject(BreakpointObserver).observe("(min-width: 1024px)").pipe(map(r => r.matches)))`.
    - **Desktop:** a `mat-sidenav-container` with `mode="side"` that lists all items and Sign out.
    - **Phone:** a fixed bottom `<nav aria-label="Main (mobile)">` with the 3 primary links plus a **More** button.
      - It uses `padding-bottom: env(safe-area-inset-bottom)`.
      - Links use `routerLinkActive` with `ariaCurrentWhenActive="page"`, and every target has the `touch` class.
    - **More** opens `MatBottomSheet` with `MoreSheetComponent`, which lists the `MORE` items and **Sign out**.
  - **`DemoBannerComponent`:** shown only when `APP_CONFIG.demo`, with the text "Demo — data resets nightly".
  - **`ResponsiveListComponent<T>`:**
    - Inputs: `items: input.required<T[]>()`, `columns: input.required<{ header: string; cell: (t: T) => string }[]>()`, `empty: input.required<string>()`.
    - The card template comes from `@ContentChild(CardTemplateDirective)`, used as `<ng-template appCard let-item>`.
    - It renders a `<table>` (shown from 768px) and a `role="list"` card list (shown below 768px) through CSS media queries, using `ngTemplateOutlet`.
  - **`MoneyInputComponent`:**
    - Implements `ControlValueAccessor` and `Validator` (`NG_VALUE_ACCESSOR` and `NG_VALIDATORS` with `multi: true`).
    - Its value is cents (`number | null`), and the text input has `inputmode="decimal"`.
    - Invalid text gives the error `{ money: true }`, displayed as "Enter an amount like 0,55".
  - **`validators.ts`:** `notBlank: ValidatorFn` (returns `{ required: true }` for whitespace) and `positiveCents: ValidatorFn`.
  - **`ConfirmService.confirm(opts: { title: string; description: string; confirmLabel: string }): Observable<boolean>`**, which opens `ConfirmDialogComponent` through `MatDialog`.

- [ ] **Step 1: Write the failing tests**
```ts
it("phone nav has primary tabs and More", async () => {
  // render ShellComponent with BreakpointObserver stubbed to matches:false, at route /orders
  const nav = screen.getByRole("navigation", { name: "Main (mobile)" });
  expect(within(nav).getAllByRole("link").map(l => l.textContent?.trim())).toEqual(["Dashboard", "Orders", "Customers"]);
  expect(within(nav).getByRole("link", { name: "Orders" })).toHaveAttribute("aria-current", "page");
  await userEvent.click(within(nav).getByRole("button", { name: "More" }));
  for (const n of ["Search", "Rates", "Payments", "Bills", "Sign out"]) expect(await screen.findByText(n)).toBeVisible();
});
it("desktop shows sidenav instead", async () => { /* matches:true → no "Main (mobile)" nav; sidenav has all items */ });
it("demo banner only in demo", async () => { /* APP_CONFIG demo true/false */ });
it("ResponsiveList renders table rows and cards", async () => {
  // host component with 2 items → 2 table body rows and 2 listitems; [] → empty text
});
it("MoneyInput writes cents to the form control", async () => {
  // host with FormControl<number|null>; type "8,50" → control.value === 850; type "abc" → control.errors {money:true}
});
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd frontend && npm test`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**
  Each page is a placeholder component with an `<h1>` until its feature task.

- [ ] **Step 4: Run the tests to verify they pass, and check by hand**
  Run: `cd frontend && npm test`. Expected: PASS.
  Then run `npm start` and open Chrome DevTools device mode at 360×740:
  - the bottom bar is visible and nothing scrolls horizontally;
  - at 1280px the sidenav is shown instead.

- [ ] **Step 5: Commit**
```bash
git add frontend/src
git commit -m "feat(frontend): shell with bottom tabs and sidenav, responsive list, money input CVA"
```

### FE-5: Customers screens

**Learn first**

- **Concepts:**
  - RxJS: `debounceTime`, `distinctUntilChanged`, `switchMap`.
  - Typed Reactive Forms and custom validators.
  - Route input binding (`withComponentInputBinding`).
- **Why it's built this way:** Search sends one request per pause and cancels outdated ones; forms are typed end to end.
- **Read:** [RxJS operators](https://rxjs.dev/guide/operators) · [Reactive forms](https://angular.dev/guide/forms/reactive-forms)
- **Check yourself** (answer these in your learning note):
  1. What would `mergeMap` do differently in the search box?
  2. Why `nonNullable` form groups?
- **After the task:** write `docs/learning/FE-5.md`, then ask me for **"walkthrough FE-5"**.


**Files:**
- Create: `features/customers/{customers.service.ts, customers.page.ts, customer-form.page.ts, customer-detail.page.ts}` (each page with its `.html`)
- Test: `features/customers/customers.page.spec.ts`, `customer-form.page.spec.ts`, `customer-detail.page.spec.ts`, `customers.service.spec.ts`

**Interfaces:**
- Consumes: `ResponsiveListComponent`, `ConfirmService`, `notBlank` (FE-4); `EurPipe`, `api-types` (FE-2).
- Produces:
  - **`CustomersService`:**
    - `list(p: { q?: string; includeInactive?: boolean }): Observable<Page<Customer>>`
    - `get(id: number): Observable<CustomerDetail>`
    - `create(body: CustomerIn): Observable<Customer>`
    - `update(id: number, body: CustomerPatch): Observable<Customer>`
    - `action(id: number, a: "deactivate" | "activate" | "anonymise"): Observable<Customer>`
    - Query parameters are built with `HttpParams`; empty values are left out.
  - **`CustomersPage`:**
    - `search = new FormControl("", { nonNullable: true })`.
    - Results: `toSignal(combineLatest([search.valueChanges.pipe(startWith(""), debounceTime(300), distinctUntilChanged()), showInactive$]).pipe(switchMap(([q, inc]) => service.list({ q, includeInactive: inc }))))`. `switchMap` cancels an older request when a newer one starts.
    - Cards show the name, the phone as a `tel:` link, and an "Inactive" chip.
  - **`CustomerFormPage`** (create, and edit when the route has `:id`):
    - `fb.nonNullable.group({ name: ["", [notBlank, Validators.maxLength(200)]], phone: ["", Validators.maxLength(50)], address: [""], notes: [""] })`.
    - The `name` error text is "Name is required".
    - The phone field is `type="tel"`.
  - **`CustomerDetailPage`:**
    - `id = input.required<number>({ transform: numberAttribute })`, which uses route input binding.
    - Shows the balance as "Owes 8,50 €", or "Credit 2,00 €" when it is negative.
    - Shows the last 20 orders (`GET /orders?customer_id=&limit=20`).
    - Buttons: Edit, New order (`/orders/new?customer=<id>`), Deactivate/Activate and Anonymise.
    - Anonymise asks for confirmation first: "This permanently removes name, phone, address and notes. Bills are kept."

- [ ] **Step 1: Write the failing tests**
```ts
it("search waits 300 ms and cancels older requests", async () => {
  // fake timers; type "as" then "ash" within 300 ms → only one request ?q=ash; respond → "Asha Patil" shown
});
it("blank name is blocked", async () => { /* type "  " → submit → "Name is required"; httpMock.expectNone POST */ });
it("detail shows balance and orders", async () => { /* balance_cents 850 → "Owes 8,50 €" */ });
it("anonymise needs confirmation", async () => { /* confirm false → no POST; true → POST /customers/1/anonymise */ });
it("service drops empty params", () => { /* list({q:""}) → URL "/api/v1/customers" with no q */ });
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd frontend && npm test`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd frontend && npm test`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add frontend/src
git commit -m "feat(frontend): customers list with rxjs search, typed form and detail"
```

### FE-6: Rates screen

**Learn first**

- **Concepts:**
  - Material dialogs returning results.
  - Showing a server error under a specific field.
- **Why it's built this way:** The user sees exactly which field to fix, not a generic toast.
- **Read:** [Material dialog](https://material.angular.dev/components/dialog/overview)
- **Check yourself** (answer these in your learning note):
  1. How does `SKIP_ERROR_TOAST` change what the user sees?
- **After the task:** write `docs/learning/FE-6.md`, then ask me for **"walkthrough FE-6"**.


**Files:**
- Create: `features/rates/{products.service.ts, rates.page.ts, new-rate.dialog.ts}`
- Test: `features/rates/rates.page.spec.ts`

**Interfaces:**
- Consumes: `MoneyInputComponent`, `positiveCents` (FE-4); `todayBerlin`, `addDays` (FE-2); `SKIP_ERROR_TOAST`.
- Produces:
  - **`ProductsService`:**
    - `list(on?: string): Observable<Product[]>`
    - `rates(productId: number): Observable<Rate[]>`
    - `createRate(body: RateIn): Observable<Rate>`
  - **`RatesPage`:** one `mat-card` per product with its name and current price, plus a "Price history" `mat-expansion-panel`.
  - **`NewRateDialog`:**
    - `MoneyInput`, required, with `positiveCents`.
    - `effective_from`, defaulting to `addDays(todayBerlin(), 1)`.
    - It sends the request with `SKIP_ERROR_TOAST` and shows `RATE_EXISTS` under the date field.
    - When it closes with a result, the page reloads.

- [ ] **Step 1: Write the failing tests**
```ts
it("shows current prices", async () => { /* "Medium pav" … "0,55 €" */ });
it("new price posts cents and date", async () => { /* "0,58", 2026-11-10 → body {product_id, price_cents: 58, effective_from: "2026-11-10"} */ });
it("duplicate date shows field error", async () => { /* 409 RATE_EXISTS → "A price already starts on this date." under date */ });
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd frontend && npm test`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd frontend && npm test`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add frontend/src/app/features/rates
git commit -m "feat(frontend): rates page with price history"
```

### FE-7: Orders screens (phone-first order entry)

**Learn first**

- **Concepts:**
  - Combining signals and Observables (`toSignal`, `computed`).
  - Dynamic form groups per product.
  - Mapping server field paths back to form controls.
  - Sticky footers and touch targets on phones.
- **Why it's built this way:** The most-used screen: fast with one thumb, and impossible to submit with a wrong total.
- **Read:** [Signals: computed](https://angular.dev/guide/signals#computed-signals) · [RxJS interop](https://angular.dev/guide/signals/rxjs-interop)
- **Check yourself** (answer these in your learning note):
  1. When the delivery date changes, what happens step by step?
  2. Why does the total use `computed()` instead of a method called in the template?
- **After the task:** write `docs/learning/FE-7.md`, then ask me for **"walkthrough FE-7"**.


**Files:**
- Create:
  - `features/orders/{orders.service.ts, status-actions.ts, orders.page.ts, order-form.component.ts, new-order.page.ts, order-detail.page.ts}`
  - `shared/quantity-stepper.component.ts`
- Test: `features/orders/order-form.component.spec.ts`, `orders.page.spec.ts`, `shared/quantity-stepper.component.spec.ts`

**Interfaces:**
- Consumes: `ProductsService.list(on)` (FE-6), `CustomersService.list` (FE-5), `ApiError`, `messageFor`, `SKIP_ERROR_TOAST` (FE-2), `ConfirmService` (FE-4).
- Produces:
  - **`OrdersService`:**
    - `list(f: { dateFrom?: string; dateTo?: string; status?: OrderStatus[]; customerId?: number }): Observable<Page<Order>>`
    - `get(id: number): Observable<Order>`
    - `create(body: OrderIn): Observable<Order>`
    - `update(id: number, body: OrderIn): Observable<Order>`
    - `changeStatus(id: number, status: OrderStatus): Observable<Order>`
  - **`status-actions.ts`:**
    - `NEXT_ACTION: Partial<Record<OrderStatus, { label: string; target: OrderStatus }>>`:
      - `pending` → "Confirm" (`confirmed`)
      - `confirmed` → "Start prep" (`in_prep`)
      - `in_prep` → "Mark delivered" (`delivered`)
    - `STATUS_LABEL`: Pending, Confirmed, In prep, Delivered, Cancelled.
  - **`QuantityStepperComponent`:** a `ControlValueAccessor` (value `number`, minimum 0). It has a − button, a number input (`inputmode="numeric"`) and a + button, each with the `touch` class, plus an `aria-label` from the `label` input.
  - **`OrderFormComponent`** (shared by new and edit):
    - Inputs: `initial = input<Order | null>(null)` and `customerId = input<number | null>(null)`. Output: `saved = output<Order>()`.
    - **Form:**
      - `customerId` uses a `mat-autocomplete` over active customers.
      - `deliveryDate` defaults to `addDays(todayBerlin(), 1)`.
      - `source` is a `mat-button-toggle-group` (WhatsApp / Phone / Other, default WhatsApp).
      - `items` is a `FormGroup<Record<productCode, FormControl<number>>>`, with one stepper per product.
      - `notes`.
    - **Prices:**
      - `products = toSignal(deliveryDate.valueChanges.pipe(startWith(initial), switchMap(d => productsService.list(d))))`.
      - `total = computed(() => sum of quantity × price_cents)`, where the quantities come from a `toSignal` of the items' `valueChanges`.
    - **Sticky footer** (`position: sticky; bottom: 0`): the total formatted with `eur`, and a Save button.
    - **Sending:** only items with a quantity above 0 are sent.
      - With none, it shows "Add at least one item" and sends nothing.
      - If a product's price is `null` for the date, it shows "No price for this date" and disables Save.
    - **Server errors:** requests use `SKIP_ERROR_TOAST`. A 422 with field `items.N.quantity` sets `{ server: message }` on that product's control, using the N-th item that was sent.
  - **`OrdersPage`:**
    - Filters: date (default today, with Today and Tomorrow chips) and status chips, synced to query parameters.
    - Each card shows the customer, the item summary ("20× Mini pav, 10× Medium pav"), the total, a status chip, the next-action button and a `mat-menu` (Edit when editable, Cancel with confirmation).
  - **`OrderDetailPage`:** a read-only view with the same actions, and `OrderFormComponent` when the order is editable.

- [ ] **Step 1: Write the failing tests**
```ts
it("live total from steppers", async () => { /* prices 40/55; Mini + ×20, Medium ×10 → footer "13,50 €" */ });
it("no items blocks submit", async () => { /* Save → "Add at least one item"; httpMock.expectNone */ });   // Review Focus 5
it("server field error shown under the right stepper", async () => {
  // Mini 3, Medium 5, Roti 0 → items sent [Mini, Medium] in product order;
  // 422 field "items.1.quantity" → message inside the Medium pav stepper group
});
it("missing price disables save", async () => { /* products?on=… price null → "No price for this date"; Save disabled */ });
it("changing date reloads prices and cancels the old request", async () => { /* two dates quickly → first request cancelled */ });
it("next action advances status", async () => { /* pending card → "Confirm" → POST /orders/1/status {status:"confirmed"} */ });
it("stepper never goes below 0", async () => { /* value 0, click − → stays 0 */ });
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd frontend && npm test`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass, and check on a phone screen**
  Run: `cd frontend && npm test`. Expected: PASS.
  Then in DevTools at 360×740, check that the whole new-order form plus its footer works with one thumb.

- [ ] **Step 5: Commit**
```bash
git add frontend/src
git commit -m "feat(frontend): orders list, status actions and phone-first order form"
```

### FE-8: Payments screen

**Learn first**

- **Concepts:**
  - Shared services between features.
  - Refreshing data after a change with a `Subject`.
- **Why it's built this way:** Balances on screen always match what was just recorded.
- **Read:** [RxJS Subject](https://rxjs.dev/guide/subject)
- **Check yourself** (answer these in your learning note):
  1. What's the difference between a Subject and a BehaviorSubject?
- **After the task:** write `docs/learning/FE-8.md`, then ask me for **"walkthrough FE-8"**.


**Files:**
- Create: `features/payments/{payments.service.ts, statements.service.ts, payments.page.ts, payment-form.component.ts}`
- Test: `features/payments/payments.page.spec.ts`

**Interfaces:**
- Consumes: `MoneyInputComponent`, `ResponsiveListComponent`, `ConfirmService`, `CustomersService`.
- Produces:
  - **`PaymentsService`:**
    - `list(p: { customerId?: number; month?: string }): Observable<Payment[]>`
    - `create(body: PaymentIn): Observable<Payment>`
    - `delete(id: number): Observable<void>`
  - **`StatementsService`** (reused in FE-9):
    - `list(p: { month: string; customerId?: number }): Observable<Statement[]>`
    - `generate(month: string): Observable<Statement[]>`
    - `issue(id: number): Observable<Statement>`
    - `pdfUrl(id: number): Observable<string>`
  - **`PaymentsPage`:**
    - A month selector (default: current month) and a customer filter.
    - The `PaymentFormComponent`: customer, amount, date (default today), method (Cash / Bank transfer / Other) and note. It uses `SKIP_ERROR_TOAST`, so field errors appear under their fields.
    - The payments list, with delete and confirmation.
    - A "Monthly balances" section: the statements for the month (opening, orders, payments and closing per customer), or "No bills generated for this month yet."
    - After any change, the page re-fetches through a `refresh$` subject.

- [ ] **Step 1: Write the failing tests**
```ts
it("records payment in cents", async () => { /* "8,50", Bank transfer → POST {amount_cents: 850, method: "bank_transfer"} */ });
it("future date error under field", async () => { /* 422 field paid_on → message under date input */ });
it("monthly balances listed", async () => { /* closing_cents 600 → "6,00 €" for customer A */ });
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd frontend && npm test`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd frontend && npm test`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add frontend/src/app/features/payments
git commit -m "feat(frontend): payments and monthly balances"
```

### FE-9: Bills screen

**Learn first**

- **Concepts:**
  - Sequential async work with `concatMap`.
  - Confirming irreversible actions.
  - Opening downloads safely with `noopener`.
- **Why it's built this way:** Issuing locks a month for good, so the UI makes that explicit and stops at the first problem.
- **Read:** [concatMap](https://rxjs.dev/api/operators/concatMap)
- **Check yourself** (answer these in your learning note):
  1. Why `concatMap` and not `forkJoin` for 'Issue all'?
  2. What does `noopener` protect against?
- **After the task:** write `docs/learning/FE-9.md`, then ask me for **"walkthrough FE-9"**.


**Files:**
- Create: `features/bills/bills.page.ts`
- Test: `features/bills/bills.page.spec.ts`

**Interfaces:**
- Consumes: `StatementsService` (FE-8), `ConfirmService`, `prevMonth`, `formatMonth`.
- Produces:
  - **`BillsPage`:**
    - A month picker (default `prevMonth` of the current month).
    - A **Generate drafts** button.
    - The statement list: customer, invoice number, closing amount, and a Draft/Issued chip.
  - **Draft actions:** **Issue**, after the confirmation "Issuing locks <Month> for <customer>. Corrections then go into the next month as adjustments."
  - **Issued actions:** **Download PDF**. It calls `pdfUrl(id)`, then `window.open(url, "_blank", "noopener")`, so on phones the PDF opens in the built-in viewer.
  - **Issue all drafts** runs `from(drafts).pipe(concatMap(d => issue(d.id)))`, which issues one at a time and stops at the first error.
  - The `MONTH_NOT_ENDED`, `PREVIOUS_MONTH_NOT_ISSUED` and `LATER_MONTH_GENERATED` messages appear in an alert above the list (`SKIP_ERROR_TOAST`).

- [ ] **Step 1: Write the failing tests**
```ts
it("generate creates drafts for month", async () => { /* POST /statements/generate {month:"2026-10"} → 1 draft row */ });
it("issue asks for confirmation then posts", async () => { /* dialog text contains "October 2026" */ });
it("issue all stops at first error", async () => { /* 2 drafts, first 409 → second never requested */ });
it("download opens presigned url", async () => { /* vi.spyOn(window, "open") called with returned url */ });
it("month not ended shows alert", async () => { /* 409 MONTH_NOT_ENDED → "Bills can be issued after the month ends." */ });
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd frontend && npm test`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd frontend && npm test`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add frontend/src/app/features/bills
git commit -m "feat(frontend): bills generate, issue and download"
```

### FE-10: Dashboard screen

**Learn first**

- **Concepts:**
  - Polling with `timer` and refreshing on `visibilitychange`.
  - Turning streams into signals.
- **Why it's built this way:** The dashboard stays current on a kitchen phone without a manual refresh.
- **Read:** [RxJS timer](https://rxjs.dev/api/index/function/timer)
- **Check yourself** (answer these in your learning note):
  1. Why also refresh when the tab becomes visible?
- **After the task:** write `docs/learning/FE-10.md`, then ask me for **"walkthrough FE-10"**.


**Files:**
- Create: `features/dashboard/{dashboard.service.ts, dashboard.page.ts}`
- Test: `features/dashboard/dashboard.page.spec.ts`

**Interfaces:**
- Consumes: `GET /dashboard` (BE-11), the `deDate` and `eur` pipes, `STATUS_LABEL` (FE-7).
- Produces:
  - **`DashboardService.get(): Observable<Dashboard>`.**
  - **`DashboardPage`:**
    - Data: `toSignal(merge(timer(0, 60_000), fromEvent(document, "visibilitychange").pipe(filter(() => !document.hidden))).pipe(switchMap(() => service.get())))`.
    - Heading: "Today · 05.11.2026".
    - A **To bake** card listing product and quantity, or "Nothing to bake today".
    - Status count chips that link to `/orders?status=<s>&date=<today>`.
    - An **Outstanding** card with the total.
    - A **New order** button.

- [ ] **Step 1: Write the failing tests**
```ts
it("shows bake list and outstanding", async () => { /* Mini 30, Roti 5, outstanding 600 → "30", "Mini pav", "6,00 €" */ });
it("status chip links to filtered orders", async () => { /* Pending 1 → href contains status=pending */ });
it("refreshes every minute", async () => { /* fake timers: advance 60 s → second GET /dashboard */ });
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd frontend && npm test`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd frontend && npm test`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add frontend/src/app/features/dashboard
git commit -m "feat(frontend): dashboard"
```

### FE-11: Search and analysis screen

**Learn first**

- **Concepts:**
  - The URL as the single source of state (query params).
  - Facets and aggregations in the UI.
  - Safe HTML rendering and Angular's sanitizer.
- **Why it's built this way:** This is the 'aggregation and analysis' screen from the BKA posting: shareable, reload-safe, and safe against injection.
- **Read:** [Router: query params](https://angular.dev/guide/routing/read-route-state) · [Angular security](https://angular.dev/guide/security)
- **Check yourself** (answer these in your learning note):
  1. Why store filters in the URL instead of component state?
  2. What exactly does Angular's sanitizer remove from `[innerHTML]`?
- **After the task:** write `docs/learning/FE-11.md`, then ask me for **"walkthrough FE-11"**.


**Files:**
- Create: `features/search/{search.service.ts, search.page.ts, search.page.html}`
- Test: `features/search/search.page.spec.ts`

**Interfaces:**
- Consumes: `GET /search` (BE-13), `ResponsiveListComponent`, the `eur` and `deDate` pipes.
- Produces:
  - **`SearchService.search(q: SearchParams): Observable<SearchResult>`**, with `type SearchParams = { q?: string; kind?: "customer" | "order"; status?: OrderStatus; month?: string }`.
  - **`SearchPage`:**
    - **The URL is the single source of state:** `params = toSignal(route.queryParamMap.pipe(map(toSearchParams)))`.
    - **Results:** `toSignal(route.queryParamMap.pipe(map(toSearchParams), distinctUntilChanged(isEqual), switchMap(p => service.search(p).pipe(catchError(() => of(EMPTY_RESULT))))))`.
    - **The search box** writes to the URL: `debounceTime(300)` on its value changes, then `router.navigate([], { queryParams: { q }, queryParamsHandling: "merge", replaceUrl: true })`.
    - **Filter chips** (`mat-chip-listbox`): kind, status and month, from `facets`, each showing its count ("Orders 12"). Selecting a chip sets that query parameter; selecting it again removes it.
    - **Results:** customer hits link to `/customers/:id` and order hits to `/orders/:id`.
      - The highlight is rendered with `[innerHTML]`. Angular's sanitizer runs on it, and the backend already escaped it (BE-13).
    - **A "Product totals" table** for the current results.
    - Empty state: "No matches. Try fewer words or remove a filter."

- [ ] **Step 1: Write the failing tests**
```ts
it("typing updates the URL after 300 ms", async () => { /* fake timers; type "asha" → router.navigate with {q:"asha"} once */ });
it("loading with query params searches once", async () => { /* /search?q=asha&kind=order → one GET /search?q=asha&kind=order */ });
it("facet chips show counts and toggle filters", async () => {
  // facets.kind {customer:1, order:2} → chips "Customers 1", "Orders 2"; click Orders → queryParams kind=order; click again → kind removed
});
it("product totals table", async () => { /* MINI_PAV 30 → row "Mini pav" "30" */ });
it("highlight cannot inject script", async () => {
  // highlight "<em>Asha</em><img src=x onerror=alert(1)>" → <em> rendered, no onerror attribute in DOM
});
it("search error shows empty state, page keeps working", async () => { /* 500 → empty-state text; next search still sent */ });
```

- [ ] **Step 2: Run the tests to verify they fail**
  Run: `cd frontend && npm test`
  Expected: FAIL.

- [ ] **Step 3: Implement the interfaces above**

- [ ] **Step 4: Run the tests to verify they pass**
  Run: `cd frontend && npm test`
  Expected: PASS.

- [ ] **Step 5: Commit**
```bash
git add frontend/src/app/features/search
git commit -m "feat(frontend): search page with URL-driven filters, facets and product totals"
```

### FE-12: End-to-end tests on desktop and phone (Playwright)

**Learn first**

- **Concepts:**
  - End-to-end testing with Playwright; device emulation.
  - Traces for debugging failures.
- **Why it's built this way:** One test proves the whole business flow works on desktop and on a phone.
- **Read:** [Playwright: getting started](https://playwright.dev/docs/intro)
- **Check yourself** (answer these in your learning note):
  1. Why only a few end-to-end tests compared with unit tests?
  2. How do you avoid flaky waits?
- **After the task:** write `docs/learning/FE-12.md`, then ask me for **"walkthrough FE-12"**.


**Files:**
- Create:
  - `frontend/playwright.config.ts`
  - `frontend/e2e/full-flow.spec.ts`
  - `frontend/e2e/mobile-layout.spec.ts`
- Modify: `README.md`

**Interfaces:**
- **Config:**
  - Projects: `desktop` (Chromium, 1280×800) and `phone` (`devices["Pixel 7"]`).
  - `baseURL = process.env.E2E_BASE_URL ?? "http://localhost:4200"`.
  - Credentials from `E2E_EMAIL` and `E2E_PASSWORD` (any values in dev mode).
  - `retries: 1` in CI, and trace `on-first-retry`.
- **The full flow relies on demo data:** the previous month has drafts, so it is generated but not locked for a new customer.

- [ ] **Step 1: Write the end-to-end tests**
```ts
test("order to bill", async ({ page }) => {
  // 1 sign in
  // 2 Customers → New → name `E2E ${Date.now()}` → Save
  // 3 New order for this customer, delivery date = last day of previous month, Mini pav 20 → Save
  // 4 Confirm → Start prep → Mark delivered
  // 5 Search → type the customer name → the order appears with "20× Mini pav"
  // 6 Payments → record 5,00 € dated last day of previous month
  // 7 Bills → previous month → Generate drafts → Issue this customer's bill → "Issued"
  // 8 Download PDF → a popup whose URL contains "/statements/" and ".pdf"
});
```
```ts
for (const path of ["/", "/orders", "/orders/new", "/customers", "/rates", "/payments", "/bills", "/search"]) {
  test(`no horizontal scroll on ${path}`, async ({ page }) => {
    await signIn(page); await page.goto(path);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
}
```

- [ ] **Step 2: Run them locally against the dev stack**
  Start the stack:
  - `docker compose up -d`
  - Backend: `cd backend && uv run alembic upgrade head && uv run python -m app.seed_demo && uv run python -m app.search.reindex && uv run uvicorn app.main:app`
  - Frontend, in another terminal: `cd frontend && npm start` (`public/config.json` has `authMode: "dev"`)

  Then run `cd frontend && npx playwright install chromium && npm run e2e`.
  Expected: both projects PASS. If they fail, fix the app, not the test.

- [ ] **Step 3: Update the README**
  Add a "Run end-to-end tests" section, and a "Screenshots" section with one desktop and one phone screenshot.

- [ ] **Step 4: Commit**
```bash
git add frontend/playwright.config.ts frontend/e2e README.md docs
git commit -m "test(e2e): order-to-bill flow and no-horizontal-scroll checks on desktop and phone"
```

---

# Group 5 — AWS & deployment [MANUAL — Suhasini]

Do these in order. Every command uses `--profile bread-admin --region eu-central-1`, written below as `$AWS`. Set it with `export AWS="--profile bread-admin --region eu-central-1"`. **Do the demo environment first, then prod.** Never paste connection strings or passwords into files in the repo.

### AWS-1: Secure the AWS account and set a cost alarm

**Learn first**

- **Concepts:**
  - Root user vs IAM Identity Center users; MFA.
  - Budgets and free-tier alerts.
- **Why it's built this way:** Most AWS horror stories are unprotected root accounts and surprise bills; this prevents both.
- **Read:** [IAM Identity Center: getting started](https://docs.aws.amazon.com/singlesignon/latest/userguide/getting-started.html)
- **Check yourself** (answer these in your learning note):
  1. Why never create access keys for root?
- **After the task:** write `docs/learning/AWS-1.md`, then ask me for **"walkthrough AWS-1"**.


- [ ] **Step 1: Create the account and protect root**
  1. Create an AWS account at aws.amazon.com and choose the Basic (free) support plan.
  2. Sign in as root and go to Security credentials → **Assign MFA** (authenticator app).
  3. Never create root access keys.

- [ ] **Step 2: Set up an admin user with IAM Identity Center**
  1. In the console, switch the region to **Europe (Frankfurt) eu-central-1**.
  2. Open IAM Identity Center → **Enable**.
  3. Create a user `suhasini` with your email.
  4. Create the permission set `AdministratorAccess` (predefined) and assign it to the user in your account.
  5. Accept the invite email, set a password and register MFA.

- [ ] **Step 3: Configure the CLI**
  1. Run `aws configure sso` with:
     - SSO start URL from the Identity Center dashboard
     - region `eu-central-1`
     - profile name `bread-admin`
  2. Check it: `aws sts get-caller-identity --profile bread-admin` should show your account ID.
  3. Write the account ID down (you'll need it as `<ACCOUNT_ID>`).

- [ ] **Step 4: Set up billing alerts**
  1. In Billing → Billing preferences, turn on **Invoice delivery by email** and **Free tier usage alerts**.
  2. Optionally, under Payment preferences, set the default currency to EUR.
  3. In Billing → Budgets → Create budget, use the **Monthly cost budget** template:
     - Amount: 5 (EUR, or USD 5 if the currency is USD).
     - Email recipients: you.

  This creates alerts at 85% actual and 100% forecast.

### AWS-2: Neon databases and secrets in SSM

**Learn first**

- **Concepts:**
  - Managed Postgres branches.
  - SSM Parameter Store SecureString.
- **Why it's built this way:** Secrets live in one encrypted place and never in Git or Terraform.
- **Read:** [Neon docs](https://neon.tech/docs/introduction) · [SSM Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- **Check yourself** (answer these in your learning note):
  1. Why a pooled connection string for Lambda?
- **After the task:** write `docs/learning/AWS-2.md`, then ask me for **"walkthrough AWS-2"**.


- [ ] **Step 1: Create the databases**
  1. Sign up at neon.tech (free plan).
  2. Create project `bread-app` with:
     - Postgres 16
     - Region **AWS Europe Central 1 (Frankfurt)**
     - Database `bread`
  3. Create a second branch named `demo` from `main`.

  `main` is prod and `demo` is demo, so they are separate databases.

- [ ] **Step 2: Create one role per branch**
  In each branch, open Roles → **New role** `bread_app`, and copy each branch's **pooled** connection string. Change the start to `postgresql+psycopg://` and make sure it ends with `?sslmode=require`.

- [ ] **Step 3: Store the connection strings in SSM** (they never go into Terraform or Git)
```bash
aws ssm put-parameter $AWS --name /bread/demo/database_url --type SecureString --value '<demo connection string>'
aws ssm put-parameter $AWS --name /bread/prod/database_url --type SecureString --value '<prod connection string>'
```
  Check: `aws ssm get-parameter $AWS --name /bread/demo/database_url --with-decryption --query Parameter.Value` prints the string.

- [ ] **Step 4: Create the schema and demo data from your laptop**
```bash
cd backend
export DATABASE_URL=$(aws ssm get-parameter $AWS --name /bread/demo/database_url --with-decryption --query Parameter.Value --output text)
uv run alembic upgrade head
ENVIRONMENT=demo uv run python -m app.seed_demo
unset DATABASE_URL
```
  Repeat `alembic upgrade head` with `/bread/prod/database_url`. **Do not seed prod**; `seed_demo` refuses anyway.

- [ ] **Step 5: Close the terminal** so the connection string isn't left in your shell history session.

### AWS-3: Terraform state bucket and lock table

**Learn first**

- **Concepts:**
  - Infrastructure as code; remote state and locking.
- **Why it's built this way:** Shared, encrypted state means infrastructure changes are tracked and can't clash.
- **Read:** [Terraform: get started with AWS](https://developer.hashicorp.com/terraform/tutorials/aws-get-started)
- **Check yourself** (answer these in your learning note):
  1. What would happen if two people ran `terraform apply` without a lock?
- **After the task:** write `docs/learning/AWS-3.md`, then ask me for **"walkthrough AWS-3"**.


- [ ] **Step 1: Write `infra/bootstrap/main.tf`** with:
  - **AWS provider:** `eu-central-1`, `default_tags = { project = "bread-order-app" }`.
  - **S3 bucket `bread-tfstate-<ACCOUNT_ID>`:**
    - versioning enabled;
    - SSE-S3 encryption;
    - all four public access blocks set to `true`;
    - a bucket policy that denies `aws:SecureTransport = false`.
  - **DynamoDB table `bread-tf-locks`:** `billing_mode = "PAY_PER_REQUEST"`, `hash_key = "LockID"` (type `S`).

- [ ] **Step 2: Apply it**
  Run: `cd infra/bootstrap && terraform init && terraform apply`, and type `yes`.
  Expected: 3–4 resources are created. Keep `terraform.tfstate` in this folder (it's gitignored) and back it up somewhere private.

- [ ] **Step 3: Commit**
  Commit `infra/bootstrap/*.tf` and `.terraform.lock.hcl` in VS Code with the message `chore(infra): terraform state bootstrap`.

### AWS-4: Terraform module for one environment

**Learn first**

- **Concepts:**
  - Terraform modules and variables.
  - Cognito, S3, ECR, Lambda, API Gateway, CloudFront with OAC.
  - Least-privilege IAM; GitHub OIDC.
- **Why it's built this way:** One module, two environments: demo and prod are identical apart from their variables.
- **Read:** [CloudFront origin access control](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html) · [GitHub OIDC with AWS](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- **Check yourself** (answer these in your learning note):
  1. Why can't anyone read the web bucket directly?
  2. What stops a fork of your repo from deploying to your AWS account?
- **After the task:** write `docs/learning/AWS-4.md`, then ask me for **"walkthrough AWS-4"**.


Create `infra/modules/app/` (`variables.tf`, `main.tf`, `outputs.tf`). Use these resources and settings. You can ask Claude to draft the HCL from this list, but apply it yourself.

- [ ] **Step 1: Variables**
  - `env` (`"demo"` | `"prod"`)
  - `account_id`
  - `image_tag`
  - `mfa_required` (bool)
  - `business_name`
  - `business_address`
  - `alarm_email`
  - `github_repo` (`"<your-github-user>/bread-order-app"`)

- [ ] **Step 2: Cognito**
  - **`aws_cognito_user_pool` `bread-${env}`:**
    - Usernames: `username_attributes = ["email"]`, `auto_verified_attributes = ["email"]`.
    - Sign-up: `admin_create_user_config { allow_admin_create_user_only = true }`, so there is no self sign-up.
    - Password policy: minimum length 12; require upper, lower, numbers and symbols; `temporary_password_validity_days = 3`.
    - MFA: `mfa_configuration = var.mfa_required ? "ON" : "OFF"`, `software_token_mfa_configuration { enabled = true }`.
    - Account recovery: `account_recovery_setting` = verified email.
    - `deletion_protection = var.env == "prod" ? "ACTIVE" : "INACTIVE"`.
  - **`aws_cognito_user_pool_client` `bread-web`:**
    - `generate_secret = false`.
    - `explicit_auth_flows = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]`.
    - `prevent_user_existence_errors = "ENABLED"`.
    - Token lifetimes: `access_token_validity = 1`, `id_token_validity = 1` (hours), `refresh_token_validity = 7` (days).
    - `enable_token_revocation = true`.

- [ ] **Step 3: Storage and the container registry**
  - **S3 bucket `bread-bills-${env}-${account_id}`:**
    - public access blocked;
    - SSE-S3 encryption;
    - `BucketOwnerEnforced` ownership;
    - a TLS-only bucket policy.
  - **S3 bucket `bread-web-${env}-${account_id}`:** same settings as the bills bucket. Its policy allows `s3:GetObject` only to `cloudfront.amazonaws.com`, with condition `AWS:SourceArn` = this distribution's ARN.
  - **`aws_ecr_repository` `bread-api-${env}`:**
    - `image_scanning_configuration { scan_on_push = true }`;
    - `image_tag_mutability = "IMMUTABLE"`;
    - a lifecycle policy that keeps the last 10 images.

- [ ] **Step 4: Lambda**
  - **IAM role `bread-api-${env}`:**
    - Trust: `lambda.amazonaws.com`.
    - Attach `AWSLambdaBasicExecutionRole`.
    - Inline policy allowing:
      - `ssm:GetParameter` on `arn:aws:ssm:eu-central-1:${account_id}:parameter/bread/${env}/*`;
      - `s3:PutObject` and `s3:GetObject` on `bread-bills-${env}-${account_id}/statements/*`.

    The default `aws/ssm` KMS key needs no extra permission.
  - **`aws_cloudwatch_log_group` `/aws/lambda/bread-api-${env}`** with 30-day retention.
  - **`aws_lambda_function` `bread-api-${env}`:**
    - Package: `package_type = "Image"`, `image_uri = "${ecr_url}:${var.image_tag}"`, `architectures = ["x86_64"]`.
    - Resources: `memory_size = 1024`, `timeout = 30`, `reserved_concurrent_executions = 5`.
    - Environment variables:
      - `ENVIRONMENT`, `SSM_DATABASE_URL=/bread/${env}/database_url`
      - `CORS_ORIGINS=["https://${cloudfront_domain}"]`
      - `COGNITO_ISSUER=https://cognito-idp.eu-central-1.amazonaws.com/${pool_id}`, `COGNITO_CLIENT_ID`
      - `BILLS_BUCKET`, `BUSINESS_NAME`, `BUSINESS_ADDRESS`, `LOG_LEVEL=INFO`
  - **Demo only** (`count = var.env == "demo" ? 1 : 0`):
    - A second function `bread-demo-reset`: same image, `image_config { command = ["app.seed_demo.reset_handler"] }`, timeout 120.
    - An `aws_scheduler_schedule` with `schedule_expression = "cron(0 3 * * ? *)"`, `schedule_expression_timezone = "Europe/Berlin"`, targeting the reset function through a role allowed `lambda:InvokeFunction` on it.

- [ ] **Step 5: API Gateway**
  - **`aws_apigatewayv2_api`** with protocol `HTTP`.
  - **Integration:** `AWS_PROXY` to the Lambda, `payload_format_version = "2.0"`.
  - **Route:** `ANY /api/{proxy+}`.
  - **`$default` stage:** `auto_deploy = true`, with `default_route_settings { throttling_burst_limit = 20, throttling_rate_limit = 10 }`.
  - **`aws_lambda_permission`** for `apigateway.amazonaws.com`.

- [ ] **Step 6: CloudFront**
  - **Origin access:** an `aws_cloudfront_origin_access_control` for S3, with `signing_behavior = "always"` and `signing_protocol = "sigv4"`.
  - **`aws_cloudfront_function` `spa-rewrite`** (runtime `cloudfront-js-2.0`). It rewrites any URI with no `.` in its last segment to `/index.html`. Do **not** use custom error responses, because they would turn API 404s into HTML.
  - **`aws_cloudfront_response_headers_policy` `bread-security`:**
    - HSTS: 63072000 seconds, include subdomains, preload, override.
    - `content_type_options` (nosniff).
    - `frame_options` DENY.
    - Referrer policy: `strict-origin-when-cross-origin`.
    - CSP: `default-src 'self'; connect-src 'self' https://cognito-idp.eu-central-1.amazonaws.com; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'`.
  - **`aws_cloudfront_distribution`:**
    - General: `price_class = "PriceClass_100"`, `default_root_object = "index.html"`, `http_version = "http2and3"`, the default certificate.
    - **Default behavior** → S3 web bucket:
      - `viewer_protocol_policy = "redirect-to-https"`;
      - cache policy `Managed-CachingOptimized`;
      - the security headers policy;
      - the `spa-rewrite` function on `viewer-request`.
    - **Ordered behavior `/api/*`** → API Gateway origin (the domain from `api_endpoint` without `https://`, HTTPS only):
      - all methods allowed;
      - cache policy `Managed-CachingDisabled`;
      - origin request policy `Managed-AllViewerExceptHostHeader`;
      - the security headers policy;
      - `redirect-to-https`.

- [ ] **Step 7: Monitoring**
  - **`aws_sns_topic` `bread-alarms-${env}`** with an email subscription to `alarm_email`.
  - **`aws_cloudwatch_metric_alarm`** on Lambda `Errors`:
    - Sum ≥ 1 over 300 seconds, 1 evaluation period;
    - `treat_missing_data = "notBreaching"`;
    - actions to the SNS topic.
  - **A second alarm** on API Gateway `5xx` with the same settings.

- [ ] **Step 8: GitHub access (OIDC)**
  Create these once, in the demo environment only (`count`), and reference them from prod with `data` sources.
  - **`aws_iam_openid_connect_provider`:**
    - URL `https://token.actions.githubusercontent.com`
    - client ID `sts.amazonaws.com`
  - **Role `bread-github-deploy`.** Its trust policy allows `sts:AssumeRoleWithWebIdentity` with these conditions:
```hcl
condition { test = "StringEquals" variable = "token.actions.githubusercontent.com:aud" values = ["sts.amazonaws.com"] }
condition { test = "StringLike"   variable = "token.actions.githubusercontent.com:sub"
            values = ["repo:${var.github_repo}:ref:refs/heads/main", "repo:${var.github_repo}:environment:prod"] }
```
    Its permissions, limited to the `bread-*` resources:
    - `ecr:GetAuthorizationToken` (on `*`);
    - ECR push actions on `bread-api-*`;
    - `lambda:UpdateFunctionCode`, `lambda:GetFunction` on `bread-api-*` and `bread-demo-reset`;
    - `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket` on `bread-web-*`;
    - `cloudfront:CreateInvalidation`;
    - `ssm:GetParameter` on `/bread/*/database_url`.
  - **Role `bread-github-plan`.** Trust `sub` = `repo:${var.github_repo}:pull_request`. Attach `ReadOnlyAccess`, plus read/write on the state bucket and lock table.

- [ ] **Step 9: Outputs**
  - `cloudfront_domain`, `distribution_id`
  - `api_endpoint`
  - `user_pool_id`, `user_pool_client_id`
  - `ecr_url`
  - `web_bucket`

- [ ] **Step 10: Environment folders**
  Create `infra/envs/demo/` and `infra/envs/prod/`. Each contains:
  - A `backend "s3"` block with:
    - bucket `bread-tfstate-<ACCOUNT_ID>`
    - key `demo/terraform.tfstate` (or `prod/…`)
    - region `eu-central-1`
    - `dynamodb_table = "bread-tf-locks"`
    - `encrypt = true`
  - `module "app" { source = "../../modules/app" … }`.
  - `example.tfvars`, which is committed and contains no secrets.
  - Your real `terraform.tfvars`, which is gitignored:
    - demo: `mfa_required = false`;
    - prod: `mfa_required = true`.

- [ ] **Step 11: Format and validate**
  Run: `terraform fmt -recursive infra && cd infra/envs/demo && terraform init && terraform validate`
  Expected: "Success! The configuration is valid."

### AWS-5: Deploy the demo environment the first time

**Learn first**

- **Concepts:**
  - Container registries; deploying an image to Lambda.
  - Cache headers and CloudFront invalidation.
- **Why it's built this way:** Doing the first deploy by hand shows you what CI will automate.
- **Read:** [CloudFront invalidation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html)
- **Check yourself** (answer these in your learning note):
  1. Why are `index.html` and `config.json` never cached, but the JS files are cached for a year?
- **After the task:** write `docs/learning/AWS-5.md`, then ask me for **"walkthrough AWS-5"**.


- [ ] **Step 1: Create the container registry first**
  Run: `cd infra/envs/demo && terraform apply -target=module.app.aws_ecr_repository.api`
  The Lambda needs an image before it can be created.

- [ ] **Step 2: Build and push the first image**
```bash
ECR=<ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com
aws ecr get-login-password $AWS | docker login --username AWS --password-stdin $ECR
docker build --platform linux/amd64 -t $ECR/bread-api-demo:v0.0.1 backend
docker push $ECR/bread-api-demo:v0.0.1
```

- [ ] **Step 3: Apply everything**
  Run: `terraform apply -var image_tag=v0.0.1`
  Expected: the apply completes, and you receive an SNS "Subscription Confirmation" email. Click **Confirm subscription** in it.

- [ ] **Step 4: Check the API through CloudFront**
  Run: `curl -s https://<cloudfront_domain>/api/v1/health` (should print `{"status":"ok"}`) and `curl -s -o /dev/null -w "%{http_code}" https://<cloudfront_domain>/api/v1/me` (should print `401`).

- [ ] **Step 5: Build and upload the frontend**
```bash
cd frontend
npm run build
cat > dist/frontend/browser/config.json <<JSON
{ "apiBaseUrl": "/api/v1", "authMode": "cognito", "cognitoUserPoolId": "<pool>", "cognitoClientId": "<client>", "demo": true }
JSON
aws s3 sync dist/frontend/browser s3://<web_bucket> --delete $AWS --cache-control "public,max-age=31536000,immutable" --exclude index.html --exclude config.json
aws s3 cp dist/frontend/browser/index.html s3://<web_bucket>/index.html $AWS --cache-control "no-cache"
aws s3 cp dist/frontend/browser/config.json s3://<web_bucket>/config.json $AWS --cache-control "no-cache"
aws cloudfront create-invalidation $AWS --distribution-id <id> --paths "/index.html" "/config.json"
```

- [ ] **Step 6: Create the demo login**
```bash
aws cognito-idp admin-create-user $AWS --user-pool-id <pool> --username demo@bread-demo.example \
  --user-attributes Name=email,Value=demo@bread-demo.example Name=email_verified,Value=true --message-action SUPPRESS
aws cognito-idp admin-set-user-password $AWS --user-pool-id <pool> --username demo@bread-demo.example \
  --password '<demo password, ≥12 chars>' --permanent
```

- [ ] **Step 7: Check it in a browser**
  Open `https://<cloudfront_domain>` on your laptop **and your phone**:
  - the demo banner shows;
  - you can sign in with the demo user;
  - the seeded data appears;
  - downloading a PDF works.

  Then check the security headers at securityheaders.com; you should get grade A.

### AWS-6: CI/CD workflows (GitHub Actions)

**Learn first**

- **Concepts:**
  - CI/CD workflows, GitHub environments and approvals.
  - Masking secrets in logs.
- **Why it's built this way:** Every merge deploys the demo and runs e2e tests; prod needs your approval.
- **Read:** [Using environments for deployment](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment)
- **Check yourself** (answer these in your learning note):
  1. What's the difference between a repository variable and an environment secret?
- **After the task:** write `docs/learning/AWS-6.md`, then ask me for **"walkthrough AWS-6"**.


- [ ] **Step 1: Set up GitHub environments, variables and secrets**
  1. In GitHub → Settings → Environments, create:
     - `demo` (no rules);
     - `prod` with **Required reviewers: you** and deployment tags `v*`.
  2. In Settings → Secrets and variables → Actions → **Variables**, add `AWS_ACCOUNT_ID` and `AWS_REGION=eu-central-1`.
  3. As **environment variables** on each environment, add: `USER_POOL_ID`, `USER_POOL_CLIENT_ID`, `WEB_BUCKET`, `DISTRIBUTION_ID`, `CLOUDFRONT_DOMAIN`.
  4. As **demo environment secrets**, add `E2E_EMAIL` and `E2E_PASSWORD` (the demo user).

  No AWS keys are stored anywhere, because the workflows use OIDC.

- [ ] **Step 2: Write `.github/workflows/deploy-demo.yml`**
  - **Trigger:** `on: push: branches: [main]`.
  - **`permissions`:** `id-token: write`, `contents: read`.
  - **Job `deploy`** (`environment: demo`). Steps:
    1. `aws-actions/configure-aws-credentials@v4` with `role-to-assume: arn:aws:iam::${{ vars.AWS_ACCOUNT_ID }}:role/bread-github-deploy`.
    2. ECR login (`aws-actions/amazon-ecr-login@v2`).
    3. Build and push `bread-api-demo:${{ github.sha }}`.
    4. Run migrations:
       - read the URL with `aws ssm get-parameter --with-decryption`;
       - mask it immediately with `echo "::add-mask::$URL"`;
       - `uv run alembic upgrade head`.
    5. `aws lambda update-function-code` for `bread-api-demo` and `bread-demo-reset` with `--image-uri`, then `aws lambda wait function-updated`.
    6. Build the frontend once, write `config.json` from the environment variables above with `"demo": true`, then run the `s3` uploads and the invalidation from AWS-5 Step 5.
  - **Job `e2e`** (needs `deploy`):
    - `npx playwright install --with-deps chromium`;
    - `npm run e2e` with `E2E_BASE_URL=https://${{ vars.CLOUDFRONT_DOMAIN }}` and the secrets;
    - upload `playwright-report` as an artifact on failure.

- [ ] **Step 3: Write `.github/workflows/deploy-prod.yml`**
  - **Trigger:** `on: push: tags: ["v*"]`.
  - **Job:** same as the demo deploy, but `environment: prod` (this pauses for your approval), the image tag is `${{ github.ref_name }}`, there is no reset function, `config.json` has `"demo": false`, and there are no e2e tests (prod holds real data).

- [ ] **Step 4: Add a Terraform plan job**
  Add a job `terraform-plan` to `backend.yml`, or create a new `infra.yml`:
  - **Trigger:** pull requests touching `infra/**`.
  - **Steps:** assume `bread-github-plan`, then run `terraform init` and `terraform plan -lock=false` in `infra/envs/demo` and `infra/envs/prod`.
  - Mark it `continue-on-error: false`.

  Applying Terraform stays manual, from your laptop.

- [ ] **Step 5: Check it end to end**
  Merge a small pull request to `main`. In the Actions tab, `deploy-demo` should be green and `e2e` should pass on both desktop and phone.

### AWS-7: Production environment

**Learn first**

- **Concepts:**
  - Releases with tags; manual approval gates.
- **Why it's built this way:** Real customer data only changes when you decide to release.
- **Read:** [Git tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging)
- **Check yourself** (answer these in your learning note):
  1. How would you roll back a bad release?
- **After the task:** write `docs/learning/AWS-7.md`, then ask me for **"walkthrough AWS-7"**.


- [ ] **Step 1: Create the prod environment**
  Repeat AWS-5 Steps 1–3 in `infra/envs/prod`, with `mfa_required = true`.

- [ ] **Step 2: Create the two admin users** (you and the second super user)
```bash
aws cognito-idp admin-create-user $AWS --user-pool-id <prod pool> --username <email> \
  --user-attributes Name=email,Value=<email> Name=email_verified,Value=true --desired-delivery-mediums EMAIL
```
  Each person receives a temporary password by email. At first sign-in the app asks them to set a new password and scan the MFA QR code (FE-3).

- [ ] **Step 3: Release**
  1. In VS Code, create a tag: Command Palette → **Git: Create Tag** → `v0.1.0`, then **Git: Push Tags**.
  2. On GitHub → Actions, approve the `deploy-prod` run.

- [ ] **Step 4: Check prod**
  - Sign in on your phone, complete MFA and create one real customer.
  - Open `https://<prod domain>/api/v1/me` without a token; it should return 401.
  - **Do not share the prod URL publicly**; only the demo goes in the README.

### AWS-8: Monitoring and cost check

**Learn first**

- **Concepts:**
  - Metrics, alarms and structured logs.
- **Why it's built this way:** You hear about errors from an email, not from a customer.
- **Read:** [CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- **Check yourself** (answer these in your learning note):
  1. How would you find the log entry for a user's error reference?
- **After the task:** write `docs/learning/AWS-8.md`, then ask me for **"walkthrough AWS-8"**.


- [ ] **Step 1: Test the alarm**
  1. In the Lambda console, temporarily set `SSM_DATABASE_URL` on `bread-api-demo` to `/bread/demo/missing`.
  2. Open the demo app; startup fails, so requests error.
  3. Check that the alarm email arrives within about 10 minutes.
  4. Set the variable back.

  If you'd rather not break things, use **Set alarm state** in the CloudWatch console instead.

- [ ] **Step 2: Check the logs**
  In CloudWatch Logs → `/aws/lambda/bread-api-demo`, check that each entry is JSON with a `request_id`, and that no connection strings or tokens appear.

- [ ] **Step 3: Check the costs**
  After one week, look at Billing → Bills (current month). Expected: €0–1.

  ECR storage and CloudFront fall within the free tier at this size. If anything is over €1, check ECR images (the lifecycle policy) and CloudWatch log volume.

### AWS-9: Finish the README for recruiters

**Learn first**

- **Concepts:**
  - Writing for reviewers: README, badges, architecture.
- **Why it's built this way:** Recruiters spend about a minute on a repo; the README decides what they see.
- **Read:** [About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
- **Check yourself** (answer these in your learning note):
  1. What would you say about this project in two minutes?
- **After the task:** write `docs/learning/AWS-9.md`, then ask me for **"walkthrough AWS-9"**.


- [ ] **Step 1: Badges**
  Replace the placeholders with real badges for the `backend`, `frontend` and `deploy-demo` workflows, plus coverage (e.g. upload `coverage.xml` to Codecov, which is free for public repos).

- [ ] **Step 2: Live demo**
  Add a **Live demo** section with the demo URL and the demo login (email and password), noting that it resets nightly.

- [ ] **Step 3: Architecture and decisions**
  - Add an **Architecture** diagram (`specs/diagrams/02-aws-deployment.png` from the architecture file).
  - Add a short **Security** list (MFA, OIDC with no keys, least-privilege IAM, CSP/HSTS, EU data residency).
  - Add a **Key decisions** section: why serverless, why Neon, why price snapshots, and why the billing-period lock.

- [ ] **Step 4: Commit through a pull request**
  Message: `docs: live demo, badges and architecture`.

### AWS-10: Ongoing habits that keep the GitHub profile active

**Learn first**

- **Concepts:**
  - Issues, project boards and steady small PRs.
- **Why it's built this way:** Visible, regular progress is itself a signal to employers.
- **Read:** [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
- **Check yourself** (answer these in your learning note):
  1. How do you break a feature into issues?
- **After the task:** write `docs/learning/AWS-10.md`, then ask me for **"walkthrough AWS-10"**.


- [ ] **Step 1: Work in small pull requests**
  Use one PR per task in this plan, each referencing its task ID (e.g. "BE-7 orders API"). Small daily commits show steady activity.

- [ ] **Step 2: Track the work in GitHub**
  1. Open GitHub Issues for the remaining tasks and add them to a GitHub Project board with columns Todo, In progress and Done.
  2. Pin the repo on your GitHub profile.

- [ ] **Step 3: Merge Dependabot pull requests weekly**, after CI passes.
