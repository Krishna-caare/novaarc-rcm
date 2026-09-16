import asyncio
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/novaarc_test")
os.environ.setdefault("SECRET_KEY", "test_secret_key_123")

# Add backend to path
sys.path.insert(0, os.path.abspath("backend"))

from app.knowledge_graph.graph_engine import denial_kg
from app.knowledge_graph.models import NodeType
from app.services.denial_rag import run_denial_rag, match_best_scenario


def test_graph_structure():
    print("=" * 70)
    print("TEST 1: Verifying Knowledge Graph Structure & Node Metrics")
    print("=" * 70)

    overview = denial_kg.get_overview()
    print(f"Total Nodes: {overview['total_nodes']}")
    print(f"Total Edges: {overview['total_edges']}")
    print(f"Node Type Breakdown: {overview['node_type_counts']}")

    assert overview['total_nodes'] >= 50, f"Expected at least 50 nodes, got {overview['total_nodes']}"
    assert overview['total_edges'] >= 50, f"Expected at least 50 edges, got {overview['total_edges']}"
    assert len(overview['categories']) == 8, f"Expected 8 categories, got {len(overview['categories'])}"
    assert "CO-16" in overview['carc_codes']
    assert "CO-197" in overview['carc_codes']
    assert "CO-29" in overview['carc_codes']
    assert "CO-22" in overview['carc_codes']

    print("✓ Knowledge Graph structure and categories verified successfully!\n")


def test_subgraph_traversals():
    print("=" * 70)
    print("TEST 2: Verifying Subgraph Traversal & Leaf Extractions")
    print("=" * 70)

    test_codes = ["CO-16", "CO-197", "CO-29", "CO-22", "CO-50", "CO-97"]
    for code in test_codes:
        subgraph = denial_kg.get_subgraph(code)
        assert subgraph is not None, f"Subgraph for {code} should not be None"
        assert subgraph.code == code
        assert len(subgraph.scenarios) >= 1
        assert len(subgraph.nodes) >= 4
        assert len(subgraph.edges) >= 3

        # Check scenario details
        sc = subgraph.scenarios[0]
        assert "title" in sc
        assert "root_cause" in sc
        assert "investigation_steps" in sc
        assert "call_script" in sc
        assert "form_requirements" in sc
        assert "action_plan" in sc

        print(f"  ✓ {code}: Extracted {len(subgraph.scenarios)} scenario(s), {len(subgraph.nodes)} nodes, {len(subgraph.edges)} edges.")

    print("✓ Subgraph traversal and leaf extractions passed!\n")


def test_keyword_search():
    print("=" * 70)
    print("TEST 3: Verifying Semantic / Keyword Search across Scenarios")
    print("=" * 70)

    queries = ["operative", "modifier 25", "timely filing", "coordination of benefits", "retro-auth"]
    for q in queries:
        results = denial_kg.search_scenarios(q)
        assert len(results) >= 1, f"Search for '{q}' should return at least 1 match"
        print(f"  ✓ Search '{q}': Found {len(results)} matching scenario(s) (Top: {results[0]['code']} - {results[0]['title']})")

    print("✓ Keyword search verified!\n")


async def test_graph_rag_pipeline():
    print("=" * 70)
    print("TEST 4: Verifying GraphRAG Recommendation Pipeline")
    print("=" * 70)

    # Simulate denied claim: CO-16 with surgery CPT
    claim_context_surgery = {
        "claim_id": 901,
        "denial_code": "CO-16",
        "description": "Claim lacks information",
        "root_cause": "Missing records",
        "cpt_codes": ["29881"],
        "date_of_service": "2026-09-01",
        "denial_date": "2026-09-15",
        "payer_name": "Aetna Commercial"
    }

    rec1 = await run_denial_rag(claim_context_surgery)
    assert rec1 is not None
    assert "Operative" in rec1["scenario_title"]
    assert len(rec1["investigation_checklist"]) > 0
    assert len(rec1["resolution_action_plan"]) > 0
    assert "standard_ar_notes" in rec1
    print(f"  ✓ GraphRAG (CO-16 Surgery): Successfully identified scenario '{rec1['scenario_title']}'")
    print(f"    Action Plan Steps: {len(rec1['resolution_action_plan'])}")
    print(f"    Form Required: {rec1.get('form_requirements', {}).get('form_name')}")

    # Simulate denied claim: CO-16 with E/M Modifier 25
    claim_context_em = {
        "claim_id": 902,
        "denial_code": "CO-16",
        "description": "Modifier missing or invalid",
        "root_cause": "Missing modifier on E/M visit",
        "cpt_codes": ["99214", "20610"],
        "date_of_service": "2026-09-05",
        "denial_date": "2026-09-16",
        "payer_name": "UnitedHealthcare"
    }

    rec2 = await run_denial_rag(claim_context_em)
    assert "Modifier 25" in rec2["scenario_title"]
    print(f"  ✓ GraphRAG (CO-16 Modifier 25): Successfully identified scenario '{rec2['scenario_title']}'")

    # Simulate denied claim: CO-29 Timely Filing
    claim_context_tf = {
        "claim_id": 903,
        "denial_code": "CO-29",
        "description": "Time limit expired",
        "initial_submission_date": "2026-08-01",
        "date_of_service": "2026-07-15",
        "denial_date": "2026-09-16",
        "payer_name": "Blue Cross Blue Shield"
    }

    rec3 = await run_denial_rag(claim_context_tf)
    assert "Proof" in rec3["scenario_title"] or "Timely" in rec3["scenario_title"]
    print(f"  ✓ GraphRAG (CO-29 Timely Filing): Successfully identified scenario '{rec3['scenario_title']}'")
    print(f"    AR Call Notes Preview: {rec3['standard_ar_notes'][:80]}...")

    print("✓ GraphRAG recommendation pipeline verified!\n")


def test_viewer_html_exists():
    print("=" * 70)
    print("TEST 5: Verifying Standalone viewer.html Visualizer")
    print("=" * 70)

    viewer_path = os.path.join("backend", "app", "knowledge_graph", "viewer.html")
    assert os.path.exists(viewer_path), f"viewer.html does not exist at {viewer_path}"
    file_size = os.path.getsize(viewer_path)
    assert file_size > 10000, f"viewer.html seems incomplete, size: {file_size}"
    print(f"  ✓ viewer.html exists at {viewer_path} ({file_size:,} bytes)")
    print("✓ Standalone IDE Knowledge Graph Visualizer verified!\n")


async def main():
    test_graph_structure()
    test_subgraph_traversals()
    test_keyword_search()
    await test_graph_rag_pipeline()
    test_viewer_html_exists()
    print("=" * 70)
    print("ALL KNOWLEDGE GRAPH & GRAPHRAG VERIFICATION TESTS PASSED! (5/5)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
