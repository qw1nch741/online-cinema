
# Online Cinema API

A production-ready, asynchronous backend architecture for an Online Cinema platform. Built using FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery, and Redis, this system implements high-performance media cataloging, secure user authentication, transactional shopping carts, and automated background data lifecycle management.

---
```markdown
## Implemented Core Features

The system architecture implements 7 core features from the project specification, organized across four operational domains:

### 1. Identity and Access Management
* Secure Registration and Token Lifecycle: Unique email constraints, secure password hashing, and asynchronous token dispatch.
* Advanced JWT Session Rotation and Logout: Dual access and refresh token pairs with active token revocation upon logout.
* Role-Based Access Control (RBAC): Generic, parameterized role-checking dependencies enforcing access control across User, Moderator, and Admin groups.

### 2. Content Management
* Movie Catalog Engine: Asynchronous relational data layers managing movies, genres, actors, directors, and age certifications.

### 3. Transactional Commerce
* Isolated Shopping Cart Manager: User-insulated item holding with complete enforcement against duplicate entries.
* Atomic Order Checkout: Relational database transaction processing that snapshots live cart entries into permanent order items, locking in the historical price (`price_at_order`) to protect against retroactive price changes.

### 4. Automated Infrastructure
* Background Daemon Automation: Distributed asynchronous task management using Celery and Redis to automatically purge expired tokens from the database.

---

## Tech Stack

* Framework: FastAPI (Asynchronous ASGI)
* Data Validation: Pydantic v2
* ORM: SQLAlchemy 2.0 (Async Engine)
* Database: PostgreSQL
* Task Queue & Scheduler: Celery and Celery Beat
* Message Broker: Redis
* Dependency Management: Poetry
* Containerization: Docker and Docker Compose

---

## Project Directory Layout


src/
├── config/          # Application settings and environment parsing
├── database/        # Connection engines, session factories, and SQLAlchemy models
├── routers/         # HTTP endpoint route definitions
├── schemas/         # Pydantic data serialization and validation contracts
├── services/        # Core business logic processing layers
└── worker/          # Celery worker initialization and task runners

```

---

## Installation and Local Setup

### Prerequisites

* Python 3.11 or higher
* Poetry
* Redis Server
* PostgreSQL Server

### 1. Clone the Repository

```bash
git clone <repository-url>
cd online-cinema-project

```

### 2. Install Dependencies

Install the project dependencies within an isolated virtual environment using Poetry:

```bash
poetry install

```

### 3. Environment Configuration

Create a `.env` file in the root directory and populate your configuration keys:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/online_cinema
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_super_secret_jwt_signing_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

```

### 4. Database Migrations

Run Alembic migrations to apply the database schema to your local PostgreSQL instance:

```bash
poetry run alembic upgrade head

```

---

## Running the System

The system requires three separate execution processes to run concurrently. Execute each command in a separate terminal window or tab within your virtual environment.

### 1. Start the FastAPI Web Server

```bash
poetry run uvicorn src.main:app --reload

```

### 2. Start the Celery Execution Worker

```bash
poetry run celery -A src.worker.celery_app:celery_app worker --loglevel=info

```

### 3. Start the Celery Beat Scheduler

```bash
poetry run celery -A src.worker.celery_app:celery_app beat --loglevel=info

```

---

## API Documentation and Interactive Testing

Once the FastAPI application server is running, the fully interactive Swagger and OpenAPI documentation is accessible via your web browser:

* Interactive Swagger UI: http://127.0.0.1:8000/docs
* Alternative ReDoc UI: http://127.0.0.1:8000/redoc

All endpoints, including the checkout pipelines and role-based permissions, can be executed and profiled directly through the Swagger interface using an active authorization bearer token.

```

```