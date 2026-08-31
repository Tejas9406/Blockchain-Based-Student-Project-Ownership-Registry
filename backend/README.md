# Backend & Database Module — Developer 2 Guide

> **Module Owner**: Developer 2  
> **Stack**: Python 3.12/3.13, FastAPI, SQLAlchemy, Alembic, PostgreSQL 16, Pydantic v2, Pytest  
> **Phase**: Phase 0 (Environment Foundation)

---

## 1. Directory Structure

```
backend/
├── alembic/              # Database migration scripts & env
│   ├── versions/         # Revision files
│   ├── env.py            # Migration runtime logic
│   └── script.py.mako    # Revision template
├── app/
│   ├── core/             # Configuration & logging settings
│   ├── database/         # Engine, sessionmaker, base declarative class
│   ├── models/           # SQLAlchemy database ORM models
│   ├── schemas/          # Pydantic request/response validation schemas
│   ├── routers/          # FastAPI API route controllers
│   ├── services/         # Domain business logic layer
│   ├── utils/            # Shared backend utilities
│   └── main.py           # FastAPI application entrypoint
├── tests/                # Pytest test suite
├── Dockerfile            # Container configuration
├── alembic.ini           # Alembic configuration
├── requirements.txt      # Python dependencies
└── README.md             # This document
```

---

## 2. Setup & Development

### 2.1 Prerequisites
- Python `3.11+` (Recommended: `3.12` or `3.13`)
- PostgreSQL `15+` or `16+` (or via Docker Compose)

### 2.2 Local Virtual Environment Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment:
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2.3 Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Ensure `DATABASE_URL` matches your local or Dockerized PostgreSQL credentials:
```env
DATABASE_URL=postgresql://registry_user:registry_password_dev@localhost:5432/project_registry_db
```

### 2.4 Running the FastAPI Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Health check**: `http://localhost:8000/health`
- **Swagger Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## 3. Database Migrations (Alembic)

```bash
# Generate a new migration revision
alembic revision --autogenerate -m "create_initial_schema"

# Apply migrations to database
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

---

## 4. Running Backend Tests

```bash
# Run test suite
pytest

# Run tests with verbose output
pytest -v
```

---

## 5. Developer Rules for Backend

1. **Keep Secrets out of Git**: Always load connection strings, JWT secrets, and keys through `app.core.config.settings`.
2. **Schema & Model Separation**: Keep SQLAlchemy ORM models in `app/models/` and Pydantic validation schemas in `app/schemas/`.
3. **Database Migrations**: Never manually alter SQL schema in production/shared environments; always author an Alembic migration.
4. **Follow API Contract**: Consult `docs/api/API_CONTRACT.md` before adding endpoints.
