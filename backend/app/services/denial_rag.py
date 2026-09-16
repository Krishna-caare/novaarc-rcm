import os
import json
import httpx
from typing import Dict, Any, Optional, List
from decimal import Decimal

from app.knowledge_graph.graph_engine import denial_kg
try:
    from app.core.config import settings
except Exception:
    settings = None

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
PRIMARY_MODEL = os.getenv("CODING_MODEL", "inclusionai/ling-3.0-flash-sante:free")
FALLBACK_MODEL = "nvidia/nemotron-3.5-lightning:free"


RAG_SYNTHESIS_PROMPT = """You are an expert Healthcare Revenue Cycle (RCM) Denial Resolution Specialist.
You have access to the Denial Knowledge Graph showing the exact scenario, investigation checklist, CMS-1500 form fields, payer call script, and resolution playbook.

Using the Claim Context and Knowledge Graph Subgraph provided below, generate an authoritative, professional denial resolution recommendation.

Claim Context:
{claim_context}

Knowledge Graph Subgraph:
{graph_context}

Return pure JSON only with this structure:
{{
  "scenario_id": "string",
  "scenario_title": "string",
  "root_cause_analysis": "string",
  "investigation_checklist": ["step 1", "step 2"],
  "payer_call_script": {{
    "question_1": "string",
    "question_2": "string"
  }},
  "form_requirements": {{
    "form_name": "CMS-1500 / EDI 275",
    "box_number": "Box 24D / Box 23 / etc",
    "required_documents": ["document 1"]
  }},
  "resolution_action_plan": ["step 1", "step 2"],
  "standard_ar_notes": "Formatted AR caller note with claim details",
  "confidence": 0.95
}}"""


def parse_json_safely(text: str) -> dict:
    import re
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


