import os
import json
import httpx
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal

from app.knowledge_graph.graph_engine import denial_kg
from app.services.vector_engine import denial_vector_engine
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


def match_best_scenario(scenarios: List[Dict[str, Any]], claim_context: Dict[str, Any]) -> Tuple[Dict[str, Any], float, str]:
    """
    Hybrid Vector + Clinical Heuristic Scenario Matching:
    1. Runs semantic vector cosine similarity across scenario vector space.
    2. Blends semantic similarity with hard healthcare rules (CPT surgery vs E/M ranges).
    3. Returns (best_scenario, confidence_score, vector_model).
    """
    if not scenarios:
        return {}, 0.50, denial_vector_engine.encoder_type

    if len(scenarios) == 1:
        return scenarios[0], 0.95, denial_vector_engine.encoder_type

    # 1. Run Dense Semantic Vector Search
    query_parts = [
        str(claim_context.get("root_cause", "")),
        str(claim_context.get("description", "")),
        str(claim_context.get("clinical_notes", "")),
        " ".join(str(c) for c in claim_context.get("cpt_codes", []))
    ]
    query_text = " ".join(p for p in query_parts if p.strip())

    denial_code = claim_context.get("denial_code", "")
    vector_hits = denial_vector_engine.search(query_text, carc_filter=denial_code, top_k=5)
    vector_scores = {h["scenario_id"]: h["similarity"] for h in vector_hits}

    cpts = [str(c).upper() for c in claim_context.get("cpt_codes", [])]
    root_cause = str(claim_context.get("root_cause", "")).lower()
    description = str(claim_context.get("description", "")).lower()

    # Determine clinical nature of procedures
    has_em = any(c.startswith("992") or c.startswith("993") or c.startswith("994") for c in cpts)
    has_surgery = any(c.startswith(("1", "2", "3", "4", "5", "6")) and len(c) == 5 for c in cpts)
    has_dme = any(c.startswith(("A", "E", "L", "K")) for c in cpts)

    scored = []
    for sc in scenarios:
        sc_id = str(sc.get('id', ''))
        v_sim = vector_scores.get(sc_id, 0.05)

        # Baseline score seeded by semantic vector similarity (scaled 0-50 points)
        score = v_sim * 50.0

        sc_id_lower = sc_id.lower()
        sc_title = str(sc.get('title', '')).lower()
        sc_text = f"{sc_id_lower} {sc_title} {sc.get('root_cause', '')}".lower()

        # Modifier 25 / E&M clinical constraint
        if "mod-25" in sc_id_lower or "modifier 25" in sc_title or "modifier" in sc_text:
            if "modifier" in description or "modifier" in root_cause:
                score += 25
            elif has_em:
                score += 15

        # Surgery / Operative note clinical constraint
        if "op-note" in sc_id_lower or "operative" in sc_text or "surgical" in sc_text:
            if "operative" in description or "operative" in root_cause or "op note" in description:
                score += 25
            elif has_surgery:
                score += 18
            else:
                score -= 15 # Penalize operative notes if NO surgical procedure on claim

        # General chart notes / progress notes
        if "chart" in sc_text or "progress note" in sc_text or "medical record" in sc_text:
            if "medical record" in description or "records" in root_cause:
                score += 20
            elif has_em:
                score += 8

        # Itemized Invoice / DME
        if "invoice" in sc_text:
            if has_dme or "invoice" in root_cause:
                score += 20

        # Prior Auth
        if "on file" in sc_text or "missing from claim" in sc_text:
            if claim_context.get("prior_auth_on_file"):
                score += 15
        if "retro" in sc_text:
            if "retro" in root_cause:
                score += 20

        # Timely filing proof vs write-off
        if "no-proof" in sc_id_lower or "write-off" in sc_text:
            if claim_context.get("initial_submission_date") or "submitted timely" in root_cause or "proof" in root_cause:
                score -= 25 # Strong penalty against write-off if initial submission date or proof is recorded
        elif "proof" in sc_id_lower or "available" in sc_text or "timely" in sc_id_lower:
            if claim_context.get("initial_submission_date") or "submitted timely" in root_cause or "proof" in root_cause:
                score += 35 # Strong boost for proof scenario when submission proof exists

        # COB Patient update
        if "patient" in sc_text and "update" in sc_text:
            if "patient" in description or "member" in description or "update" in root_cause:
                score += 15

        scored.append((score, v_sim, sc))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0]
    # Compute normalized confidence (0.80 to 0.99)
    confidence = round(min(0.99, max(0.80, 0.75 + best[1] * 0.5)), 3)
    return best[2], confidence, denial_vector_engine.encoder_type


async def run_denial_rag(claim_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the Hybrid GraphRAG pipeline:
    1. Traverses the Knowledge Graph for the denial code.
    2. Semantically matches the optimal scenario via Dense Vector + Clinical Rules.
    3. Prompts specialized clinical LLM (or deterministic fallback) with combined context.
    4. Formats and returns resolution playbook, vector confidence, and standard AR call notes.
    """
    denial_code = claim_context.get("denial_code", "CO-16").upper().strip()
    subgraph = denial_kg.get_subgraph(denial_code)

    if not subgraph or not subgraph.scenarios:
        # Fallback to general missing info if code unknown
        subgraph = denial_kg.get_subgraph("CO-16")

    selected_scenario, confidence, vector_model = match_best_scenario(subgraph.scenarios, claim_context)

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
                                llm_result["confidence"] = confidence
                                llm_result["vector_model"] = vector_model
                                llm_result["retrieval_method"] = "hybrid_graph_vector"
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
        "confidence": confidence,
        "vector_model": vector_model,
        "retrieval_method": "hybrid_graph_vector",
        "source": "knowledge_graph_deterministic"
    }
