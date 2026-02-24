import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    member_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    diagnosis_code: Mapped[str] = mapped_column(String(20), nullable=False)
    procedure_code: Mapped[str] = mapped_column(String(20), nullable=False)
    claim_amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    fraud_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_amount: Mapped[float] = mapped_column(Float, default=0.0)
    rejection_reasons: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
