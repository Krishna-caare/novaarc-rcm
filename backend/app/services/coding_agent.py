import os
import json
import httpx
from typing import Optional
from decimal import Decimal
from app.core.config import settings


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "nvidia/nemotron-3.5-lightning:free"


CODING_ASSIST_PROMPT = """You are a certified medical coder assisting with ICD-10-CM and CPT code selection.

Given clinical documentation, suggest the most appropriate:
1. ICD-10-CM diagnosis codes (with specificity)
2. CPT procedure codes (with modifiers if applicable)

Rules:
- Follow official coding guidelines (ICD-10-CM Official Guidelines, CPT Assistant)
- Use highest specificity available
- Include combination codes when appropriate
- Consider medical necessity
- Flag any documentation gaps

Return JSON only with this structure:
{
  "icd10_suggestions": [
    {"code": "X00.0", "description": "...", "confidence": 0.95, "rationale": "..."}
  ],
  "cpt_suggestions": [
    {"code": "99213", "description": "...", "confidence": 0.90, "modifiers": ["25"], "rationale": "..."}
  ],
  "documentation_gaps": ["..."],
  "overall_confidence": 0.92
}"""


async def call_openrouter(messages: list[dict], temperature: float = 0.3) -> dict:
    if not OPENROUTER_API_KEY:
        return {"error": "OpenRouter API key not configured"}

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


async def suggest_codes(clinical_notes: str, patient_context: dict = None) -> dict:
    context = ""
    if patient_context:
        context = f"\nPatient Context: {json.dumps(patient_context)}"

    messages = [
        {"role": "system", "content": CODING_ASSIST_PROMPT},
        {"role": "user", "content": f"Clinical Notes:\n{clinical_notes}{context}"}
    ]

    result = await call_openrouter(messages)

    if "error" in result:
        return {
            "icd10_suggestions": [],
            "cpt_suggestions": [],
            "documentation_gaps": ["AI service unavailable - using fallback"],
            "overall_confidence": 0.0,
            "hitl_required": True
        }

    confidence = result.get("overall_confidence", 0.5)
    hitl_required = confidence < 0.75

    return {
        "icd10_suggestions": result.get("icd10_suggestions", []),
        "cpt_suggestions": result.get("cpt_suggestions", []),
        "documentation_gaps": result.get("documentation_gaps", []),
        "overall_confidence": confidence,
        "hitl_required": hitl_required
    }