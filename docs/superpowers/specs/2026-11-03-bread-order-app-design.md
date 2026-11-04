# Bread Order App — Design Spec

**Date:** 2026-11-03
**Status:** Draft, awaiting review

## 1. Purpose

Two goals:

1. **Run the home bread business:** customer records, orders, daily rates, monthly bills and payment tracking.
2. **Portfolio:** demonstrate full-stack skills (React + TypeScript, Python) for the European job market through a public GitHub repo and a live demo.

## 2. Scope

### In scope
- Customer records (create, edit, deactivate, anonymise)
- Order entry and status workflow
- Product rates with effective dates
- Payments and monthly balances with carry-forward
- Monthly PDF bill per customer (Kleinunternehmer, no VAT)
- Two environments: private `prod` and public `demo`

### Out of scope
- Customer logins or a customer-facing ordering page
- WhatsApp integration (WhatsApp orders are entered manually)
- Online payments
- VAT handling
- Email or SMS sending
- Mobile app

## 3. Users

| User | Access |
|---|---|
| Admin (exactly 2 accounts) | Full access to all features |
| Customer | No login; exists only as a record |
| Demo visitor (demo environment only) | Shared demo admin login with fake data |

## 4. Products and initial rates

| Product | Initial price per piece |
|---|---|
| Mini pav | €0.40 |
| Medium pav | €0.55 |
| Normal pav | €0.60 |
| Brownie | €1.00 |
| Roti | €1.00 |

Admins can change prices at any time through the rates feature (§6.3).

## 5. Architecture

```
Browser (React + TS)
   │  HTTPS
CloudFront ──► S3 (static frontend)
   │ /api/*
API Gateway (HTTP API) ──► Lambda (FastAPI via Mangum)
                              ├──► Neon Postgres (eu-central-1)
                              └──► S3 private bucket (PDF bills)
Cognito user pool ── issues JWTs; the API verifies them on every request
EventBridge schedule ──► Lambda (nightly demo data reset, demo only)
```

### Region and cost
- All AWS resources run in `eu-central-1` (Frankfurt); Neon runs in its Frankfurt region.
- Target cost: close to €0 per month (AWS free tier plus Neon free tier).

### Environments
- `prod` and `demo` are deployed from the same code.
- Each has its own Neon database, Cognito pool, S3 buckets and Lambda.
- Demo can never reach prod data.

### Repo layout
One public monorepo:

```
frontend/            React + TypeScript (Vite)
backend/
  app/api/           FastAPI routers
  app/services/      business rules (pure Python)
  app/repositories/  database access (SQLAlchemy)
  app/models/        ORM models
  app/schemas/       Pydantic request/response models
  app/pdf/           bill rendering
  migrations/        Alembic
  tests/
infra/               Terraform (modules + envs/prod, envs/demo)
.github/workflows/   CI/CD
docs/
```

### Stack
- **Frontend:** React, TypeScript (strict), Vite, React Router, TanStack Query, React Hook Form with Zod, shadcn/ui. API types are generated from FastAPI's OpenAPI schema.
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, Mangum (to run on Lambda).
- **PDF:** WeasyPrint, using HTML templates rendered with Jinja2.
- **Infrastructure:** Terraform, with state in S3 and a DynamoDB lock table.

## 6. Data model

### General rules
- Money is stored as integer cents.
- Dates are stored as calendar dates, interpreted in the Europe/Berlin timezone.
- Every table has `id`, `created_at`, `created_by`, `updated_at` and `updated_by`.

### 6.1 `customers`
- Fields: `name`, `phone`, `address`, `notes`, `is_active`, `anonymised_at`.
- Customers are never hard-deleted.

### 6.2 `products`
- Fields: `code` (unique), `name`, `is_active`.

### 6.3 `product_rates`
- Fields: `product_id`, `price_cents`, `effective_from` (date).
- The pair (`product_id`, `effective_from`) is unique.
- The rate for date D is the row with the latest `effective_from` that is on or before D.
- If no such row exists, the order is rejected with the error `NO_RATE_FOR_DATE`.

### 6.4 `orders`
- Fields: `customer_id`, `delivery_date`, `source` (`whatsapp` / `phone` / `other`), `status`, `notes`.

