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

                # Investigation Steps as individual starburst leaves
                inv_steps = sc.get("investigation_steps", [])
                for s_idx, step_text in enumerate(inv_steps):
                    inv_id = f"INV_{sc['id'].replace('-', '_')}_{s_idx+1}"
                    inv_node = Node(
                        id=inv_id,
                        label=step_text[:34] + ("..." if len(step_text) > 34 else ""),
                        type=NodeType.INVESTIGATION_STEP,
                        description=step_text,
                        properties={"step_index": s_idx + 1, "category_id": cat_id, "scenario": sc["id"]},
                    )
                    self._add_node(inv_node)
                    self._add_edge(sc_id, inv_id, RelationType.REQUIRES_CHECK, f"Verification check #{s_idx+1}")

                # Payer Call Questions as individual starburst leaves
                call_script = sc.get("call_script", {})
                for q_idx, (q_key, q_val) in enumerate(call_script.items()):
                    call_id = f"CALL_{sc['id'].replace('-', '_')}_{q_key}"
                    call_node = Node(
                        id=call_id,
                        label=f"Q{q_idx+1}: {q_val[:28]}...",
                        type=NodeType.PAYER_QUESTION,
                        description=q_val,
                        properties={"question_key": q_key, "category_id": cat_id, "scenario": sc["id"]},
                    )
                    self._add_node(call_node)
                    self._add_edge(sc_id, call_id, RelationType.CALL_SCRIPT, f"Phone inquiry {q_key}")

                # Form & Field Requirements
                form_req = sc.get("form_requirements", {})
                if form_req:
                    form_name = form_req.get("form_name", "CMS-1500")
                    box_number = form_req.get("box_number", "Field Requirement")
                    form_id = f"FORM_{sc['id'].replace('-', '_')}"
                    form_node = Node(
                        id=form_id,
                        label=f"{box_number} ({form_name.split('/')[0].strip()})",
                        type=NodeType.FORM_REQUIREMENT,
                        description=f"{form_name} - {box_number}. Required: {', '.join(form_req.get('required_documents', []))}",
                        properties=form_req,
                    )
                    self._add_node(form_node)
                    self._add_edge(sc_id, form_id, RelationType.REQUIRES_FORM, "Form & field correction requirement")

                # Resolution Action Plan as individual action leaves
                action_plan = sc.get("action_plan", [])
                for a_idx, act_text in enumerate(action_plan):
                    act_id = f"ACT_{sc['id'].replace('-', '_')}_{a_idx+1}"
                    act_node = Node(
                        id=act_id,
                        label=f"Action {a_idx+1}: {act_text[:30]}...",
                        type=NodeType.ACTION_PLAN,
                        description=act_text,
                        properties={"step_index": a_idx + 1, "category_id": cat_id, "scenario": sc["id"]},
                    )
                    self._add_node(act_node)
                    self._add_edge(sc_id, act_id, RelationType.RESOLVED_BY, f"Playbook resolution action #{a_idx+1}")

        # Cross-Ontology Clinical & Regulatory Interconnects (Bridges between related CARC clusters)
        cross_links = [
            ("CODE_CO_16", "CODE_CO_4", "Requires modifier or clinical notes unbundling"),
            ("CODE_CO_16", "CODE_CO_216", "Documentation deficiency triggers ADR medical review"),
            ("CODE_CO_197", "CODE_CO_16", "Missing authorization requires clinical record submission"),
            ("CODE_CO_4", "CODE_CO_97", "NCCI Procedure-to-Procedure bundling modifier relationship"),
            ("CODE_CO_29", "CODE_CO_22", "Secondary timely filing dependent on primary remittance receipt"),
            ("CODE_CO_50", "CODE_CO_16", "Medical necessity determination substantiated by progress notes"),
            ("CODE_CO_18", "CODE_CO_97", "Duplicate billing edit vs incidental procedure bundling"),
            ("CODE_CO_27", "CODE_CO_22", "Terminated patient coverage requires COB carrier update"),
        ]
        for src, tgt, reason in cross_links:
            if src in self.nodes and tgt in self.nodes:
                self._add_edge(src, tgt, RelationType.RELATED_TO, reason)

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
