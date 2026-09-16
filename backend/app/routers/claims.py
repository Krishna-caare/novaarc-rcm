from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date, datetime

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models import Claim as ClaimModel, ClaimStatus, Patient, Provider, Payer, Denial, Payment, AgentRun, AppealStatus
from app.schemas import (
    ClaimCreate, ClaimUpdate, Claim as ClaimSchema, ClaimDetail,
    ClaimSubmitRequest
)
from app.services.edi_parser import generate_837_claim
from app.services.work_queue import assign_claim_to_queue

router = APIRouter()


@router.get("/stats/summary")
async def claims_summary(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    total_res = await db.execute(select(func.count(ClaimModel.claim_id)))
    by_status = await db.execute(
        select(ClaimModel.status, func.count(ClaimModel.claim_id), func.sum(ClaimModel.charge_amount))
        .group_by(ClaimModel.status)
    )
    total_charges_res = await db.execute(select(func.sum(ClaimModel.charge_amount)))
    total_paid_res = await db.execute(select(func.sum(ClaimModel.paid_amount)))

    total_val = total_res.scalar() or 0
    total_charges_val = total_charges_res.scalar() or 0
    total_paid_val = total_paid_res.scalar() or 0

    return {
        "total_claims": total_val,
        "by_status": [
            {"status": s.value, "count": c, "total_charges": float(a or 0)}
            for s, c, a in by_status.all()
        ],
        "total_charges": float(total_charges_val),
        "total_paid": float(total_paid_val),
        "collection_rate": float((total_paid_val or 0) / (total_charges_val or 1)) * 100
    }


@router.get("", response_model=list[ClaimSchema])
async def list_claims(
    status: Optional[ClaimStatus] = None,
    payer_id: Optional[int] = None,
    provider_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = select(ClaimModel).options(
        selectinload(ClaimModel.patient),
        selectinload(ClaimModel.provider),
        selectinload(ClaimModel.payer)
    )

    if status:
        query = query.where(ClaimModel.status == status)
    if payer_id:
        query = query.where(ClaimModel.payer_id == payer_id)
    if provider_id:
        query = query.where(ClaimModel.provider_id == provider_id)
    if patient_id:
        query = query.where(ClaimModel.patient_id == patient_id)
    if date_from:
        query = query.where(ClaimModel.date_of_service >= date_from)
    if date_to:
        query = query.where(ClaimModel.date_of_service <= date_to)

    query = query.order_by(ClaimModel.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/reference-data")
async def get_reference_data(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    patients_res = await db.execute(select(Patient).order_by(Patient.patient_id).limit(100))
    providers_res = await db.execute(select(Provider).order_by(Provider.name).limit(100))
    payers_res = await db.execute(select(Payer).order_by(Payer.name).limit(100))
    return {
        "patients": [{"patient_id": p.patient_id, "mrn": p.mrn, "payer_id": p.payer_id} for p in patients_res.scalars().all()],
        "providers": [{"provider_id": pr.provider_id, "name": pr.name, "specialty": pr.specialty} for pr in providers_res.scalars().all()],
        "payers": [{"payer_id": py.payer_id, "name": py.name} for py in payers_res.scalars().all()]
    }


@router.get("/{claim_id}", response_model=ClaimDetail)
async def get_claim(
    claim_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = select(ClaimModel).options(
        selectinload(ClaimModel.patient),
        selectinload(ClaimModel.provider),
        selectinload(ClaimModel.payer),
        selectinload(ClaimModel.denials),
        selectinload(ClaimModel.payments),
        selectinload(ClaimModel.agent_runs)
    ).where(ClaimModel.claim_id == claim_id)

    result = await db.execute(query)
    claim = result.scalar_one_or_none()

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return claim


@router.post("", response_model=ClaimSchema, status_code=201)
async def create_claim(
    claim_data: ClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    claim = ClaimModel(**claim_data.model_dump())
    db.add(claim)
    await db.commit()
    await db.refresh(claim)

    await assign_claim_to_queue(db, claim.claim_id)

    # Reload with relationships for full response serialization
    res = await db.execute(
        select(ClaimModel).options(
            selectinload(ClaimModel.patient),
            selectinload(ClaimModel.provider),
            selectinload(ClaimModel.payer)
        ).where(ClaimModel.claim_id == claim.claim_id)
    )
    return res.scalar_one()


@router.patch("/{claim_id}", response_model=ClaimSchema)
async def update_claim(
    claim_id: int,
    claim_data: ClaimUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(select(ClaimModel).where(ClaimModel.claim_id == claim_id))
    claim = result.scalar_one_or_none()

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    update_data = claim_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value is not None:
            if isinstance(value, str):
                try:
                    value = ClaimStatus(value)
                except ValueError:
                    pass
        setattr(claim, field, value)

    if claim.status == ClaimStatus.paid:
        if claim.paid_amount is None or claim.paid_amount == 0:
            claim.paid_amount = claim.charge_amount
        # Check if a Payment record exists, if not create one so it appears in Payments page
        pay_check = await db.execute(select(Payment).where(Payment.claim_id == claim_id))
        if not pay_check.scalar_one_or_none():
            db.add(Payment(
                claim_id=claim_id,
                amount=claim.paid_amount or claim.charge_amount,
                posted_date=date.today(),
                remittance_ref=f"ERA-{claim_id}-{int(datetime.utcnow().timestamp())}",
                payer_id=claim.payer_id,
            ))

    if claim.status == ClaimStatus.submitted and not claim.submitted_at:
        claim.submitted_at = func.now()
        if not claim.edi_837_ref:
            claim.edi_837_ref = f"EDI837-{claim_id}-{int(datetime.utcnow().timestamp())}"

    # If status is set to denied, ensure a Denial record exists so it shows in Denials page and queue
    if claim.status == ClaimStatus.denied:
        denial_check = await db.execute(select(Denial).where(Denial.claim_id == claim_id))
        existing_denial = denial_check.scalar_one_or_none()
        if not existing_denial:
            new_denial = Denial(
                claim_id=claim_id,
                denial_code="CO-16",
                description="Claim/service lacks information or has submission/billing error(s)",
                denied_amount=claim.charge_amount,
                denial_date=date.today(),
                root_cause="Missing Information / Billing Error",
                appeal_status=AppealStatus.not_started,
                appeal_drafted_by_ai=False,
            )
            db.add(new_denial)

    await db.commit()

    if claim.status == ClaimStatus.denied:
        try:
            await assign_claim_to_queue(db, claim_id)
        except Exception:
            pass

    # Reload with relationships for full response serialization
    res = await db.execute(
        select(ClaimModel).options(
            selectinload(ClaimModel.patient),
            selectinload(ClaimModel.provider),
            selectinload(ClaimModel.payer)
        ).where(ClaimModel.claim_id == claim_id)
    )
    return res.scalar_one()


@router.post("/{claim_id}/submit", response_model=ClaimSchema)
async def submit_claim(
    claim_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(
        select(ClaimModel).options(
            selectinload(ClaimModel.patient),
            selectinload(ClaimModel.provider),
            selectinload(ClaimModel.payer)
        ).where(ClaimModel.claim_id == claim_id)
    )
    claim = result.scalar_one_or_none()

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.status != ClaimStatus.created:
        status_val = claim.status.value if hasattr(claim.status, 'value') else claim.status
        raise HTTPException(status_code=400, detail=f"Claim cannot be submitted from status: {status_val}")

    try:
        edi_content = generate_837_claim(claim)
    except Exception:
        edi_content = ""

    created_ts = int(claim.created_at.timestamp()) if (claim.created_at and hasattr(claim.created_at, 'timestamp')) else int(datetime.utcnow().timestamp())
    edi_ref = f"EDI837-{claim_id}-{created_ts}"

    claim.status = ClaimStatus.submitted
    claim.submitted_at = func.now()
    claim.edi_837_ref = edi_ref

    await db.commit()

    try:
        await assign_claim_to_queue(db, claim.claim_id)
    except Exception:
        pass

    res = await db.execute(
        select(ClaimModel).options(
            selectinload(ClaimModel.patient),
            selectinload(ClaimModel.provider),
            selectinload(ClaimModel.payer)
        ).where(ClaimModel.claim_id == claim_id)
    )
    return res.scalar_one()