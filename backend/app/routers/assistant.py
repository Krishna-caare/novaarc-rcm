from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models import Claim, ClaimStatus, Denial, Payment, Payer, Provider
from app.schemas import AssistantQueryRequest, AssistantQueryResponse

router = APIRouter()


INTENT_PATTERNS = {
    "ar_over_90": [
        "ar over 90", "ar > 90", "accounts receivable over 90", "aging over 90",
        "90 day aging", "over 90 days"
    ],
    "denial_rate": [
        "denial rate", "denial percentage", "denials", "denial ratio"
    ],
    "top_denial_codes": [
        "top denial codes", "top denials", "most common denials", "denial codes"
    ],
    "payer_comparison": [
        "payer comparison", "compare payers", "payer performance", "best payer", "worst payer"
    ],
    "collection_rate": [
        "collection rate", "collection percentage", "collections"
    ],
    "total_ar": [
        "total ar", "total accounts receivable", "outstanding ar", "ar balance"
    ],
    "claims_by_status": [
        "claims by status", "claim status", "status breakdown"
    ]
}


def match_intent(query: str) -> str:
    query_lower = query.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if pattern in query_lower:
                return intent
    return "unknown"


@router.post("/query", response_model=AssistantQueryResponse)
async def assistant_query(
    request: AssistantQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    intent = match_intent(request.query)

    if intent == "ar_over_90":
        return await handle_ar_over_90(db)
    elif intent == "denial_rate":
        return await handle_denial_rate(db)
    elif intent == "top_denial_codes":
        return await handle_top_denial_codes(db)
    elif intent == "payer_comparison":
        return await handle_payer_comparison(db)
    elif intent == "collection_rate":
        return await handle_collection_rate(db)
    elif intent == "total_ar":
        return await handle_total_ar(db)
    elif intent == "claims_by_status":
        return await handle_claims_by_status(db)
    else:
        return AssistantQueryResponse(
            intent="unknown",
            response="I can help you with queries about AR aging, denial rates, top denial codes, payer comparison, collection rates, total AR, and claims by status. Try asking: 'What's our AR over 90 days?' or 'Show me top denial codes'",
            follow_up_suggestions=[
                "What's our AR over 90 days?",
                "Show me top denial codes",
                "What's the denial rate by payer?",
                "Show me collection rate"
            ]
        )


async def handle_ar_over_90(db: AsyncSession) -> AssistantQueryResponse:
    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=90)

    result = await db.execute(
        select(
            func.sum(Claim.charge_amount - Claim.paid_amount).label("ar_90"),
            func.count(Claim.claim_id).label("count")
        )
        .where(
            Claim.status.in_([ClaimStatus.submitted, ClaimStatus.acknowledged, ClaimStatus.in_process, ClaimStatus.denied]),
            Claim.date_of_service <= cutoff
        )
    )
    row = result.first()

    ar_90 = float(row.ar_90 or 0)
    count = row.count or 0

    total_ar_result = await db.execute(
        select(func.sum(Claim.charge_amount - Claim.paid_amount))
        .where(Claim.status.in_([ClaimStatus.submitted, ClaimStatus.acknowledged, ClaimStatus.in_process, ClaimStatus.denied]))
    )
    total_ar = float(total_ar_result.scalar() or 0)

    pct = (ar_90 / total_ar * 100) if total_ar > 0 else 0

    return AssistantQueryResponse(
        intent="ar_over_90",
        response=f"AR over 90 days: ${ar_90:,.2f} ({count} claims, {pct:.1f}% of total AR)",
        data={"ar_over_90": ar_90, "claim_count": count, "percentage_of_total": pct, "total_ar": total_ar},
        follow_up_suggestions=[
            "Show me AR aging by payer",
            "Which claims are over 90 days?",
            "What's our total AR?"
        ]
    )


async def handle_denial_rate(db: AsyncSession) -> AssistantQueryResponse:
    total_claims = await db.execute(select(func.count(Claim.claim_id)))
    denied_claims = await db.execute(
        select(func.count(Claim.claim_id)).where(Claim.status == ClaimStatus.denied)
    )

    total = total_claims.scalar() or 0
    denied = denied_claims.scalar() or 0
    rate = (denied / total * 100) if total > 0 else 0

    return AssistantQueryResponse(
        intent="denial_rate",
        response=f"Overall denial rate: {rate:.1f}% ({denied} denied out of {total} total claims)",
        data={"denial_rate": rate, "denied_claims": denied, "total_claims": total},
        follow_up_suggestions=[
            "Show denial rate by payer",
            "Show top denial codes",
            "What's our appeal win rate?"
        ]
    )


