import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.claim import Claim
from app.schemas.claim import ClaimDetailResponse, ClaimRequest, ClaimResponse
from app.services.claim_processor import ClaimProcessor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/claims", tags=["claims"])

processor = ClaimProcessor()


@router.post(
    "",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_claim(payload: ClaimRequest, db: Session = Depends(get_db)):
    result = processor.adjudicate(
        member_id=payload.member_id,
        provider_id=payload.provider_id,
        diagnosis_code=payload.diagnosis_code,
        procedure_code=payload.procedure_code,
        claim_amount=payload.claim_amount,
    )

    claim = Claim(
        member_id=payload.member_id,
        provider_id=payload.provider_id,
        diagnosis_code=payload.diagnosis_code,
        procedure_code=payload.procedure_code,
        claim_amount=payload.claim_amount,
        status=result.status,
        fraud_flag=result.fraud_flag,
        approved_amount=result.approved_amount,
        rejection_reasons=(
            json.dumps(result.rejection_reasons)
            if result.rejection_reasons
            else None
        ),
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)

    return ClaimResponse(
        claim_id=claim.id,
        status=claim.status,
        fraud_flag=claim.fraud_flag,
        approved_amount=claim.approved_amount,
        rejection_reasons=result.rejection_reasons or None,
    )


@router.get("/{claim_id}", response_model=ClaimDetailResponse)
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found",
        )

    rejection_reasons = None
    if claim.rejection_reasons:
        rejection_reasons = json.loads(claim.rejection_reasons)

    return ClaimDetailResponse(
        claim_id=claim.id,
        member_id=claim.member_id,
        provider_id=claim.provider_id,
        diagnosis_code=claim.diagnosis_code,
        procedure_code=claim.procedure_code,
        claim_amount=claim.claim_amount,
        status=claim.status,
        fraud_flag=claim.fraud_flag,
        approved_amount=claim.approved_amount,
        rejection_reasons=rejection_reasons,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
    )
