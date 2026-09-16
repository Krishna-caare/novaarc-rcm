from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class NodeType(str, Enum):
    CATEGORY = "category"
    DENIAL_CODE = "denial_code"
    SCENARIO = "scenario"
    ROOT_CAUSE = "root_cause"
    INVESTIGATION_STEP = "investigation_step"
    PAYER_QUESTION = "payer_question"
    ACTION_PLAN = "action_plan"
    FORM_REQUIREMENT = "form_requirement"
    PAYER_POLICY = "payer_policy"


class RelationType(str, Enum):
    INCLUDES = "INCLUDES"
    MANIFESTS_AS = "MANIFESTS_AS"
    CAUSED_BY = "CAUSED_BY"
    REQUIRES_CHECK = "REQUIRES_CHECK"
    CALL_SCRIPT = "CALL_SCRIPT"
    RESOLVED_BY = "RESOLVED_BY"
    REQUIRES_FORM = "REQUIRES_FORM"
    GOVERNED_BY = "GOVERNED_BY"


@dataclass
class Node:
    id: str
    label: str
    type: NodeType
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type.value if isinstance(self.type, NodeType) else self.type,
            "description": self.description,
            "properties": self.properties,
        }


@dataclass
class Edge:
    source: str
    target: str
    relation: RelationType
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation.value if isinstance(self.relation, RelationType) else self.relation,
            "description": self.description,
            "properties": self.properties,
        }


@dataclass
class SubgraphResult:
    code: str
    code_description: str
    category: str
    scenarios: List[Dict[str, Any]]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "code_description": self.code_description,
            "category": self.category,
            "scenarios": self.scenarios,
            "nodes": self.nodes,
            "edges": self.edges,
        }
