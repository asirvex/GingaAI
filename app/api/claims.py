import json
import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_api_key
from app.database import get_db
from app.models.claim import Claim
from app.schemas.claim import (
    ClaimDetailResponse,
    ClaimRequest,
    ClaimResponse,
    PaginatedClaimsResponse,
)
from app.services.claim_processor import ClaimProcessor

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/claims",
    tags=["claims"],
    dependencies=[Depends(require_api_key)],
)

processor = ClaimProcessor()


def _build_detail(claim: Claim) -> ClaimDetailResponse:
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


@router.post(
    "",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_claim(
    payload: ClaimRequest, db: AsyncSession = Depends(get_db)
):
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
    await db.commit()
    await db.refresh(claim)

    return ClaimResponse(
        claim_id=claim.id,
        status=claim.status,
        fraud_flag=claim.fraud_flag,
        approved_amount=claim.approved_amount,
        rejection_reasons=result.rejection_reasons or None,
    )


@router.get("", response_model=PaginatedClaimsResponse)
async def list_claims(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    member_id: str | None = Query(None, description="Filter by member ID"),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by status"
    ),
    fraud_flag: bool | None = Query(None, description="Filter by fraud flag"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Claim)
    count_query = select(func.count(Claim.id))

    if member_id:
        query = query.where(Claim.member_id == member_id)
        count_query = count_query.where(Claim.member_id == member_id)
    if status_filter:
        query = query.where(Claim.status == status_filter.upper())
        count_query = count_query.where(Claim.status == status_filter.upper())
    if fraud_flag is not None:
        query = query.where(Claim.fraud_flag == fraud_flag)
        count_query = count_query.where(Claim.fraud_flag == fraud_flag)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    query = query.order_by(Claim.created_at.desc()).offset(offset).limit(page_size)
    rows = (await db.execute(query)).scalars().all()

    return PaginatedClaimsResponse(
        items=[_build_detail(c) for c in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{claim_id}", response_model=ClaimDetailResponse)
async def get_claim(claim_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found",
        )
    return _build_detail(claim)
