from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from decimal import Decimal
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.core.auth import get_current_active_user, require_ar_executive
from app.models import Denial, Claim, AppealStatus
from app.schemas import Denial as DenialSchema, DenialCreate, DenialUpdate, DenialTopCodesResponse, AppealDraftRequest, AppealDraftResponse
from app.services.appeal_agent import draft_appeal_letter
from app.services.agent_logger import log_agent_run

router = APIRouter()


@router.get("", response_model=List[DenialSchema])
async def list_denials(
    claim_id: Optional[int] = None,
    denial_code: Optional[str] = None,
    appeal_status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = select(Denial).options(
        selectinload(Denial.claim).selectinload(Claim.patient),
        selectinload(Denial.claim).selectinload(Claim.provider),
        selectinload(Denial.claim).selectinload(Claim.payer)
    )

    if claim_id:
        query = query.where(Denial.claim_id == claim_id)
    if denial_code:
        query = query.where(Denial.denial_code == denial_code)
    if appeal_status:
        query = query.where(Denial.appeal_status == appeal_status)
    if date_from:
        query = query.where(Denial.denial_date >= date_from)
    if date_to:
        query = query.where(Denial.denial_date <= date_to)

    query = query.order_by(Denial.denial_date.desc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/top-codes", response_model=List[DenialTopCodesResponse])
async def get_top_denial_codes(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = (
        select(
            Denial.denial_code,
            func.count(Denial.denial_id).label("count"),
            func.sum(Denial.denied_amount).label("total_denied"),
            func.avg(Denial.denied_amount).label("avg_denied")
        )
        .where(Denial.denial_code.isnot(None))
        .group_by(Denial.denial_code)
        .order_by(func.count(Denial.denial_id).desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return [
        DenialTopCodesResponse(
            denial_code=row.denial_code,
            count=row.count,
            total_denied_amount=row.total_denied or Decimal("0"),
            avg_denied_amount=row.avg_denied or Decimal("0")
        )
        for row in result.all()
    ]


@router.get("/{denial_id}", response_model=DenialSchema)
async def get_denial(
    denial_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = select(Denial).options(
        selectinload(Denial.claim).selectinload(Claim.patient),
        selectinload(Denial.claim).selectinload(Claim.provider),
        selectinload(Denial.claim).selectinload(Claim.payer)
    ).where(Denial.denial_id == denial_id)

    result = await db.execute(query)
    denial = result.scalar_one_or_none()

    if not denial:
        raise HTTPException(status_code=404, detail="Denial not found")

    return denial


@router.patch("/{denial_id}", response_model=DenialSchema)
async def update_denial(
    denial_id: int,
    denial_data: DenialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(select(Denial).where(Denial.denial_id == denial_id))
    denial = result.scalar_one_or_none()

    if not denial:
        raise HTTPException(status_code=404, detail="Denial not found")

    update_data = denial_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(denial, field, value)

    await db.commit()
    await db.refresh(denial)
    return denial


@router.post("/{denial_id}/draft-appeal", response_model=AppealDraftResponse)
async def draft_appeal(
    denial_id: int,
    request: AppealDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Denial).options(
            selectinload(Denial.claim).selectinload(Claim.patient),
            selectinload(Denial.claim).selectinload(Claim.provider),
            selectinload(Denial.claim).selectinload(Claim.payer)
        ).where(Denial.denial_id == denial_id)
    )
    denial = result.scalar_one_or_none()

    if not denial:
        raise HTTPException(status_code=404, detail="Denial not found")

    appeal_letter, confidence, hitl_required = await draft_appeal_letter(denial, request.additional_context)

    await log_agent_run(
        db=db,
        claim_id=denial.claim_id,
        agent_type="appeal_drafter",
        input_payload={"denial_id": denial_id, "additional_context": request.additional_context},
        output_payload={"appeal_letter": appeal_letter},
        confidence=confidence,
        hitl_required=hitl_required
    )

    denial.appeal_status = AppealStatus.drafted
    denial.appeal_drafted_by_ai = True
    await db.commit()

    return AppealDraftResponse(
        appeal_letter=appeal_letter,
        confidence=confidence,
        hitl_required=hitl_required
    )