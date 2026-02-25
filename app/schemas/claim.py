from datetime import datetime

from pydantic import BaseModel, Field


class ClaimRequest(BaseModel):
    member_id: str = Field(..., min_length=1, max_length=50, examples=["M123"])
    provider_id: str = Field(..., min_length=1, max_length=50, examples=["H456"])
    diagnosis_code: str = Field(..., min_length=1, max_length=20, examples=["D001"])
    procedure_code: str = Field(..., min_length=1, max_length=20, examples=["P001"])
    claim_amount: float = Field(..., gt=0, examples=[50000])


class ClaimResponse(BaseModel):
    claim_id: str
    status: str
    fraud_flag: bool
    approved_amount: float
    rejection_reasons: list[str] | None = None

    model_config = {"from_attributes": True}


class ClaimDetailResponse(ClaimResponse):
    member_id: str
    provider_id: str
    diagnosis_code: str
    procedure_code: str
    claim_amount: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedClaimsResponse(BaseModel):
    items: list[ClaimDetailResponse]
    total: int
    page: int
    page_size: int
    pages: int
