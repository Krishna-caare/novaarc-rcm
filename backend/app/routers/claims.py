import io
import re
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
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
@router.put("/{claim_id}", response_model=ClaimSchema)
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

    try:
        edi_content = generate_837_claim(claim)
    except Exception:
        edi_content = ""

    try:
        created_ts = int(claim.created_at.timestamp()) if (claim.created_at and hasattr(claim.created_at, 'timestamp')) else int(datetime.utcnow().timestamp())
    except Exception:
        created_ts = int(datetime.utcnow().timestamp())
    edi_ref = f"EDI837-{claim_id}-{created_ts}"

    claim.status = ClaimStatus.submitted
    claim.submitted_at = datetime.utcnow()
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


@router.post("/{claim_id}/adjudicate", response_model=ClaimSchema)
async def adjudicate_claim(
    claim_id: int,
    outcome: Optional[str] = Query(None, description="Force outcome: 'deny' or 'pay'"),
    denial_code: Optional[str] = Query("CO-16", description="Denial code if denied"),
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

    should_deny = False
    if outcome == "deny":
        should_deny = True
    elif outcome == "pay":
        should_deny = False
    else:
        # Automated simulation based on claim characteristics
        should_deny = bool(claim.denial_predicted or (claim.denial_probability and claim.denial_probability > 0.4) or not claim.modifiers)

    if should_deny:
        claim.status = ClaimStatus.denied
        # Check if denial record already exists
        denial_check = await db.execute(select(Denial).where(Denial.claim_id == claim_id))
        existing_denial = denial_check.scalar_one_or_none()
        code_to_use = denial_code or "CO-16"
        desc_map = {
            "CO-16": "Claim/service lacks information or has submission/billing error(s)",
            "CO-216": "Claim appeal/reconsideration reviewed by medical review organization",
            "CO-4": "The procedure code is inconsistent with the modifier used or a required modifier is missing",
            "CO-18": "Exact duplicate claim/service",
            "CO-197": "Precertification/authorization/prior authorization absent",
            "CO-29": "The time limit for filing has expired",
            "CO-22": "This care may be covered by another payer per coordination of benefits",
            "CO-50": "These are non-covered services because this is not deemed a medical necessity"
        }
        if not existing_denial:
            new_denial = Denial(
                claim_id=claim_id,
                denial_code=code_to_use,
                description=desc_map.get(code_to_use, "Claim denied by payer adjudication"),
                denied_amount=claim.charge_amount,
                denial_date=date.today(),
                root_cause=f"{code_to_use}: Payer Remittance Discrepancy",
                appeal_status=AppealStatus.not_started,
                appeal_drafted_by_ai=False,
            )
            db.add(new_denial)
        else:
            existing_denial.denial_code = code_to_use
            existing_denial.description = desc_map.get(code_to_use, existing_denial.description)
    else:
        claim.status = ClaimStatus.paid
        claim.paid_amount = claim.charge_amount
        pay_check = await db.execute(select(Payment).where(Payment.claim_id == claim_id))
        if not pay_check.scalar_one_or_none():
            db.add(Payment(
                claim_id=claim_id,
                amount=claim.charge_amount,
                posted_date=date.today(),
                remittance_ref=f"ERA-835-{claim_id}-{int(datetime.utcnow().timestamp())}",
                payer_id=claim.payer_id,
            ))

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


@router.post("/extract-document")
async def extract_claim_document(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Extract text content from uploaded medical records, encounter notes, or superbill (PDF, TXT, MD).
    Automatically parses clinical notes and runs AI Medical Coding Specialist (Ling 3.0 / heuristics)
    to suggest ICD-10 diagnosis codes, CPT procedure codes, and estimated charges.
    """
    content_type = file.content_type or ""
    filename = file.filename or "document"
    contents = await file.read()

    extracted_text = ""

    # PDF extraction using pypdf
    if filename.lower().endswith(".pdf") or "pdf" in content_type:
        try:
            from pypdf import PdfReader
            pdf_file = io.BytesIO(contents)
            reader = PdfReader(pdf_file)
            pages_text = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    pages_text.append(t.strip())
            extracted_text = "\n\n".join(pages_text)
        except Exception as e:
            try:
                raw = contents.decode("latin-1", errors="ignore")
                matches = re.findall(r"\((.*?)\)\s*Tj", raw)
                if matches:
                    extracted_text = " ".join(matches)
                else:
                    raise e
            except Exception:
                raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(e)}")
    else:
        # Text, Markdown, CSV decode
        try:
            extracted_text = contents.decode("utf-8")
        except UnicodeDecodeError:
            extracted_text = contents.decode("latin-1", errors="ignore")

    extracted_text = extracted_text.strip()
    if not extracted_text:
        raise HTTPException(status_code=400, detail="The uploaded document contains no readable text.")

    # Contextual patient lookup if patient_id provided
    patient_context = {}
    if patient_id and patient_id.isdigit():
        try:
            p_res = await db.execute(select(Patient).where(Patient.patient_id == int(patient_id)))
            patient_rec = p_res.scalar_one_or_none()
            if patient_rec:
                patient_context = {
                    "mrn": patient_rec.mrn,
                    "gender": getattr(patient_rec, "gender", None),
                    "dob": str(getattr(patient_rec, "dob", "")) if getattr(patient_rec, "dob", None) else None
                }
        except Exception:
            pass

    # Call AI Medical Coding Specialist
    from app.services.coding_agent import suggest_codes, generate_fallback_codes
    try:
        coding_result = await suggest_codes(extracted_text, patient_context)
    except Exception:
        coding_result = generate_fallback_codes(extracted_text)

    # Fee schedule estimation
    cpt_fee_schedule = {
        "99213": 145.00,
        "99214": 215.00,
        "99215": 310.00,
        "99203": 185.00,
        "99204": 280.00,
        "99205": 375.00,
        "29881": 1850.00,
        "29880": 2100.00,
        "93000": 85.00,
        "93306": 450.00,
        "80053": 75.00,
        "85025": 50.00,
    }
    suggested_cpts = [c.get("code") for c in coding_result.get("cpt_suggestions", []) if c.get("code")]
    suggested_icds = [d.get("code") for d in coding_result.get("icd10_suggestions", []) if d.get("code")]

    total_charge = sum(cpt_fee_schedule.get(code, 150.0) for code in suggested_cpts) if suggested_cpts else 250.0

    return {
        "filename": filename,
        "extracted_text": extracted_text[:4000],
        "word_count": len(extracted_text.split()),
        "icd10_suggestions": coding_result.get("icd10_suggestions", []),
        "cpt_suggestions": coding_result.get("cpt_suggestions", []),
        "suggested_cpt": ", ".join(suggested_cpts) if suggested_cpts else "99213",
        "suggested_icd10": ", ".join(suggested_icds) if suggested_icds else "I10",
        "suggested_charge": round(total_charge, 2),
        "confidence": float(coding_result.get("overall_confidence", 0.90)),
        "documentation_gaps": coding_result.get("documentation_gaps", []),
    }