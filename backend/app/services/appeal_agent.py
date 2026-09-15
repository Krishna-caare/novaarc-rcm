import os
import json
import httpx
from typing import Optional
from decimal import Decimal
from app.models import Denial, Claim
from app.core.config import settings


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "nvidia/nemotron-3.5-lightning:free"


APPEAL_DRAFT_PROMPT = """You are a healthcare revenue cycle specialist writing appeal letters for denied claims.

Write a professional, persuasive appeal letter that includes:
1. Clear identification of the claim and denial
2. Specific rebuttal of the denial reason with clinical evidence
3. Citations of relevant policies (LCD/NCD, payer policies, coding guidelines)
4. Request for specific action (reconsideration, peer-to-peer, etc.)
5. Professional tone throughout

Return JSON only with this structure:
{
  "appeal_letter": "Full formatted appeal letter text...",
  "key_arguments": ["argument 1", "argument 2"],
  "supporting_citations": ["citation 1", "citation 2"],
  "recommended_action": "peer_to_peer | reconsideration | external_review",
  "confidence": 0.85
}"""


async def call_openrouter(messages: list[dict], temperature: float = 0.4) -> dict:
    if not OPENROUTER_API_KEY:
        return {"error": "OpenRouter API key not configured"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://novaarc.local",
                    "X-Title": "NovaArc RCM"
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                    "reasoning": {"enabled": True}
                }
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as e:
        return {"error": str(e)}


async def draft_appeal_letter(denial: Denial, additional_context: str = None) -> tuple[str, Decimal, bool]:
    claim = denial.claim
    patient = claim.patient
    provider = claim.provider
    payer = claim.payer

    context = f"""
Claim ID: {claim.claim_id}
Patient: {patient.mrn} (DOB: {patient.dob})
Provider: {provider.name} (NPI: {provider.npi}, Specialty: {provider.specialty})
Payer: {payer.name}
Date of Service: {claim.date_of_service}
Charge Amount: ${claim.charge_amount}
CPT Codes: {', '.join(claim.cpt_codes or [])}
ICD-10 Codes: {', '.join(claim.icd10_codes or [])}
Modifiers: {', '.join(claim.modifiers or [])}

Denial Code: {denial.denial_code}
Denial Description: {denial.description}
Denied Amount: ${denial.denied_amount}
Denial Date: {denial.denial_date}
Root Cause: {denial.root_cause}
"""

    if additional_context:
        context += f"\nAdditional Context: {additional_context}"

    messages = [
        {"role": "system", "content": APPEAL_DRAFT_PROMPT},
        {"role": "user", "content": context}
    ]

    result = await call_openrouter(messages)

    if "error" in result:
        fallback_letter = generate_fallback_appeal(denial, claim, patient, provider, payer)
        return fallback_letter, Decimal("0.3"), True

    appeal_letter = result.get("appeal_letter", "")
    confidence = Decimal(str(result.get("confidence", 0.5)))
    hitl_required = confidence < 0.75

    return appeal_letter, confidence, hitl_required


def generate_fallback_appeal(denial: Denial, claim: Claim, patient, provider, payer) -> str:
    return f"""
APPEAL LETTER - CLAIM {claim.claim_id}

Date: {claim.date_of_service}
Patient: {patient.mrn}
Provider: {provider.name} (NPI: {provider.npi})
Payer: {payer.name}

RE: Appeal of Denial for Claim {claim.claim_id}
Denial Code: {denial.denial_code}
Denied Amount: ${denial.denied_amount}

Dear {payer.name} Appeals Department,

We are writing to formally appeal the denial of the above-referenced claim. The claim was denied with code {denial.denial_code} ({denial.description}) on {denial.denial_date}.

CLINICAL JUSTIFICATION:
The services rendered on {claim.date_of_service} were medically necessary and appropriately coded. The diagnosis codes {', '.join(claim.icd10_codes or [])} support the procedures {', '.join(claim.cpt_codes or [])} performed.

DENIAL REBUTTAL:
{denial.root_cause or 'The denial reason does not align with the clinical documentation and coding guidelines.'}

REQUEST:
We respectfully request reconsideration of this denial and payment of the denied amount of ${denial.denied_amount}. We are available for a peer-to-peer review at your convenience.

Supporting documentation is attached.

Sincerely,
{provider.name}
{provider.specialty}
""".strip()