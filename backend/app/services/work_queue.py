from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Claim, WorkQueue, ClaimQueueAssignment, ClaimStatus, Denial
from decimal import Decimal


async def assign_claim_to_queue(db: AsyncSession, claim_id: int) -> ClaimQueueAssignment:
    result = await db.execute(select(Claim).where(Claim.claim_id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise ValueError(f"Claim {claim_id} not found")

    existing = await db.execute(
        select(ClaimQueueAssignment).where(
            ClaimQueueAssignment.claim_id == claim_id,
            ClaimQueueAssignment.resolved_at.is_(None)
        )
    )
    if existing.scalar_one_or_none():
        return existing.scalar_one()

    queue = await determine_queue(db, claim)
    if not queue:
        queue = await get_default_queue(db)

    assignment = ClaimQueueAssignment(claim_id=claim_id, queue_id=queue.queue_id)
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def determine_queue(db: AsyncSession, claim: Claim) -> WorkQueue | None:
    denial = await db.execute(
        select(Denial).where(Denial.claim_id == claim.claim_id).order_by(Denial.denial_date.desc())
    )
    denial = denial.scalar_one_or_none()

    if denial:
        if denial.appeal_status.value in ["not_started", "drafted"]:
            return await get_queue_by_name(db, "Appeals - Drafting")
        elif denial.appeal_status.value == "submitted":
            return await get_queue_by_name(db, "Appeals - Follow-up")

    if claim.denial_predicted and (claim.denial_probability or 0) > Decimal("0.7"):
        return await get_queue_by_name(db, "High Risk - Denial Prevention")

    if claim.status == ClaimStatus.denied:
        return await get_queue_by_name(db, "Denials - Work")

    if claim.status in [ClaimStatus.submitted, ClaimStatus.acknowledged, ClaimStatus.in_process]:
        days_outstanding = (await db.execute(select(func.julianday(func.date('now')) - func.julianday(claim.date_of_service)))).scalar()
        if days_outstanding and days_outstanding > 60:
            return await get_queue_by_name(db, "Aging - 60+ Days")
        elif days_outstanding and days_outstanding > 30:
            return await get_queue_by_name(db, "Aging - 30-60 Days")

    return await get_queue_by_name(db, "New Claims - Review")


async def get_queue_by_name(db: AsyncSession, name: str) -> WorkQueue | None:
    result = await db.execute(select(WorkQueue).where(WorkQueue.name == name))
    return result.scalar_one_or_none()


async def get_default_queue(db: AsyncSession) -> WorkQueue:
    result = await db.execute(select(WorkQueue).where(WorkQueue.name == "New Claims - Review"))
    queue = result.scalar_one_or_none()
    if not queue:
        queue = WorkQueue(name="New Claims - Review", priority="medium", rule_definition={})
        db.add(queue)
        await db.commit()
        await db.refresh(queue)
    return queue


async def reassign_claim(db: AsyncSession, claim_id: int, queue_id: int) -> ClaimQueueAssignment:
    result = await db.execute(
        select(ClaimQueueAssignment).where(
            ClaimQueueAssignment.claim_id == claim_id,
            ClaimQueueAssignment.resolved_at.is_(None)
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.resolved_at = func.now()

    assignment = ClaimQueueAssignment(claim_id=claim_id, queue_id=queue_id)
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment