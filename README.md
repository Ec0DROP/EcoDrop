# EcoDrop

EcoDrop is a Tech for Good API that reduces food waste. It connects local supermarkets and restaurants with food banks so that surplus food can be donated before it expires.

**Stack:** Python 3.11+ · FastAPI · PostgreSQL · Docker · Postman · GitHub Actions · Render

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Design Patterns & Guidelines](#2-design-patterns--guidelines)
3. [Development Workflow](#3-development-workflow)
4. [Setup & Run Instructions](#4-setup--run-instructions)
5. [Verification Log](#5-verification-log)

---

## 1. Architecture Overview

EcoDrop uses a **Layered Architecture**. Each layer depends only on the layer directly below it.

![EcoDrop architecture](docs/architecture.png)

> Source model: `docs/architecture.mdj` (StarUML). Export the diagram to `docs/architecture.png` after every change.

```text
Client (Postman / food bank app / donor app)
        │  HTTP/JSON
        ▼
┌─────────────────────────────┐
│ API layer      (routers)    │  request parsing, status codes
├─────────────────────────────┤
│ Schema layer   (Pydantic)   │  validation, request/response DTOs
├─────────────────────────────┤
│ Service layer               │  business rules (expiry, claiming)
├─────────────────────────────┤
│ Repository layer            │  all SQL / ORM access
├─────────────────────────────┤
│ PostgreSQL                  │
└─────────────────────────────┘
```

### Folder structure

```text
ecodrop/
├── app/
│   ├── main.py            # FastAPI app, router registration, exception handlers
│   ├── api/               # routers: donations.py, claims.py
│   ├── schemas/           # Pydantic models (DonationCreate, DonationRead, ClaimRead)
│   ├── services/          # business logic
│   ├── repositories/      # database access
│   ├── models/            # SQLAlchemy ORM models
│   ├── core/              # config, exceptions, dependencies
│   └── db/                # engine, session factory, migrations
├── tests/
├── docs/                  # architecture.mdj, architecture.png
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

### Data flow

**`POST /donations`** — register a surplus-food donation

1. The router receives the JSON body and FastAPI validates it against `DonationCreate`.
2. The router calls `DonationService.create_donation(...)` (injected via `Depends`).
3. The service checks business rules (e.g. the expiry date is in the future).
4. `DonationRepository.add(...)` persists the batch in PostgreSQL.
5. The service returns the entity, which is serialised as `DonationRead` with `201 Created`.

**`GET /claims`** — view food batches claimed by food banks

1. The router calls `ClaimService.list_claims(...)`.
2. `ClaimRepository` queries claimed batches.
3. Results are returned as a list of `ClaimRead` with `200 OK`.

---

## 2. Design Patterns & Guidelines

| Pattern / principle | Where it is used | Why |
|---|---|---|
| **Layered Architecture** | whole project | Separates HTTP, business logic and persistence, so each part can be tested and changed independently. |
| **Dependency Injection** | FastAPI `Depends` for services, repositories, DB session | Removes hard-coded dependencies; tests can inject fakes or a test database. |
| **Repository** | `app/repositories/` | Hides ORM/SQL behind a small interface; services never touch the session directly. |
| **Factory** | `get_session()` / session factory in `app/db/` | One place creates DB sessions, with correct lifecycle (open → commit/rollback → close). |
| **DTO (Pydantic schemas)** | `app/schemas/` | Keeps the public API contract separate from the database model. |

### Error & validation handling conventions

- **Input validation** is done by Pydantic schemas. Invalid input returns `422 Unprocessable Entity` automatically.
- **Business errors** are custom exceptions in `app/core/exceptions.py` (e.g. `DonationExpiredError`, `BatchAlreadyClaimedError`), raised by services only.
- **Exception handlers** registered in `main.py` map exceptions to HTTP codes (`400`, `404`, `409`), all with the same JSON body: `{"error": "<code>", "detail": "<message>"}`.
- Routers contain **no business logic** and **no try/except**; they only delegate.
- Never return stack traces to clients; log them server-side.

### Clean Code principles

- Meaningful names; functions do one thing and stay short.
- No magic numbers or strings; use constants or enums.
- Type hints on all public functions; code is formatted and linted in CI (`ruff`, `black`).
- Comments explain *why*, not *what*.
- Every new endpoint comes with tests (happy path + at least one edge case).

---

## 3. Development Workflow

### Branching strategy

- `main` — always deployable; protected, changes only through Pull Requests.
- `feature/<ticket-id>-short-description` — new functionality (e.g. `feature/ECO-12-post-donations`).
- `fix/<ticket-id>-short-description` — bug fixes.
- `docs/<ticket-id>-short-description` — documentation changes.

### Commit message convention (Conventional Commits)

```text
<type>(<scope>): <short imperative summary>

feat(donations): add POST /donations endpoint
fix(claims): return 404 for unknown claim id
docs(readme): describe branching strategy
test(donations): cover expired batch case
```

Allowed types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.

### Pull Request process (step-by-step)

1. Create a branch from the latest `main`.
2. Commit small, focused changes using the convention above.
3. Push the branch and open a Pull Request into `main`; link the Jira ticket and fill in the PR template.
4. GitHub Actions runs linting and tests; the PR cannot be merged while checks fail.
5. At least **one teammate** reviews the PR (the Technical Writer checks documentation and Markdown structure). Review checklist:
   - follows the architecture and patterns from this README,
   - Clean Code principles respected,
   - tests added and passing,
   - docs updated if behaviour changed.
6. The author resolves all comments; the reviewer approves.
7. Merge using **Squash and merge**, then delete the branch.
8. Move the Jira ticket to *Done*.

### Team rhythm

- 15-minute stand-ups (Past Simple for completed tasks, Present Perfect for blockers/in-progress work).
- Internal draft review exactly 24 hours before each weekly deliverable.
- Important decisions are recorded in this documentation.

---

## 4. Setup & Run Instructions

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11 or newer |
| Docker & Docker Compose | recent stable |
| PostgreSQL | 15+ (provided by Docker Compose) |
| Git | any recent version |

### Environment variables

Copy the template and fill in the values:

```bash
cp .env.example .env
```

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://ecodrop:ecodrop@localhost:5432/ecodrop` |
| `APP_ENV` | `development` / `production` | `development` |
| `LOG_LEVEL` | logging verbosity | `INFO` |

### Run locally

```bash
# 1. Clone
git clone <repository-url>
cd ecodrop

# 2. Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Start PostgreSQL
docker compose up -d db

# 4. Apply database migrations
alembic upgrade head

# 5. Run the application
uvicorn app.main:app --reload
```

The API is available at <http://localhost:8000>, interactive docs at <http://localhost:8000/docs>.

### Run everything in Docker

```bash
docker compose up --build
```

### Test

```bash
pytest
```

### Build

```bash
docker build -t ecodrop .
```

---