def match_best_scenario(scenarios: List[Dict[str, Any]], claim_context: Dict[str, Any]) -> Dict[str, Any]:
    """Matches the most specific scenario from candidate scenarios based on claim clinical indicators"""
    if not scenarios:
        return {}

    if len(scenarios) == 1:
        return scenarios[0]

    cpts = [str(c).upper() for c in claim_context.get("cpt_codes", [])]
    root_cause = str(claim_context.get("root_cause", "")).lower()
    description = str(claim_context.get("description", "")).lower()
    notes = str(claim_context.get("clinical_notes", "")).lower()

    # Heuristic scoring
    scored = []
    for sc in scenarios:
        score = 0
        sc_text = f"{sc.get('id', '')} {sc.get('title', '')} {sc.get('root_cause', '')}".lower()

        # Modifier 25 / E&M
        if "modifier" in sc_text:
            if "modifier" in description or "modifier" in root_cause:
                score += 12
            elif any(cpt.startswith("992") for cpt in cpts) and len(cpts) > 1:
                score += 6

        # Surgery / Operative
        if any(c in sc_text for c in ["operative", "surgery", "op note"]):
            if "operative" in description or "operative" in root_cause or "op note" in description:
                score += 12
            elif any(cpt.startswith("2") or cpt.startswith("3") or cpt.startswith("4") or cpt.startswith("5") for cpt in cpts) or "surg" in notes:
                score += 5

        # Taxonomy / NPI
        if "taxonomy" in sc_text or "npi" in sc_text:
            if "taxonomy" in root_cause or "npi" in root_cause or "taxonomy" in description or "npi" in description:
                score += 12
            elif "provider" in description:
                score += 5

        # Prior auth on file vs retro
        if "on file" in sc_text or "missing from claim" in sc_text:
            if claim_context.get("prior_auth_on_file"):
                score += 15
        if "retro" in sc_text:
            if "retro" in root_cause or not claim_context.get("prior_auth_on_file"):
                score += 6

        # Timely filing proof
        if "proof" in sc_text or "available" in sc_text:
            if claim_context.get("initial_submission_date") or "submitted timely" in root_cause:
                score += 10

        # COB Patient update
        if "patient" in sc_text and "update" in sc_text:
            if "patient" in description or "member" in description or "update" in root_cause:
                score += 10

        scored.append((score, sc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


async def run_denial_rag(claim_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the Hybrid GraphRAG pipeline:
    1. Traverses the Knowledge Graph for the denial code.
    2. Selects the most accurate scenario subgraph.
    3. Prompts specialized clinical LLM (or deterministic fallback) with combined context.
    4. Formats and returns resolution playbook and standard AR call notes.
    """
    denial_code = claim_context.get("denial_code", "CO-16").upper().strip()
    subgraph = denial_kg.get_subgraph(denial_code)

    if not subgraph or not subgraph.scenarios:
        # Fallback to general missing info if code unknown
        subgraph = denial_kg.get_subgraph("CO-16")

    selected_scenario = match_best_scenario(subgraph.scenarios, claim_context)

    # Pre-populate template variables for AR Notes
    claim_id = claim_context.get("claim_id", "N/A")
    dos = claim_context.get("date_of_service", "N/A")
    denial_date = claim_context.get("denial_date", "N/A")
    payer_name = claim_context.get("payer_name", "Insurance Carrier")

    std_notes = selected_scenario.get("standard_notes", "")
    std_notes = std_notes.replace("[RepName]", "Claims Rep").replace("[CallRef]", f"REF-{claim_id}").replace("[FaxNumber]", "800-555-0199").replace("[TimeLimit]", "60").replace("[DenialDate]", str(denial_date)).replace("[OrigClaimID]", str(claim_id)).replace("[PaidDate]", str(dos)).replace("[CheckNum]", "CHK89214").replace("[AuthNumber]", "AUTH-98231").replace("[TraceID]", f"TRC{claim_id}").replace("[PayerPhone]", "800-555-0100").replace("[PrimaryPayer]", "Primary Insurer").replace("[EffDate]", str(dos)).replace("[DOS]", str(dos)).replace("[TermDate]", str(dos)).replace("[MemberID]", "MEM12345").replace("[CorrectedID]", "ABC12345")

    # Try LLM Synthesis via OpenRouter if key is present
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "") or getattr(settings, "OPENROUTER_API_KEY", "")
    if openrouter_key:
        try:
            prompt = RAG_SYNTHESIS_PROMPT.format(
                claim_context=json.dumps(claim_context, indent=2),
                graph_context=json.dumps({
                    "code": subgraph.code,
                    "category": subgraph.category,
                    "selected_scenario": selected_scenario
                }, indent=2)
            )
            messages = [
                {"role": "system", "content": "You are a senior healthcare RCM appeal and denial resolution director."},
                {"role": "user", "content": prompt}
            ]
            for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.post(
                            f"{OPENROUTER_BASE_URL}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {openrouter_key}",
                                "Content-Type": "application/json",
                                "HTTP-Referer": "https://novaarc.netlify.app",
                                "X-Title": "NovaArc RCM"
                            },
                            json={
                                "model": model,
                                "messages": messages,
                                "temperature": 0.2
                            }
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data["choices"][0]["message"]["content"]
                            llm_result = parse_json_safely(content)
                            if isinstance(llm_result, dict) and "resolution_action_plan" in llm_result:
                                return llm_result
                except Exception:
                    continue
        except Exception as e:
            print(f"OpenRouter synthesis error: {e}")

    # Deterministic Knowledge Graph Fallback
    return {
        "scenario_id": selected_scenario.get("id"),
        "scenario_title": selected_scenario.get("title"),
        "root_cause_analysis": selected_scenario.get("root_cause"),
        "investigation_checklist": selected_scenario.get("investigation_steps", []),
        "payer_call_script": selected_scenario.get("call_script", {}),
        "form_requirements": selected_scenario.get("form_requirements", {}),
        "resolution_action_plan": selected_scenario.get("action_plan", []),
        "standard_ar_notes": std_notes,
        "confidence": 0.95,
        "source": "knowledge_graph_deterministic"
    }
