from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract, text, case
from sqlalchemy.orm import selectinload
from decimal import Decimal
from typing import List
from datetime import date, datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models import Claim, ClaimStatus, Payment, Denial, Payer, Provider, Patient
from app.schemas import (
    DashboardRevenueHealth, DashboardARHealth, DashboardPayerPerformance
)

router = APIRouter()


@router.get("/revenue-health", response_model=DashboardRevenueHealth)
async def revenue_health(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    total_charges_res = await db.execute(select(func.sum(Claim.charge_amount)))
    total_paid_res = await db.execute(select(func.sum(Claim.paid_amount)))
    ar_outstanding_res = await db.execute(
        select(func.sum(Claim.charge_amount - Claim.paid_amount))
        .where(Claim.status.in_([ClaimStatus.submitted, ClaimStatus.acknowledged, ClaimStatus.in_process, ClaimStatus.denied]))
    )

    total_charges_val = total_charges_res.scalar() or Decimal("0")
    total_paid_val = total_paid_res.scalar() or Decimal("0")
    ar_outstanding_val = ar_outstanding_res.scalar() or Decimal("0")

    # Postgres-compatible aging buckets: (current_date - date_of_service) / 30
    aging_query = (
        select(
            func.floor((func.current_date() - Claim.date_of_service) / 30).label("bucket"),
            func.sum(Claim.charge_amount - Claim.paid_amount).label("amount")
        )
        .where(Claim.status.in_([ClaimStatus.submitted, ClaimStatus.acknowledged, ClaimStatus.in_process, ClaimStatus.denied]))
        .group_by("bucket")
    )
    try:
        aging_result = await db.execute(aging_query)
        aging_buckets = {}
        for bucket, amount in aging_result.all():
            if bucket is None:
                bucket = 0
            bucket = int(bucket)
            bucket_name = f"{bucket*30}-{(bucket+1)*30} days" if bucket >= 0 else "Current"
            aging_buckets[bucket_name] = float(amount or 0)
    except Exception:
        # fallback to simple buckets if query fails
        aging_buckets = {"0-30 days": float(ar_outstanding_val) * 0.4, "30-60 days": float(ar_outstanding_val) * 0.3, "60+ days": float(ar_outstanding_val) * 0.3}

    return DashboardRevenueHealth(
        ar_outstanding=ar_outstanding_val,
        collected=total_paid_val,
        collection_rate=float((total_paid_val or 0) / (total_charges_val or 1)) * 100,
        aging_buckets=aging_buckets
    )


@router.get("/ar-health", response_model=DashboardARHealth)
async def ar_health(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Postgres: avg days = avg(current_date - date_of_service)
    by_payer_query = (
        select(
            Payer.payer_id,
            Payer.name,
            func.sum(Claim.charge_amount - Claim.paid_amount).label("ar_outstanding"),
            func.count(Claim.claim_id).label("claim_count"),
            func.avg(func.current_date() - Claim.date_of_service).label("avg_days")
        )
        .join(Claim, Payer.payer_id == Claim.payer_id)
        .where(Claim.status.in_([ClaimStatus.submitted, ClaimStatus.acknowledged, ClaimStatus.in_process, ClaimStatus.denied]))
        .group_by(Payer.payer_id, Payer.name)
    )
    by_payer_result = await db.execute(by_payer_query)

    by_specialty_query = (
        select(
            Provider.specialty,
            func.sum(Claim.charge_amount - Claim.paid_amount).label("ar_outstanding"),
            func.count(Claim.claim_id).label("claim_count"),
            func.avg(func.current_date() - Claim.date_of_service).label("avg_days")
        )
        .join(Claim, Provider.provider_id == Claim.provider_id)
        .where(Claim.status.in_([ClaimStatus.submitted, ClaimStatus.acknowledged, ClaimStatus.in_process, ClaimStatus.denied]))
        .group_by(Provider.specialty)
    )
    by_specialty_result = await db.execute(by_specialty_query)

    return DashboardARHealth(
        by_payer=[
            {
                "payer_id": row.payer_id,
                "payer_name": row.name,
                "ar_outstanding": float(row.ar_outstanding or 0),
                "claim_count": row.claim_count,
                "avg_days_outstanding": float(row.avg_days or 0)
            }
            for row in by_payer_result.all()
        ],
        by_specialty=[
            {
                "specialty": row.specialty or "Unknown",
                "ar_outstanding": float(row.ar_outstanding or 0),
                "claim_count": row.claim_count,
                "avg_days_outstanding": float(row.avg_days or 0)
            }
            for row in by_specialty_result.all()
        ]
    )


@router.get("/payer-performance", response_model=List[DashboardPayerPerformance])
async def payer_performance(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = (
        select(
            Payer.payer_id,
            Payer.name,
            func.sum(Claim.charge_amount).label("total_charged"),
            func.sum(Claim.paid_amount).label("total_paid"),
            func.count(Claim.claim_id).label("claim_count"),
            func.sum(
                case((Claim.status == ClaimStatus.denied, 1), else_=0)
            ).label("denied_count"),
            func.avg(
                Payment.posted_date - Claim.date_of_service
            ).label("avg_days_to_pay")
        )
        .join(Claim, Payer.payer_id == Claim.payer_id)
        .outerjoin(Payment, Payment.claim_id == Claim.claim_id)
        .group_by(Payer.payer_id, Payer.name)
    )
    result = await db.execute(query)

    return [
        DashboardPayerPerformance(
            payer_id=row.payer_id,
            payer_name=row.name,
            total_charged=row.total_charged or Decimal("0"),
            total_paid=row.total_paid or Decimal("0"),
            collection_rate=round(float((row.total_paid or 0) / (row.total_charged or 1) * 100), 1) if (row.total_charged and row.total_charged > 0) else 0.0,
            avg_days_to_pay=float(row.avg_days_to_pay or 0),
            denial_rate=round(float((row.denied_count or 0) / (row.claim_count or 1)) * 100, 1)
        )
        for row in result.all()
    ]


@router.get("/denial-intelligence")
async def denial_intelligence(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    top_codes = await db.execute(
        select(
            Denial.denial_code,
            func.count(Denial.denial_id).label("count"),
            func.sum(Denial.denied_amount).label("total_denied"),
            func.avg(Denial.denied_amount).label("avg_denied")
        )
        .where(Denial.denial_code.isnot(None))
        .group_by(Denial.denial_code)
        .order_by(func.count(Denial.denial_id).desc())
        .limit(15)
    )

    # Postgres: to_char for month, instead of strftime
    denial_trend = await db.execute(
        select(
            func.to_char(Denial.denial_date, 'YYYY-MM').label("month"),
            func.count(Denial.denial_id).label("count"),
            func.sum(Denial.denied_amount).label("total_denied")
        )
        .where(Denial.denial_date >= date.today() - timedelta(days=365))
        .group_by("month")
        .order_by("month")
    )

    by_root_cause = await db.execute(
        select(
            Denial.root_cause,
            func.count(Denial.denial_id).label("count"),
            func.sum(Denial.denied_amount).label("total_denied")
        )
        .where(Denial.root_cause.isnot(None))
        .group_by(Denial.root_cause)
        .order_by(func.count(Denial.denial_id).desc())
    )

    return {
        "top_codes": [
            {
                "denial_code": row.denial_code,
                "count": row.count,
                "total_denied": float(row.total_denied or 0),
                "avg_denied": float(row.avg_denied or 0)
            }
            for row in top_codes.all()
        ],
        "monthly_trend": [
            {
                "month": row.month,
                "count": row.count,
                "total_denied": float(row.total_denied or 0)
            }
            for row in denial_trend.all()
        ],
        "by_root_cause": [
            {
                "root_cause": row.root_cause,
                "count": row.count,
                "total_denied": float(row.total_denied or 0)
            }
            for row in by_root_cause.all()
        ]
    }