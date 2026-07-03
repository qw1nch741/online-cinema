# CI/CD Pipeline Guide

This project uses **GitHub Actions** to run automated checks on every push and pull request.

Workflow file: `.github/workflows/ci.yml`

---

## When does CI run?

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

- **`on`** — defines trigger events.
- **`push`** — runs when you push commits to `main` or `develop`.
- **`pull_request`** — runs when someone opens/updates a PR targeting those branches.

---

## Job overview

```yaml
jobs:
  quality-and-tests:
    runs-on: ubuntu-latest
```

- **`jobs`** — list of parallel/sequential tasks in the workflow.
- **`quality-and-tests`** — custom job name (lint + type check + migrations + tests).
- **`runs-on: ubuntu-latest`** — executes on a fresh Ubuntu virtual machine in GitHub cloud.

---

## Service containers (Postgres + Redis)

```yaml
services:
  postgres:
    image: postgres:15-alpine
    ...
  redis:
    image: redis:7-alpine
    ...
```

- **`services`** — starts extra Docker containers linked to the job.
- **`image`** — which Docker image to run (same versions as local dev).
- **`env`** (Postgres) — creates DB user/password/database inside container.
- **`ports`** — exposes container ports to the runner (`5432`, `6379`).
- **`options: --health-cmd=...`** — waits until DB/Redis are ready before steps continue.

Why needed: future integration tests can connect to real Postgres/Redis during CI.

---

## Environment variables for the job

```yaml
env:
  POSTGRES_HOST: localhost
  REDIS_URL: redis://localhost:6379/0
  ...
```

- **`env`** — variables available to all steps in this job.
- App settings read these values (same as `.env` locally).
- `localhost` is correct in CI because service ports are mapped to the runner.

---

## Step-by-step commands

### 1) Checkout repository

```yaml
uses: actions/checkout@v4
```

Downloads your repository code into the CI runner so commands can access project files.

---

### 2) Set up Python

```yaml
uses: actions/setup-python@v5
with:
  python-version: "3.11"
```

Installs Python 3.11 on the runner (matches Dockerfile/runtime target).

---

### 3) Install Poetry

```bash
pip install poetry==1.8.3
```

Installs Poetry package manager used by this project.

---

### 4) Install project dependencies

```bash
poetry install --no-interaction
```

- Reads `pyproject.toml` + `poetry.lock`.
- Creates virtual environment and installs main + dev dependencies.
- `--no-interaction` prevents prompts (required in CI).

---

### 5) Run flake8

```bash
poetry run flake8 src tests
```

- **`flake8`** — linter for Python style/syntax issues.
- Checks source (`src`) and tests (`tests`).
- Config rules are in `.flake8` (line length, ignored warnings, excluded paths).
- Fails CI if style/syntax violations are found.

---

### 6) Run mypy

```bash
poetry run mypy src
```

- **`mypy`** — static type checker.
- Analyzes type hints without executing business flows.
- Config in `pyproject.toml` (`ignore_missing_imports`, migration exclusions).

---

### 7) Apply database migrations

```bash
poetry run alembic upgrade head
```

- Runs Alembic migrations against CI Postgres.
- Ensures schema can be applied cleanly from scratch.
- Validates migration chain integrity.

---

### 8) Run tests with coverage

```bash
poetry run pytest --cov=src --cov-report=term-missing --cov-report=xml
```

- **`pytest`** — test runner.
- **`--cov=src`** — measure code coverage for application code.
- **`--cov-report=term-missing`** — print uncovered lines in CI logs.
- **`--cov-report=xml`** — generate `coverage.xml` artifact for review/tools.

---

### 9) Upload coverage report

```yaml
uses: actions/upload-artifact@v4
with:
  name: coverage-report
  path: coverage.xml
```

Stores `coverage.xml` as downloadable workflow artifact in GitHub Actions UI.

---

## Local commands (same as CI)

Run these locally before pushing:

```bash
poetry install
poetry run flake8 src tests
poetry run mypy src
poetry run alembic upgrade head
poetry run pytest --cov=src --cov-report=term-missing
```

---

## Expected result

- Green check on PR = lint + type check + migrations + tests passed.
- Red check = inspect failed step logs in GitHub Actions and fix before merge.