### 6.5 `order_items`
- Fields: `order_id`, `product_id`, `quantity` (a positive integer), `unit_price_cents`.
- `unit_price_cents` is copied from the rate for the delivery date when the item is saved, and is never recalculated afterwards.

### 6.6 `payments`
- Fields: `customer_id`, `amount_cents` (positive), `paid_on`, `method` (`cash` / `bank_transfer` / `other`), `note`.

### 6.7 `adjustments`
- Fields: `customer_id`, `amount_cents` (signed), `applies_to_month`, `reason`.
- Used to correct issued bills.

### 6.8 `monthly_statements`
- Fields: `customer_id`, `month` (first day of the month), `opening_cents`, `orders_cents`, `payments_cents`, `adjustments_cents`, `closing_cents`, `status` (`draft` / `issued`), `pdf_s3_key`, `issued_at`.
- The pair (`customer_id`, `month`) is unique.

## 7. Business rules

### 7.1 Order status
- Allowed transitions:
  - `pending → confirmed → in_prep → delivered`
  - `pending`, `confirmed` or `in_prep` → `cancelled`
- Every other transition is rejected with `INVALID_STATUS_TRANSITION`.
- Items can only be edited while the order is `pending` or `confirmed`.
- A `delivered` order cannot be edited or cancelled. Corrections are made through `adjustments`.

### 7.2 Billing
- Only `delivered` orders are billed.
- The billing month is the month of `delivery_date`.

### 7.3 Monthly statement for customer C and month M
- `opening` = `closing` of C's statement for month M−1, or 0 if C has no earlier statement.
- `orders` = sum of quantity × unit price for C's delivered orders delivered in M.
- `payments` = sum of C's payments with `paid_on` in M.
- `adjustments` = sum of C's adjustments for M.
- `closing` = opening + orders − payments + adjustments.
- A positive closing balance is money owed; a negative one is credit. Either carries forward to the next month.

### 7.4 Issuing statements
- Generating month M creates a draft for every customer who has delivered orders, payments or adjustments in M, or a non-zero opening balance. Customers with none of these get no statement.
- A draft can be regenerated any number of times.
- Issuing locks the statement.
- After a statement for month M is issued, delivered orders dated in M, payments dated in M and adjustments for M can no longer be created, changed or removed. Each such attempt is rejected with `PERIOD_LOCKED`.
- Months are billed in sequence. Month M can be generated only if no statements exist yet (the first billing month) or every statement for M−1 is issued. Otherwise generation is rejected with `PREVIOUS_MONTH_NOT_ISSUED`. This stops a skipped month from losing its orders and payments.
- Regenerating M replaces its drafts and leaves its issued statements untouched.
- A statement can be issued only after its month has ended (Europe/Berlin time). Otherwise it is rejected with `MONTH_NOT_ENDED`.
- The PDF is created when the statement is issued.

### 7.5 PDF bill contents
- Business name and address
- Customer name and address
- Invoice number in the format `YYYY-MM-<customer id>`
- Issue date and billing period
- One line per delivered order: date, items, quantities, unit prices and line totals
- Opening balance, orders total, payments, adjustments and closing balance
- The note: "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."

### 7.6 Anonymisation
- Replaces the customer's name, phone, address and notes with placeholders.
- Keeps the customer's orders and statements for invoice retention.

## 8. API

- All routes are under `/api/v1` and require a Cognito JWT, except `GET /api/v1/health`.
- Routes follow standard REST patterns for customers, products, rates, orders (plus `POST /orders/{id}/status`), payments, adjustments and statements (`POST /statements/generate`, `POST /statements/{id}/issue`, `GET /statements/{id}/pdf`).
- `GET /statements/{id}/pdf` returns a presigned S3 URL that expires after 5 minutes.
- Error format: `{"error": {"code": "...", "message": "...", "field": "..."}}`
- Each response includes an `X-Request-ID` header, which is also logged.

## 9. Frontend screens

1. **Login:** email, password and MFA code.
2. **Dashboard:** today's orders by status, today's baking totals per product, and the total amount outstanding.
3. **Customers:**
   - List with search
   - Create and edit form
   - Detail page with order history and current balance
