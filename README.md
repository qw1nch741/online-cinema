# Online Cinema API - Phase 1 (Core Infrastructure & Auth)

Asynchronous backend for an Online Cinema platform built with FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery, Redis, and Poetry.

**Currently under review for Phase 1.** This phase focuses entirely on establishing a production-grade infrastructure, a bulletproof CI/CD pipeline, and a highly secure Authentication & Authorization domain. 

---

## Phase 1 Deliverables

This submission fulfills the following core requirements from the project specification:

| # | Task | Status | Focus Area |
|---|------|--------|------------|
| 1 | **Authorization and Authentication** | ✅ Implemented | JWTs, Password Reset Flows, Email Activation |
| 6 | **Docker and Docker Compose** | ✅ Implemented | Multi-container dev environment |
| 7 | **Poetry for Dependency Management** | ✅ Implemented | Reproducible builds via `pyproject.toml` |
| 8 | **CI/CD with GitHub Actions** | ✅ Implemented | Automated linters, static analysis, and testing |
| 9 | **Swagger Documentation** | ✅ Implemented | Interactive OpenAPI 3.x schema |
| 10| **Writing Tests** | 🚧 In Progress | Pytest coverage for Auth domain |

> **Note on Phase 2 (Business Domain):** Basic boilerplate models and routers for Movies, Cart, and Orders have been scaffolded to provide context for the auth flows, but the complete relational logic (Many-to-Many associations, Payments) is reserved for Phase 2.

---

## API Documentation (Swagger / OpenAPI)

The project uses **OpenAPI 3.x** via FastAPI. All custom endpoints are rigorously documented.

### Accessing documentation

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/docs` | Swagger UI (interactive) |
| `http://127.0.0.1:8000/redoc` | ReDoc (read-only) |
| `http://127.0.0.1:8000/openapi.json` | Raw OpenAPI 3.x schema |

### Restricting documentation access

Set in `.env`:
```env
OPENAPI_DOCS_ENABLED=false
```
When disabled, `/docs`, `/redoc`, and `/openapi.json` return a generic message instead of the schema. Use this in production to restrict public access to API documentation.

### Using Bearer auth in Swagger UI
1. Call `POST /auth/login` with email and password.
2. Copy the `access_token` from the response.
3. Click **Authorize** in Swagger UI.
4. Enter: `Bearer <access_token>`

---

## Phase 1 Endpoint Reference (Auth Domain)

The Auth domain is fully realized with secure hashing, token rotation, and password management.

| Method | Path | Auth | Action |
|--------|------|------|--------|
| POST | `/auth/register` | No | Register with email; creates inactive user and 24h activation token |
| GET | `/auth/activate?token=` | No | Activate account using email token |
| POST | `/auth/activate/resend` | No | Resend activation token for inactive account |
| POST | `/auth/login` | No | Login; returns access + refresh JWT pair |
| POST | `/auth/refresh` | No | Exchange refresh token for new access + refresh tokens |
| POST | `/auth/logout?refresh_token=` | Yes | Revoke refresh token |
| POST | `/auth/change-password` | Yes | Change password (requires old password) |
| POST | `/auth/forgot-password` | No | Generates and issues a secure password reset token |
| POST | `/auth/reset-password` | No | Validates reset token and sets new password |

---

## Tech Stack

- **Framework:** FastAPI (async ASGI)
- **ORM:** SQLAlchemy 2.0 + asyncpg
- **Database:** PostgreSQL
- **Task queue:** Celery + Celery Beat
- **Broker:** Redis
- **Dependencies:** Poetry
- **Containers:** Docker + Docker Compose

---

## Local Setup

### Prerequisites
- Python 3.10+
- Poetry
- Docker & Docker Compose

### Run via Docker (Recommended)
```bash
cp .env.sample .env   # edit values as needed
docker compose -f docker-compose-dev.yml up --build
```
API: `http://127.0.0.1:8000`  
Swagger: `http://127.0.0.1:8000/docs`

---

## Test Coverage (Task 10)

Tests use **pytest** with **pytest-cov** for coverage reporting. 

```bash
poetry run pytest --cov=src --cov-report=html
```
*Open `htmlcov/index.html` in your browser for a line-by-line coverage breakdown.*

---
## CI/CD Pipeline (Task 8)
GitHub Actions runs on every push/PR to `main`:
1. `flake8` — code style checks
2. `mypy` — static type checking
3. `alembic upgrade head` — migration validation
4. `pytest --cov` — automated test execution
