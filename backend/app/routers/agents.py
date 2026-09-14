from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models import Claim as ClaimModel, AgentRun as AgentRunModel, AgentType, ReviewDecision
from app.schemas import (
    CodingAssistRequest, CodingAssistResponse,
    DenialPredictRequest, DenialPredictResponse,
    AppealDraftRequest, AppealDraftResponse,
    AgentReviewRequest, AgentRun as AgentRunSchema
)
from app.services.coding_agent import suggest_codes
from app.services.denial_predictor import get_denial_prediction
from app.services.appeal_agent import draft_appeal_letter
from app.services.agent_logger import log_agent_run, review_agent_run, get_pending_reviews

router = APIRouter()


@router.post("/coding-assist", response_model=CodingAssistResponse)
async def coding_assist(
    request: CodingAssistRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await suggest_codes(request.clinical_notes, request.patient_context)

    agent_run = await log_agent_run(
        db=db,
        claim_id=request.patient_context.get("claim_id", 0) if request.patient_context else 0,
        agent_type="coding_assist",
        input_payload={"clinical_notes": request.clinical_notes, "patient_context": request.patient_context},
        output_payload=result,
        confidence=Decimal(str(result.get("overall_confidence", 0.5))),
        hitl_required=result.get("hitl_required", True)
    )

    return CodingAssistResponse(
        icd10_suggestions=result.get("icd10_suggestions", []),
        cpt_suggestions=result.get("cpt_suggestions", []),
        confidence=Decimal(str(result.get("overall_confidence", 0.5))),
        hitl_required=result.get("hitl_required", True)
    )


@router.post("/denial-predict", response_model=DenialPredictResponse)
async def denial_predict(
    request: DenialPredictRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    probability, shap_explanation, risk_factors, hitl_required = await get_denial_prediction(db, request.claim_id)

    result = await db.execute(select(ClaimModel).where(ClaimModel.claim_id == request.claim_id))
    claim = result.scalar_one_or_none()
    if claim:
        claim.denial_predicted = True
        claim.denial_probability = probability
        await db.commit()

    await log_agent_run(
        db=db,
        claim_id=request.claim_id,
        agent_type="denial_classifier",
        input_payload={"claim_id": request.claim_id},
        output_payload={
            "denial_probability": float(probability),
            "shap_explanation": shap_explanation,
            "risk_factors": risk_factors
        },
        confidence=probability,
        hitl_required=hitl_required
    )

    return DenialPredictResponse(
        denial_probability=probability,
        shap_explanation=shap_explanation,
        risk_factors=risk_factors,
        hitl_required=hitl_required
    )


@router.post("/review")
async def review_agent_output(
    request: AgentReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    await review_agent_run(
        db=db,
        run_id=request.run_id,
        decision=request.decision,
        edited_output=request.edited_output,
        reviewer=current_user.name,
        reviewer_notes=request.reviewer_notes
    )
    return {"message": "Review submitted", "run_id": request.run_id, "decision": request.decision.value}


@router.get("/pending-reviews")
async def get_pending_reviews_endpoint(
    agent_type: str = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    runs = await get_pending_reviews(db, agent_type)
    return [
        {
            "run_id": r.run_id,
            "claim_id": r.claim_id,
            "agent_type": r.agent_type.value,
            "input_payload": r.input_payload,
            "output_payload": r.output_payload,
            "confidence": float(r.confidence),
            "created_at": r.created_at.isoformat()
        }
        for r in runs
    ]


@router.get("/runs/{claim_id}")
async def get_agent_runs_for_claim(
    claim_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    from app.services.agent_logger import get_agent_runs_for_claim as get_runs
    runs = await get_runs(db, claim_id)
    return [
        {
            "run_id": r.run_id,
            "agent_type": r.agent_type.value,
            "input_payload": r.input_payload,
            "output_payload": r.output_payload,
            "confidence": float(r.confidence),
            "hitl_required": r.hitl_required,
            "review_decision": r.review_decision.value if r.review_decision else None,
            "reviewed_by": r.reviewed_by,
            "created_at": r.created_at.isoformat()
        }
        for r in runs
    ]