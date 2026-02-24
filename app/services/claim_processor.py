"""Core claim adjudication logic.

Each validation step is a separate method so individual rules
can be tested and extended independently.
"""

import logging
from dataclasses import dataclass, field

from app.services.mock_data import (
    BENEFIT_LIMITS,
    MEMBERS,
    PROCEDURE_AVG_COSTS,
    PROVIDERS,
)

logger = logging.getLogger(__name__)

FRAUD_COST_MULTIPLIER = 2.0


@dataclass
class AdjudicationResult:
    status: str = "APPROVED"
    approved_amount: float = 0.0
    fraud_flag: bool = False
    rejection_reasons: list[str] = field(default_factory=list)


class ClaimProcessor:
    """Runs a claim through eligibility, benefit, and fraud checks."""

    def adjudicate(
        self,
        member_id: str,
        provider_id: str,
        diagnosis_code: str,
        procedure_code: str,
        claim_amount: float,
    ) -> AdjudicationResult:
        result = AdjudicationResult(approved_amount=claim_amount)

        self._check_member_eligibility(member_id, result)
        self._check_provider(provider_id, result)
        self._check_benefit_limit(diagnosis_code, claim_amount, result)
        self._check_fraud(procedure_code, claim_amount, result)

        self._resolve_status(claim_amount, result)

        logger.info(
            "Adjudicated claim: member=%s status=%s approved=%.2f fraud=%s",
            member_id,
            result.status,
            result.approved_amount,
            result.fraud_flag,
        )
        return result

    def _check_member_eligibility(
        self, member_id: str, result: AdjudicationResult
    ) -> None:
        member = MEMBERS.get(member_id)
        if member is None:
            result.rejection_reasons.append(f"Unknown member: {member_id}")
            result.approved_amount = 0.0
            return
        if member["status"] != "active":
            result.rejection_reasons.append(
                f"Member {member_id} is not eligible (status: {member['status']})"
            )
            result.approved_amount = 0.0

    def _check_provider(self, provider_id: str, result: AdjudicationResult) -> None:
        if provider_id not in PROVIDERS:
            result.rejection_reasons.append(f"Unknown provider: {provider_id}")
            result.approved_amount = 0.0

    def _check_benefit_limit(
        self, diagnosis_code: str, claim_amount: float, result: AdjudicationResult
    ) -> None:
        limit = BENEFIT_LIMITS.get(diagnosis_code)
        if limit is None:
            result.rejection_reasons.append(
                f"No benefit coverage for diagnosis: {diagnosis_code}"
            )
            result.approved_amount = 0.0
            return
        if claim_amount > limit:
            result.approved_amount = min(result.approved_amount, limit)

    def _check_fraud(
        self, procedure_code: str, claim_amount: float, result: AdjudicationResult
    ) -> None:
        avg_cost = PROCEDURE_AVG_COSTS.get(procedure_code)
        if avg_cost is None:
            result.rejection_reasons.append(
                f"Unknown procedure code: {procedure_code}"
            )
            result.approved_amount = 0.0
            return
        if claim_amount > avg_cost * FRAUD_COST_MULTIPLIER:
            result.fraud_flag = True

    def _resolve_status(
        self, claim_amount: float, result: AdjudicationResult
    ) -> None:
        if result.rejection_reasons:
            result.status = "REJECTED"
            result.approved_amount = 0.0
        elif result.approved_amount < claim_amount:
            result.status = "PARTIAL"