4. **Orders:**
   - New-order form with a live total calculated from the rate for the delivery date
   - List filtered by date and status
   - One-click change to the next status
5. **Rates:** current price per product, set a new price from a date, and price history.
6. **Payments:** record a payment, and view a customer's monthly balances.
7. **Bills:** choose a month, generate drafts, issue statements, and download PDFs.

### Mobile-friendly
- Designed mobile-first; every screen works from 360px wide (phones) up to desktop, with no horizontal scrolling.
- Navigation: a bottom tab bar on phones (Dashboard, Orders, Customers, More) and a sidebar on screens 1024px and wider.
- Tables become stacked cards below 768px.
- Touch targets are at least 44×44px; number inputs open the numeric keypad.
- New-order form fits one phone screen: customer, delivery date, and a +/− quantity stepper per product, with the total pinned at the bottom.
- PDF bills open in the phone's own viewer.

### Session handling
- When the session expires, the user is redirected to the login page.
- A friendly error toast shows the request ID.

## 10. Security

### Login
- Cognito with self sign-up disabled; only the 2 admins are created, by Terraform or the console.
- MFA is required, using an authenticator app.
- Password policy: at least 12 characters with mixed character types.
- Access tokens last 1 hour.

### API
- JWTs are verified (signature, issuer, audience and expiry) on every request.
- All input is validated by Pydantic.
- The database is accessed only through the ORM or parameterised queries.
- Rate limiting is configured on API Gateway.
- CORS allows only the frontend's own origin.

### Data
- TLS everywhere.
- Neon encrypts data at rest and requires TLS connections.
- The S3 bills bucket is private, with all public access blocked and encryption on.
- Secrets are stored in SSM Parameter Store (SecureString), never in the repo.
- Each Lambda has an IAM role with only the permissions it needs.

### Browser
- CloudFront sets security response headers: CSP, HSTS, X-Content-Type-Options, X-Frame-Options and Referrer-Policy.

### Supply chain
- Dependabot keeps dependencies updated.
- CI runs `pip-audit`, `npm audit`, gitleaks and bandit.
- Branch protection on `main` requires CI to pass.
- GitHub Actions connects to AWS through OIDC, so no long-lived AWS keys exist.

### GDPR
- All data is stored in the EU.
- The demo contains only fake data.
- Customers can be anonymised (§7.6).

## 11. Demo environment

- The demo admin login is published in the README. MFA is off for the demo pool only.
- The demo database is reset nightly to seed data.
- The demo shows a banner: "Demo — data resets nightly".

## 12. Testing

| Layer | Tool | Covers |
|---|---|---|
| Unit | pytest | Rate lookup, status transitions, statement calculation, period lock |
| API / integration | pytest, FastAPI TestClient, Testcontainers Postgres | Endpoints, login checks, validation errors, migrations |
| PDF | pytest | Totals and the §19 note in the rendered output |
| Frontend | Vitest, React Testing Library, MSW | Forms, validation, order-total display |
| End-to-end | Playwright (against demo) | Login → customer → order → delivered → payment → issue bill → download PDF, run on a desktop viewport and on a phone viewport (Pixel 7) |

- Business-logic coverage target: 85% or more.
- Business rules are developed test-first.

## 13. Code quality

- **Python:** ruff (linting and formatting) and mypy (strict).
- **Frontend:** ESLint, Prettier and strict TypeScript.
- **Local:** pre-commit hooks run the same checks.

## 14. CI/CD (GitHub Actions)

### On every pull request
- Lint and type checks
- Backend and frontend tests
- Security scans (§10)
- `terraform plan`

### On merge to `main`
- Build and deploy to `demo`
- Run Alembic migrations
- Run the Playwright tests against `demo`

### On a `v*` release tag
- Deploy to `prod`, after manual approval in a protected GitHub environment
- Run Alembic migrations

### README
- Badges: build status, coverage and live demo link
- Architecture diagram
- Local setup instructions (Docker Compose with Postgres)

## 15. Observability

- Structured JSON logs in CloudWatch, each including the request ID.
- A CloudWatch alarm fires on the Lambda error rate.
- An AWS Budgets alert fires at €5 per month.
