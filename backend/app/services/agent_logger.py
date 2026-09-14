from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from app.models import AgentRun, AgentType
from app.schemas import ReviewDecision


async def log_agent_run(
    db: AsyncSession,
    claim_id: int,
    agent_type: str,
    input_payload: dict,
    output_payload: dict,
    confidence: Decimal,
    hitl_required: bool
) -> AgentRun:
    agent_run = AgentRun(
        claim_id=claim_id,
        agent_type=AgentType(agent_type),
        input_payload=input_payload,
        output_payload=output_payload,
        confidence=confidence,
        hitl_required=hitl_required
    )
    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)
    return agent_run


async def review_agent_run(
    db: AsyncSession,
    run_id: int,
    decision: ReviewDecision,
    edited_output: dict = None,
    reviewer: str = None,
    reviewer_notes: str = None
) -> AgentRun:
    result = await db.execute(select(AgentRun).where(AgentRun.run_id == run_id))
    agent_run = result.scalar_one_or_none()
    if not agent_run:
        raise ValueError(f"Agent run {run_id} not found")

    agent_run.review_decision = decision
    agent_run.reviewed_by = reviewer

    if decision == ReviewDecision.edited and edited_output:
        agent_run.output_payload = edited_output

    await db.commit()
    await db.refresh(agent_run)
    return agent_run


async def get_agent_runs_for_claim(
    db: AsyncSession,
    claim_id: int
) -> list[AgentRun]:
    result = await db.execute(
        select(AgentRun).where(AgentRun.claim_id == claim_id).order_by(AgentRun.created_at.desc())
    )
    return result.scalars().all()


async def get_pending_reviews(
    db: AsyncSession,
    agent_type: str = None
) -> list[AgentRun]:
    query = select(AgentRun).where(
        AgentRun.hitl_required == True,
        AgentRun.review_decision.is_(None)
    )
    if agent_type:
        query = query.where(AgentRun.agent_type == AgentType(agent_type))

    query = query.order_by(AgentRun.created_at)
    result = await db.execute(query)
    return result.scalars().all()