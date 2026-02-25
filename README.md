# Claims Processing Service

A minimal REST API that simulates health insurance claim submission and adjudication, built with **Python 3.12**, **FastAPI**, and **async SQLAlchemy**.

---

## Architecture Decisions

| Decision | Rationale |
|---|---|
| **FastAPI** | Automatic OpenAPI docs, Pydantic validation, native async support, minimal boilerplate. |
| **Async SQLAlchemy 2.0** | Non-blocking DB I/O for higher concurrency. `AsyncSession` + `create_async_engine`. |
| **SQLite (dev) / PostgreSQL (prod)** | Zero-config locally via `aiosqlite`. Swap to Postgres by changing `DATABASE_URL`. |
| **Alembic migrations** | Schema changes are versioned and repeatable. Configured for async engine. |
| **API key authentication** | API key over JWT because this is a service-to-service API with no user/role model. API keys are simpler and appropriate when the caller is another backend system rather than end users.
| **Layered architecture** | `schemas/` (Pydantic I/O) → `api/` (HTTP) → `services/` (business logic) → `models/` (persistence). Keeps business rules testable without HTTP. |
| **Mock data as constants** | Reference data (members, providers, benefit limits, procedure costs) lives in `services/mock_data.py` — easy to find, easy to replace with DB tables later. |
| **UUID primary keys** | Avoids sequential ID enumeration; safe for external exposure. |

### Adjudication Flow

```
Submit Claim
  ├── Member eligibility check (active / inactive / unknown)
  ├── Provider validation
  ├── Benefit limit check (caps approved_amount per diagnosis)
  ├── Fraud rule (claim > 2× avg procedure cost → flag)
  └── Resolve status: APPROVED | PARTIAL | REJECTED
```

---

## How to Run Locally

### Prerequisites
- Python 3.12+
- pip

### Option 1 — Direct

```bash
pip install -r requirements.txt

# Run migrations
python -m alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### Option 2 — Docker

```bash
docker compose up --build
```

### Run Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./claims.db` | Async DB connection string |
| `API_KEY` | `dev-test-api-key` | API key for authentication |
| `LOG_LEVEL` | `INFO` | Logging level |

For PostgreSQL, set:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

---

## Sample API Requests

All `/claims` endpoints require the `X-API-Key` header.

### Submit a Claim (APPROVED)

```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-test-api-key" \
  -d '{
    "member_id": "M123",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 30000
  }'
```

Response (`201`):
```json
{
  "claim_id": "...",
  "status": "APPROVED",
  "fraud_flag": false,
  "approved_amount": 30000.0,
  "rejection_reasons": null
}
```

### Submit a Claim (PARTIAL + fraud flag)

```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-test-api-key" \
  -d '{
    "member_id": "M123",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 50000
  }'
```

Response (`201`):
```json
{
  "claim_id": "...",
  "status": "PARTIAL",
  "fraud_flag": true,
  "approved_amount": 40000.0,
  "rejection_reasons": null
}
```

### Submit a Claim (REJECTED — inactive member)

```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-test-api-key" \
  -d '{
    "member_id": "M125",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 10000
  }'
```

Response (`201`):
```json
{
  "claim_id": "...",
  "status": "REJECTED",
  "fraud_flag": false,
  "approved_amount": 0.0,
  "rejection_reasons": ["Member M125 is not eligible (status: inactive)"]
}
```

### List Claims (with pagination and filters)

```bash
# All claims, page 1
curl -H "X-API-Key: dev-test-api-key" \
  "http://localhost:8000/claims?page=1&page_size=10"

# Filter by member
curl -H "X-API-Key: dev-test-api-key" \
  "http://localhost:8000/claims?member_id=M123"

# Filter by status
curl -H "X-API-Key: dev-test-api-key" \
  "http://localhost:8000/claims?status=REJECTED"

# Filter by fraud flag
curl -H "X-API-Key: dev-test-api-key" \
  "http://localhost:8000/claims?fraud_flag=true"
```

Response:
```json
{
  "items": [{ "claim_id": "...", "status": "APPROVED", "..." : "..." }],
  "total": 42,
  "page": 1,
  "page_size": 10,
  "pages": 5
}
```

### Retrieve a Claim

```bash
curl -H "X-API-Key: dev-test-api-key" \
  http://localhost:8000/claims/{claim_id}
```

### Health Check (no auth required)

```bash
curl http://localhost:8000/health
```

---

## Database Migrations

```bash
# Create a new migration after changing models
python -m alembic revision --autogenerate -m "describe change"

# Apply all pending migrations
python -m alembic upgrade head

# Rollback one migration
python -m alembic downgrade -1
```

---

## What I Would Improve for Production

- **Rate limiting**: Protect against abuse (e.g., `slowapi`).
- **External reference data**: Move members/providers/benefits to database tables with admin CRUD endpoints.
- **Audit trail**: Log every adjudication decision with timestamps for compliance.
- **Observability**: Structured JSON logging, OpenTelemetry traces, Prometheus metrics.
- **CI/CD**: GitHub Actions pipeline with lint (ruff), type-check (mypy), test, and Docker build stages.
- **Input sanitization**: Additional validation on code formats (regex patterns for ICD/CPT codes).
- **JWT authentication**: Replace API key with JWT for role-based access control.

---

## Project Structure

```
├── alembic/
│   ├── versions/              # Migration scripts
│   └── env.py                 # Async migration runner
├── app/
│   ├── api/
│   │   └── claims.py          # REST endpoints (async)
│   ├── models/
│   │   └── claim.py           # SQLAlchemy model
│   ├── schemas/
│   │   └── claim.py           # Pydantic request/response schemas
│   ├── services/
│   │   ├── claim_processor.py # Adjudication business logic
│   │   └── mock_data.py       # Reference data (members, providers, etc.)
│   ├── auth.py                # API key authentication
│   ├── config.py              # Settings via env vars
│   ├── database.py            # Async DB engine and session
│   └── main.py                # FastAPI app entrypoint
├── tests/
│   ├── conftest.py            # Async test fixtures
│   ├── test_api.py            # Integration tests (24 tests)
│   └── test_claim_processor.py # Unit tests (business logic)
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```
