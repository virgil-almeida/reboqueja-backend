# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ReboqueJá** is a Django REST Framework API connecting drivers (motoristas) with tow truck providers (prestadores) via geolocation-based matching. When a vehicle breaks down, drivers create service requests that are matched to nearby available providers using the Haversine algorithm.

## Commands

### Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then edit with SECRET_KEY, DATABASE_URL, etc.
python manage.py migrate
```

### Run
```bash
python manage.py runserver
```

### Test
```bash
# Required env vars for tests (SQLite is used, no PostgreSQL needed locally)
export SECRET_KEY="test-secret-key-for-local-pytest-only-32chars"
export DEBUG=True
export DATABASE_URL=sqlite:///test.sqlite3
export ALLOWED_HOSTS=localhost,127.0.0.1,testserver

pytest                          # all tests with coverage
pytest services/tests/          # specific directory
pytest tests/test_api_flows.py  # specific file
pytest -k "test_geo"            # specific test by name
```

Minimum 60% coverage is enforced. See `.coveragerc` for exclusions and `pytest.ini` for config.

## Architecture

### Apps

- **`users/`** — Custom `AbstractUser` with email-based auth, plus `Motorista` (driver) and `Prestador` (provider) profile models via OneToOne FK. Handles registration, JWT auth, profile management, and availability toggling.
- **`services/`** — Core domain. `Solicitacao` (service request) model with a state machine lifecycle. Handles request creation, geolocation matching, and status transitions.
- **`ratings/`** — `Avaliacao` model for post-service ratings (1–5 stars). Only motoristas can rate, only after a `CONCLUIDO` request.
- **`config/`** — Django settings, root URL routing, WSGI/ASGI entrypoints.
- **`tests/`** — Integration tests using Factory Boy fixtures (`tests/factories.py`, `tests/conftest.py`).

### Key Files

| File | Purpose |
|------|---------|
| `services/transitions.py` | State machine: validates and applies status transitions with atomic transactions |
| `services/geo.py` | Haversine distance calculation for nearby-provider matching |
| `services/filters.py` | QuerySet filters for history endpoints (status, date range) |
| `users/permissions.py` | Custom DRF permission classes (e.g. `IsMotorista`, `IsPrestador`) |
| `users/validators.py` | CPF and other input validators |
| `ratings/stats.py` | Rating average helpers for provider profiles |

### Service Request Lifecycle

State machine defined in `services/transitions.py`:

```
PENDENTE → ACEITO → A_CAMINHO → CONCLUIDO
PENDENTE → CANCELADO  (motorista only, while still pending)
```

Each transition is enforced in a dedicated function (`aplicar_aceite`, `aplicar_cancelamento_motorista`, `aplicar_status_prestador`) with `transaction.atomic()`.

### Authentication

JWT-only via `djangorestframework-simplejwt`. Access tokens expire in 60 min, refresh in 7 days. Default permission is `AllowAny`; protected endpoints declare `IsAuthenticated` + role permission explicitly.

### Database

PostgreSQL in production, SQLite for development and CI. Configured via `DATABASE_URL` env var using `django-environ`.

## API Documentation

Auto-generated OpenAPI 3.0 docs via `drf-spectacular`:
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`

## Environment Variables

See `.env.example`. Required: `SECRET_KEY`, `DATABASE_URL`, `DEBUG`, `ALLOWED_HOSTS`.

## Deployment

`Procfile` targets Heroku/Render. Pre-deploy runs `migrate` + `collectstatic`; web process uses Gunicorn.
