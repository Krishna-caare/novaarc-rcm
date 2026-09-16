from typing import Dict, List, Any, Optional, Set
from app.knowledge_graph.models import Node, Edge, NodeType, RelationType, SubgraphResult
from app.knowledge_graph.data import CATEGORIES, DENIAL_KNOWLEDGE_BASE


class DenialKnowledgeGraph:
    """
    In-memory, bidirectional Healthcare Denial Knowledge Graph.
    Constructs an entity mesh connecting CARC/RARC codes, operational scenarios,
    investigation checklists, call scripts, CMS-1500 form fields, and resolution playbooks.
    """

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._adjacency: Dict[str, List[Edge]] = {}
        self._reverse_adjacency: Dict[str, List[Edge]] = {}
        self._build_graph()

    def _add_node(self, node: Node):
        self.nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []
        if node.id not in self._reverse_adjacency:
            self._reverse_adjacency[node.id] = []

    def _add_edge(self, source_id: str, target_id: str, relation: RelationType, description: str = ""):
        edge = Edge(source=source_id, target=target_id, relation=relation, description=description)
        self.edges.append(edge)
        self._adjacency[source_id].append(edge)
        self._reverse_adjacency[target_id].append(edge)

    def _build_graph(self):
        # 1. Add Category Nodes
        for cat in CATEGORIES:
            cat_node = Node(
                id=cat["id"],
                label=cat["name"],
                type=NodeType.CATEGORY,
                description=cat["description"],
                properties={"color": cat["color"]},
            )
            self._add_node(cat_node)

        # 2. Add CARC Code Nodes and Sub-Scenarios
        for code_str, data in DENIAL_KNOWLEDGE_BASE.items():
            code_id = f"CODE_{code_str.replace('-', '_')}"
            code_node = Node(
                id=code_id,
                label=f"{code_str}: {data.get('short_name', code_str)}",
                type=NodeType.DENIAL_CODE,
                description=data.get("description", ""),
                properties={"code": code_str, "category_id": data.get("category_id")},
            )
            self._add_node(code_node)

            # Link Category -> Denial Code
            cat_id = data.get("category_id")
            if cat_id and cat_id in self.nodes:
                self._add_edge(cat_id, code_id, RelationType.INCLUDES, f"Category includes {code_str}")

            # 3. Add Scenario Nodes and connected leaves
            for sc in data.get("scenarios", []):
                sc_id = f"SCENARIO_{sc['id'].replace('-', '_')}"
                sc_node = Node(
                    id=sc_id,
                    label=sc["title"],
                    type=NodeType.SCENARIO,
                    description=sc.get("root_cause", ""),
                    properties={
                        "raw_id": sc["id"],
                        "code": code_str,
                        "standard_notes": sc.get("standard_notes", ""),
                    },
                )
                self._add_node(sc_node)
                self._add_edge(code_id, sc_id, RelationType.MANIFESTS_AS, "Denial manifests in scenario")

                # Investigation Step
                inv_steps = sc.get("investigation_steps", [])
                if inv_steps:
                    inv_id = f"INV_{sc['id'].replace('-', '_')}"
                    inv_node = Node(
                        id=inv_id,
                        label=f"Investigation: {sc['title'][:30]}...",
                        type=NodeType.INVESTIGATION_STEP,
                        description="; ".join(inv_steps),
                        properties={"steps": inv_steps},
                    )
                    self._add_node(inv_node)
                    self._add_edge(sc_id, inv_id, RelationType.REQUIRES_CHECK, "Requires clinical/billing checks")

                # Payer Call Script
                call_script = sc.get("call_script", {})
                if call_script:
                    call_id = f"CALL_{sc['id'].replace('-', '_')}"
                    call_node = Node(
                        id=call_id,
                        label=f"Call Script: {sc['title'][:30]}...",
                        type=NodeType.PAYER_QUESTION,
                        description=f"{len(call_script)} phone inquiry questions",
                        properties=call_script,
                    )
                    self._add_node(call_node)
                    self._add_edge(sc_id, call_id, RelationType.CALL_SCRIPT, "Questions to ask payer representative")

                # Form & Field Requirements
                form_req = sc.get("form_requirements", {})
                if form_req:
                    form_id = f"FORM_{sc['id'].replace('-', '_')}"
                    form_node = Node(
                        id=form_id,
                        label=f"Form: {form_req.get('form_name', 'CMS-1500')}",
                        type=NodeType.FORM_REQUIREMENT,
                        description=f"Box: {form_req.get('box_number', 'N/A')}",
                        properties=form_req,
                    )
                    self._add_node(form_node)
                    self._add_edge(sc_id, form_id, RelationType.REQUIRES_FORM, "Specific form & box correction needed")

                # Resolution Action Plan
                action_plan = sc.get("action_plan", [])
                if action_plan:
                    act_id = f"ACT_{sc['id'].replace('-', '_')}"
                    act_node = Node(
                        id=act_id,
                        label=f"Action Plan: {sc['title'][:30]}...",
                        type=NodeType.ACTION_PLAN,
                        description=f"{len(action_plan)} step resolution playbook",
                        properties={"steps": action_plan},
                    )
                    self._add_node(act_node)
                    self._add_edge(sc_id, act_id, RelationType.RESOLVED_BY, "Step-by-step resolution playbook")

    def get_overview(self) -> Dict[str, Any]:
        """Summary metrics of the knowledge graph"""
        type_counts: Dict[str, int] = {}
        for n in self.nodes.values():
            t = n.type.value if isinstance(n.type, NodeType) else n.type
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_type_counts": type_counts,
            "categories": [c for c in CATEGORIES],
            "carc_codes": list(DENIAL_KNOWLEDGE_BASE.keys()),
        }

    def get_subgraph(self, code_or_query: str) -> Optional[SubgraphResult]:
        """Extract the connected subgraph for a specific CARC code (e.g. CO-16)"""
        clean_code = code_or_query.strip().upper().replace(" ", "-")
        if not clean_code.startswith("CO-") and not clean_code.startswith("PR-") and clean_code.isdigit():
            clean_code = f"CO-{clean_code}"

        code_data = DENIAL_KNOWLEDGE_BASE.get(clean_code)
        if not code_data:
            # Try fuzzy match
            for k in DENIAL_KNOWLEDGE_BASE.keys():
                if clean_code in k:
                    code_data = DENIAL_KNOWLEDGE_BASE[k]
                    clean_code = k
                    break

        if not code_data:
            return None

        target_code_id = f"CODE_{clean_code.replace('-', '_')}"
        visited_nodes: Set[str] = {target_code_id}
        collected_edges: List[Edge] = []

        # Find parent category
        for edge in self._reverse_adjacency.get(target_code_id, []):
            visited_nodes.add(edge.source)
            collected_edges.append(edge)

        # Find child scenarios and their leaves
        for edge in self._adjacency.get(target_code_id, []):
            visited_nodes.add(edge.target)
            collected_edges.append(edge)
            sc_id = edge.target
            # Find scenario children (investigation, call script, form, action)
            for sc_edge in self._adjacency.get(sc_id, []):
                visited_nodes.add(sc_edge.target)
                collected_edges.append(sc_edge)

        nodes_list = [self.nodes[nid].to_dict() for nid in visited_nodes if nid in self.nodes]
        edges_list = [e.to_dict() for e in collected_edges]

        return SubgraphResult(
            code=clean_code,
            code_description=code_data.get("description", ""),
            category=code_data.get("category_id", ""),
            scenarios=code_data.get("scenarios", []),
            nodes=nodes_list,
            edges=edges_list,
        )

    def search_scenarios(self, query: str, category_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search across denial scenarios, keywords, root causes, and action steps"""
        q = query.lower().strip()
        matches = []

        for code_str, data in DENIAL_KNOWLEDGE_BASE.items():
            if category_id and data.get("category_id") != category_id:
                continue

            for sc in data.get("scenarios", []):
                text_corpus = f"{code_str} {sc.get('title', '')} {sc.get('root_cause', '')} " \
                              f"{' '.join(sc.get('investigation_steps', []))} " \
                              f"{' '.join(sc.get('action_plan', []))} " \
                              f"{sc.get('form_requirements', {}).get('box_number', '')}"

                if not q or q in text_corpus.lower():
                    matches.append({
                        "code": code_str,
                        "code_description": data.get("description", ""),
                        "category_id": data.get("category_id"),
                        "scenario_id": sc.get("id"),
                        "title": sc.get("title"),
                        "root_cause": sc.get("root_cause"),
                        "investigation_steps": sc.get("investigation_steps", []),
                        "call_script": sc.get("call_script", {}),
                        "form_requirements": sc.get("form_requirements", {}),
                        "action_plan": sc.get("action_plan", []),
                        "standard_notes": sc.get("standard_notes", ""),
                    })

        return matches

    def to_d3_graph(self) -> Dict[str, Any]:
        """Convert entire graph to D3/Canvas format for interactive visualization"""
        category_map = {c["id"]: c for c in CATEGORIES}

        nodes_data = []
        for n in self.nodes.values():
            nd = n.to_dict()
            # Assign visual radius and color
            if n.type == NodeType.CATEGORY:
                nd["radius"] = 32
                nd["color"] = category_map.get(n.id, {}).get("color", "#3b82f6")
            elif n.type == NodeType.DENIAL_CODE:
                nd["radius"] = 24
                nd["color"] = "#60a5fa"
            elif n.type == NodeType.SCENARIO:
                nd["radius"] = 18
                nd["color"] = "#34d399"
            elif n.type == NodeType.INVESTIGATION_STEP:
                nd["radius"] = 12
                nd["color"] = "#fb923c"
            elif n.type == NodeType.PAYER_QUESTION:
                nd["radius"] = 12
                nd["color"] = "#f472b6"
            elif n.type == NodeType.FORM_REQUIREMENT:
                nd["radius"] = 14
                nd["color"] = "#c084fc"
            elif n.type == NodeType.ACTION_PLAN:
                nd["radius"] = 14
                nd["color"] = "#2dd4bf"
            else:
                nd["radius"] = 10
                nd["color"] = "#94a3b8"
            nodes_data.append(nd)

        links_data = [e.to_dict() for e in self.edges]

        return {
            "nodes": nodes_data,
            "links": links_data,
            "categories": CATEGORIES,
        }


# Global singleton instance
denial_kg = DenialKnowledgeGraph()
