from app.services.claim_processor import ClaimProcessor


processor = ClaimProcessor()


def test_approved_claim():
    result = processor.adjudicate("M123", "H456", "D001", "P001", 30000)
    assert result.status == "APPROVED"
    assert result.approved_amount == 30000
    assert result.fraud_flag is False
    assert result.rejection_reasons == []


def test_partial_approval_benefit_limit():
    """Claim of 50000 against D001 limit of 40000 -> PARTIAL."""
    result = processor.adjudicate("M123", "H456", "D001", "P001", 50000)
    assert result.status == "PARTIAL"
    assert result.approved_amount == 40000
    assert result.fraud_flag is True  # 50000 > 2 * 20000


def test_fraud_flag():
    """Claim > 2x average procedure cost is flagged."""
    result = processor.adjudicate("M123", "H456", "D002", "P001", 45000)
    assert result.fraud_flag is True
    assert result.status == "APPROVED"  # still approved, just flagged
    assert result.approved_amount == 45000


def test_inactive_member_rejected():
    result = processor.adjudicate("M125", "H456", "D001", "P001", 10000)
    assert result.status == "REJECTED"
    assert result.approved_amount == 0.0
    assert any("not eligible" in r for r in result.rejection_reasons)


def test_unknown_member_rejected():
    result = processor.adjudicate("UNKNOWN", "H456", "D001", "P001", 10000)
    assert result.status == "REJECTED"
    assert any("Unknown member" in r for r in result.rejection_reasons)


def test_unknown_provider_rejected():
    result = processor.adjudicate("M123", "UNKNOWN", "D001", "P001", 10000)
    assert result.status == "REJECTED"


def test_unknown_diagnosis_rejected():
    result = processor.adjudicate("M123", "H456", "D999", "P001", 10000)
    assert result.status == "REJECTED"
    assert any("No benefit coverage" in r for r in result.rejection_reasons)


def test_unknown_procedure_rejected():
    result = processor.adjudicate("M123", "H456", "D001", "P999", 10000)
    assert result.status == "REJECTED"
    assert any("Unknown procedure" in r for r in result.rejection_reasons)


def test_no_fraud_at_boundary():
    """Exactly 2x average cost should NOT be flagged."""
    result = processor.adjudicate("M123", "H456", "D001", "P001", 40000)
    assert result.fraud_flag is False
