import pytest

from tests.conftest import AUTH_HEADERS

pytestmark = pytest.mark.asyncio

VALID_CLAIM = {
    "member_id": "M123",
    "provider_id": "H456",
    "diagnosis_code": "D001",
    "procedure_code": "P001",
    "claim_amount": 30000,
}


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- Authentication ---


async def test_missing_api_key_returns_401(client):
    resp = await client.post("/claims", json=VALID_CLAIM)
    assert resp.status_code == 401


async def test_wrong_api_key_returns_401(client):
    resp = await client.post(
        "/claims", json=VALID_CLAIM, headers={"X-API-Key": "wrong"}
    )
    assert resp.status_code == 401


# --- POST /claims ---


async def test_submit_and_retrieve_approved_claim(client):
    resp = await client.post("/claims", json=VALID_CLAIM, headers=AUTH_HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "APPROVED"
    assert data["approved_amount"] == 30000
    assert data["fraud_flag"] is False

    claim_id = data["claim_id"]
    resp2 = await client.get(f"/claims/{claim_id}", headers=AUTH_HEADERS)
    assert resp2.status_code == 200
    detail = resp2.json()
    assert detail["claim_id"] == claim_id
    assert detail["member_id"] == "M123"


async def test_submit_partial_claim(client):
    resp = await client.post(
        "/claims",
        json={**VALID_CLAIM, "claim_amount": 50000},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PARTIAL"
    assert data["approved_amount"] == 40000
    assert data["fraud_flag"] is True


async def test_submit_rejected_claim(client):
    resp = await client.post(
        "/claims",
        json={**VALID_CLAIM, "member_id": "M125"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert data["approved_amount"] == 0


async def test_get_nonexistent_claim(client):
    resp = await client.get("/claims/nonexistent-id", headers=AUTH_HEADERS)
    assert resp.status_code == 404


async def test_invalid_payload(client):
    resp = await client.post(
        "/claims", json={"member_id": "M123"}, headers=AUTH_HEADERS
    )
    assert resp.status_code == 422


async def test_negative_amount(client):
    resp = await client.post(
        "/claims",
        json={**VALID_CLAIM, "claim_amount": -100},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 422


# --- GET /claims (list + pagination) ---


async def test_list_claims_empty(client):
    resp = await client.get("/claims", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0


async def test_list_claims_with_data(client):
    # Submit 3 claims
    for _ in range(3):
        await client.post("/claims", json=VALID_CLAIM, headers=AUTH_HEADERS)

    resp = await client.get("/claims", headers=AUTH_HEADERS)
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


async def test_list_claims_pagination(client):
    for _ in range(5):
        await client.post("/claims", json=VALID_CLAIM, headers=AUTH_HEADERS)

    resp = await client.get(
        "/claims", params={"page": 1, "page_size": 2}, headers=AUTH_HEADERS
    )
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["pages"] == 3

    resp2 = await client.get(
        "/claims", params={"page": 3, "page_size": 2}, headers=AUTH_HEADERS
    )
    data2 = resp2.json()
    assert len(data2["items"]) == 1


async def test_list_claims_filter_by_status(client):
    await client.post("/claims", json=VALID_CLAIM, headers=AUTH_HEADERS)
    await client.post(
        "/claims",
        json={**VALID_CLAIM, "member_id": "M125"},
        headers=AUTH_HEADERS,
    )

    resp = await client.get(
        "/claims", params={"status": "REJECTED"}, headers=AUTH_HEADERS
    )
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "REJECTED"


async def test_list_claims_filter_by_member(client):
    await client.post("/claims", json=VALID_CLAIM, headers=AUTH_HEADERS)
    await client.post(
        "/claims",
        json={**VALID_CLAIM, "member_id": "M124"},
        headers=AUTH_HEADERS,
    )

    resp = await client.get(
        "/claims", params={"member_id": "M124"}, headers=AUTH_HEADERS
    )
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["member_id"] == "M124"


async def test_list_claims_filter_by_fraud(client):
    await client.post("/claims", json=VALID_CLAIM, headers=AUTH_HEADERS)
    await client.post(
        "/claims",
        json={**VALID_CLAIM, "claim_amount": 50000},
        headers=AUTH_HEADERS,
    )

    resp = await client.get(
        "/claims", params={"fraud_flag": True}, headers=AUTH_HEADERS
    )
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["fraud_flag"] is True
