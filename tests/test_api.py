import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_db():
    """Recreate tables for each test so state doesn't leak."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_submit_and_retrieve_approved_claim():
    resp = client.post(
        "/claims",
        json={
            "member_id": "M123",
            "provider_id": "H456",
            "diagnosis_code": "D001",
            "procedure_code": "P001",
            "claim_amount": 30000,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "APPROVED"
    assert data["approved_amount"] == 30000
    assert data["fraud_flag"] is False

    # Retrieve
    claim_id = data["claim_id"]
    resp2 = client.get(f"/claims/{claim_id}")
    assert resp2.status_code == 200
    detail = resp2.json()
    assert detail["claim_id"] == claim_id
    assert detail["member_id"] == "M123"


def test_submit_partial_claim():
    resp = client.post(
        "/claims",
        json={
            "member_id": "M123",
            "provider_id": "H456",
            "diagnosis_code": "D001",
            "procedure_code": "P001",
            "claim_amount": 50000,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PARTIAL"
    assert data["approved_amount"] == 40000
    assert data["fraud_flag"] is True


def test_submit_rejected_claim():
    resp = client.post(
        "/claims",
        json={
            "member_id": "M125",
            "provider_id": "H456",
            "diagnosis_code": "D001",
            "procedure_code": "P001",
            "claim_amount": 10000,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert data["approved_amount"] == 0


def test_get_nonexistent_claim():
    resp = client.get("/claims/nonexistent-id")
    assert resp.status_code == 404


def test_invalid_payload():
    resp = client.post("/claims", json={"member_id": "M123"})
    assert resp.status_code == 422


def test_negative_amount():
    resp = client.post(
        "/claims",
        json={
            "member_id": "M123",
            "provider_id": "H456",
            "diagnosis_code": "D001",
            "procedure_code": "P001",
            "claim_amount": -100,
        },
    )
    assert resp.status_code == 422
