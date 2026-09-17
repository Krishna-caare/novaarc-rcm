from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import os

from app.knowledge_graph.graph_engine import denial_kg
from app.services.vector_engine import denial_vector_engine

router = APIRouter()


class SemanticSearchRequest(BaseModel):
    query: str
    carc_filter: Optional[str] = None
    top_k: Optional[int] = 5


class SemanticSearchHit(BaseModel):
    scenario_id: str
    code: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    title: str
    root_cause: str
    similarity: float
    encoder_type: str
    investigation_steps: List[str]
    form_requirements: Dict[str, Any]
    action_plan: List[str]
    standard_notes: Optional[str] = None


@router.get("/overview")
async def get_knowledge_graph_overview():
    """Returns top-level metrics, categories, and code distribution of the Denial Knowledge Graph"""
    return denial_kg.get_overview()


@router.get("/subgraph/{code}")
async def get_subgraph_by_code(code: str):
    """Retrieves the connected subgraph and leaf actions for a specific CARC/RARC code (e.g. CO-16)"""
    subgraph = denial_kg.get_subgraph(code)
    if not subgraph:
        raise HTTPException(status_code=404, detail=f"No knowledge subgraph found for code: {code}")
    return subgraph.to_dict()


@router.post("/semantic-search", response_model=List[SemanticSearchHit])
async def semantic_search_knowledge_graph(req: SemanticSearchRequest):
    """
    Performs vector cosine similarity search across all denial scenarios.
    Accepts natural-language queries (e.g., 'patient had secondary insurance but primary didn't remit')
    and returns top semantically matched scenarios with investigation checklists and CMS-1500 fields.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    hits = denial_vector_engine.search(
        query_text=req.query,
        carc_filter=req.carc_filter,
        top_k=req.top_k or 5
    )

    formatted = []
    for h in hits:
        sc = h.get("scenario", {})
        formatted.append(SemanticSearchHit(
            scenario_id=h["scenario_id"],
            code=h["code"],
            category_id=h.get("category_id"),
            category_name=h.get("category_name"),
            title=h["title"],
            root_cause=h["root_cause"],
            similarity=h["similarity"],
            encoder_type=h.get("encoder_type", "vector"),
            investigation_steps=sc.get("investigation_steps", []),
            form_requirements=sc.get("form_requirements", {}),
            action_plan=sc.get("action_plan", []),
            standard_notes=sc.get("standard_notes"),
        ))

    return formatted


@router.get("/viewer", response_class=HTMLResponse)
async def view_knowledge_graph():
    """Serves the interactive 3D Spherical & 2D Constellation Knowledge Graph HTML Visualizer"""
    viewer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_graph", "viewer.html")
    if not os.path.exists(viewer_path):
        raise HTTPException(status_code=404, detail="Knowledge graph visualizer HTML not built yet.")

    with open(viewer_path, "r", encoding="utf-8") as f:
        html = f.read()

    return HTMLResponse(content=html)
