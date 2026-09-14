from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from decimal import Decimal
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models import WorkQueue as WorkQueueModel, ClaimQueueAssignment as CQAModel, Claim as ClaimModel, ClaimStatus
from app.schemas import WorkQueueCreate, WorkQueueUpdate, WorkQueue as WorkQueueSchema, WorkQueueSummary, ClaimQueueAssignment as CQASchema, Claim as ClaimSchema

router = APIRouter()


@router.get("", response_model=List[WorkQueueSummary])
async def list_work_queues(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = (
        select(
            WorkQueueModel.queue_id,
            WorkQueueModel.name,
            WorkQueueModel.priority,
            func.count(CQAModel.id).label("claim_count"),
            func.sum(ClaimModel.charge_amount - ClaimModel.paid_amount).label("total_value")
        )
        .outerjoin(CQAModel, WorkQueueModel.queue_id == CQAModel.queue_id)
        .outerjoin(ClaimModel, and_(
            CQAModel.claim_id == ClaimModel.claim_id,
            CQAModel.resolved_at.is_(None)
        ))
        .group_by(WorkQueueModel.queue_id, WorkQueueModel.name, WorkQueueModel.priority)
        .order_by(WorkQueueModel.priority.desc(), WorkQueueModel.name)
    )
    result = await db.execute(query)

    return [
        WorkQueueSummary(
            queue_id=row.queue_id,
            name=row.name,
            priority=row.priority,
            claim_count=row.claim_count or 0,
            total_value=row.total_value or Decimal("0")
        )
        for row in result.all()
    ]


@router.post("", response_model=WorkQueueSchema, status_code=201)
async def create_work_queue(
    queue_data: WorkQueueCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    queue = WorkQueueModel(**queue_data.model_dump())
    db.add(queue)
    await db.commit()
    await db.refresh(queue)
    return queue


@router.get("/{queue_id}", response_model=WorkQueueSchema)
async def get_work_queue(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(select(WorkQueueModel).where(WorkQueueModel.queue_id == queue_id))
    queue = result.scalar_one_or_none()
    if not queue:
        raise HTTPException(status_code=404, detail="Work queue not found")
    return queue


@router.patch("/{queue_id}", response_model=WorkQueueSchema)
async def update_work_queue(
    queue_id: int,
    queue_data: WorkQueueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(select(WorkQueueModel).where(WorkQueueModel.queue_id == queue_id))
    queue = result.scalar_one_or_none()
    if not queue:
        raise HTTPException(status_code=404, detail="Work queue not found")

    update_data = queue_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(queue, field, value)

    await db.commit()
    await db.refresh(queue)
    return queue


@router.get("/{queue_id}/claims", response_model=List[ClaimSchema])
async def get_queue_claims(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = (
        select(ClaimModel)
        .join(CQAModel, ClaimModel.claim_id == CQAModel.claim_id)
        .where(
            CQAModel.queue_id == queue_id,
            CQAModel.resolved_at.is_(None)
        )
        .options(
            selectinload(ClaimModel.patient),
            selectinload(ClaimModel.provider),
            selectinload(ClaimModel.payer)
        )
        .order_by(ClaimModel.date_of_service)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{queue_id}/claims/{claim_id}/resolve")
async def resolve_claim_in_queue(
    queue_id: int,
    claim_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(
        select(CQAModel).where(
            CQAModel.queue_id == queue_id,
            CQAModel.claim_id == claim_id,
            CQAModel.resolved_at.is_(None)
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Claim not found in this queue")

    from datetime import datetime
    assignment.resolved_at = datetime.utcnow()
    await db.commit()

    return {"message": "Claim resolved in queue", "claim_id": claim_id, "queue_id": queue_id}