async def handle_top_denial_codes(db: AsyncSession) -> AssistantQueryResponse:
    result = await db.execute(
        select(
            Denial.denial_code,
            func.count(Denial.denial_id).label("count"),
            func.sum(Denial.denied_amount).label("total_denied")
        )
        .where(Denial.denial_code.isnot(None))
        .group_by(Denial.denial_code)
        .order_by(func.count(Denial.denial_id).desc())
        .limit(10)
    )

    codes = [
        {"code": row.denial_code, "count": row.count, "total_denied": float(row.total_denied or 0)}
        for row in result.all()
    ]

    response_lines = ["Top Denial Codes:"]
    for c in codes:
        response_lines.append(f"  {c['code']}: {c['count']} denials (${c['total_denied']:,.2f})")

    return AssistantQueryResponse(
        intent="top_denial_codes",
        response="\n".join(response_lines),
        data={"top_codes": codes},
        follow_up_suggestions=[
            "Show denial trend over time",
            "Show denials by root cause",
            "Which payer has most denials?"
        ]
    )


async def handle_payer_comparison(db: AsyncSession) -> AssistantQueryResponse:
    result = await db.execute(
        select(
            Payer.name,
            func.sum(Claim.charge_amount).label("charged"),
            func.sum(Claim.paid_amount).label("paid"),
            func.count(Claim.claim_id).label("claims"),
            func.sum(func.case((Claim.status == ClaimStatus.denied, 1), else_=0)).label("denials")
        )
        .join(Claim, Payer.payer_id == Claim.payer_id)
        .group_by(Payer.name)
        .order_by(func.sum(Claim.charge_amount).desc())
    )

    payers = []
    for row in result.all():
        charged = float(row.charged or 0)
        paid = float(row.paid or 0)
        denial_rate = float((row.denials or 0) / (row.claims or 1)) * 100
        payers.append({
            "payer": row.name,
            "charged": charged,
            "paid": paid,
            "collection_rate": (paid / charged * 100) if charged > 0 else 0,
            "denial_rate": denial_rate,
            "claims": row.claims
        })

    response_lines = ["Payer Performance:"]
    for p in payers[:5]:
        response_lines.append(f"  {p['payer']}: ${p['charged']:,.0f} charged, {p['collection_rate']:.1f}% collected, {p['denial_rate']:.1f}% denied")

    return AssistantQueryResponse(
        intent="payer_comparison",
        response="\n".join(response_lines),
        data={"payers": payers},
        follow_up_suggestions=[
            "Show me the worst performing payer",
            "Compare payer denial rates",
            "Show payer aging"
        ]
    )


async def handle_collection_rate(db: AsyncSession) -> AssistantQueryResponse:
    total_charges = await db.execute(select(func.sum(Claim.charge_amount)))
    total_paid = await db.execute(select(func.sum(Claim.paid_amount)))

    charged = float(total_charges.scalar() or 0)
    paid = float(total_paid.scalar() or 0)
    rate = (paid / charged * 100) if charged > 0 else 0

    return AssistantQueryResponse(
        intent="collection_rate",
        response=f"Collection rate: {rate:.1f}% (${paid:,.2f} collected of ${charged:,.2f} charged)",
        data={"collection_rate": rate, "collected": paid, "charged": charged},
        follow_up_suggestions=[
            "Show collection rate by payer",
            "Show collection trend over time",
            "What's our AR over 90 days?"
        ]
    )


async def handle_total_ar(db: AsyncSession) -> AssistantQueryResponse:
    result = await db.execute(
        select(func.sum(Claim.charge_amount - Claim.paid_amount))
        .where(Claim.status.in_([ClaimStatus.submitted, ClaimStatus.acknowledged, ClaimStatus.in_process, ClaimStatus.denied]))
    )
    total_ar = float(result.scalar() or 0)

    return AssistantQueryResponse(
        intent="total_ar",
        response=f"Total outstanding AR: ${total_ar:,.2f}",
        data={"total_ar": total_ar},
        follow_up_suggestions=[
            "Show AR aging buckets",
            "Show AR by payer",
            "What's our AR over 90 days?"
        ]
    )


async def handle_claims_by_status(db: AsyncSession) -> AssistantQueryResponse:
    result = await db.execute(
        select(Claim.status, func.count(Claim.claim_id), func.sum(Claim.charge_amount))
        .group_by(Claim.status)
    )

    statuses = [
        {"status": row[0].value, "count": row[1], "total_charges": float(row[2] or 0)}
        for row in result.all()
    ]

    response_lines = ["Claims by Status:"]
    for s in statuses:
        response_lines.append(f"  {s['status']}: {s['count']} claims (${s['total_charges']:,.2f})")

    return AssistantQueryResponse(
        intent="claims_by_status",
        response="\n".join(response_lines),
        data={"by_status": statuses},
        follow_up_suggestions=[
            "Show claims submitted this month",
            "Show denied claims needing appeal",
            "What's our submission rate?"
        ]
    )