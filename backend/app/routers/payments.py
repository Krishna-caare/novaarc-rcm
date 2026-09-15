from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from decimal import Decimal
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models import Payment as PaymentModel, Claim as ClaimModel
from app.schemas import PaymentCreate, PaymentUpdate, Payment as PaymentSchema

router = APIRouter()


@router.get("/stats/summary")
async def payments_summary(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    total = await db.execute(select(func.count(PaymentModel.payment_id)))
    total_amount = await db.execute(select(func.sum(PaymentModel.amount)))
    by_payer = await db.execute(
        select(PaymentModel.payer_id, func.count(PaymentModel.payment_id), func.sum(PaymentModel.amount))
        .group_by(PaymentModel.payer_id)
    )

    return {
        "total_payments": total.scalar() or 0,
        "total_amount": float(total_amount.scalar() or 0),
        "by_payer": [
            {"payer_id": p, "count": c, "total_amount": float(a or 0)}
            for p, c, a in by_payer.all()
        ]
    }


@router.get("", response_model=list[PaymentSchema])
async def list_payments(
    claim_id: Optional[int] = None,
    payer_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = select(PaymentModel).options(
        selectinload(PaymentModel.claim).selectinload(ClaimModel.patient),
        selectinload(PaymentModel.claim).selectinload(ClaimModel.provider),
        selectinload(PaymentModel.payer)
    )

    if claim_id:
        query = query.where(PaymentModel.claim_id == claim_id)
    if payer_id:
        query = query.where(PaymentModel.payer_id == payer_id)
    if date_from:
        query = query.where(PaymentModel.posted_date >= date_from)
    if date_to:
        query = query.where(PaymentModel.posted_date <= date_to)

    query = query.order_by(PaymentModel.posted_date.desc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=PaymentSchema, status_code=201)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(select(ClaimModel).where(ClaimModel.claim_id == payment_data.claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    payment = PaymentModel(**payment_data.model_dump())
    db.add(payment)

    claim.paid_amount += payment_data.amount
    if claim.paid_amount >= claim.charge_amount:
        from app.models import ClaimStatus
        claim.status = ClaimStatus.paid

    await db.commit()

    res = await db.execute(
        select(PaymentModel).options(
            selectinload(PaymentModel.payer),
            selectinload(PaymentModel.claim)
        ).where(PaymentModel.payment_id == payment.payment_id)
    )
    return res.scalar_one()


@router.get("/{payment_id}", response_model=PaymentSchema)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(
        select(PaymentModel).options(
            selectinload(PaymentModel.claim).selectinload(ClaimModel.patient),
            selectinload(PaymentModel.claim).selectinload(ClaimModel.provider),
            selectinload(PaymentModel.payer)
        ).where(PaymentModel.payment_id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.patch("/{payment_id}", response_model=PaymentSchema)
async def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(select(PaymentModel).where(PaymentModel.payment_id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    old_amount = payment.amount
    update_data = payment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)

    if "amount" in update_data and update_data["amount"] != old_amount:
        claim_result = await db.execute(select(ClaimModel).where(ClaimModel.claim_id == payment.claim_id))
        claim = claim_result.scalar_one_or_none()
        if claim:
            claim.paid_amount = claim.paid_amount - old_amount + update_data["amount"]
            if claim.paid_amount >= claim.charge_amount:
                from app.models import ClaimStatus
                claim.status = ClaimStatus.paid

    await db.commit()

    res = await db.execute(
        select(PaymentModel).options(
            selectinload(PaymentModel.payer),
            selectinload(PaymentModel.claim)
        ).where(PaymentModel.payment_id == payment.payment_id)
    )
    return res.scalar_one()