# Claims Processing Service

A minimal REST API that simulates health insurance claim submission and adjudication, built with **Python 3.12**, **FastAPI**, and **SQLAlchemy**.

---

## Architecture Decisions

| Decision | Rationale |
|---|---|
| **FastAPI** | Automatic OpenAPI docs, Pydantic validation, async-ready, minimal boilerplate. |
| **SQLAlchemy 2.0 (mapped columns)** | Type-safe ORM with modern declarative syntax; easy to swap SQLite for PostgreSQL. |
| **SQLite (default)** | Zero-config for local dev. Swap via `DATABASE_URL` env var for production. |
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

---

## Sample API Requests

### Submit a Claim (APPROVED)

```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
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

### Retrieve a Claim

```bash
curl http://localhost:8000/claims/{claim_id}
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## What I Would Improve for Production

- **Database**: Replace SQLite with PostgreSQL; add Alembic migrations.
- **Authentication**: API key or JWT-based auth middleware.
- **Rate limiting**: Protect against abuse (e.g., `slowapi`).
- **Async DB sessions**: Use async SQLAlchemy engine for higher throughput.
- **External reference data**: Move members/providers/benefits to database tables with admin CRUD endpoints.
- **Audit trail**: Log every adjudication decision with timestamps for compliance.
- **Observability**: Structured JSON logging, OpenTelemetry traces, Prometheus metrics.
- **CI/CD**: GitHub Actions pipeline with lint (ruff), type-check (mypy), test, and Docker build stages.
- **Input sanitization**: Additional validation on code formats (regex patterns for ICD/CPT codes).
- **Pagination**: Add pagination to a `GET /claims` list endpoint.

---

## Project Structure

```
├── app/
│   ├── api/
│   │   └── claims.py          # REST endpoints
│   ├── models/
│   │   └── claim.py            # SQLAlchemy model
│   ├── schemas/
│   │   └── claim.py            # Pydantic request/response schemas
│   ├── services/
│   │   ├── claim_processor.py  # Adjudication business logic
│   │   └── mock_data.py        # Reference data (members, providers, etc.)
│   ├── config.py               # Settings via env vars
│   ├── database.py             # DB engine and session
│   └── main.py                 # FastAPI app entrypoint
├── tests/
│   ├── test_api.py             # Integration tests (HTTP)
│   └── test_claim_processor.py # Unit tests (business logic)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```
