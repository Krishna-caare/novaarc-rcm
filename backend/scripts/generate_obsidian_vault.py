import os
import json
import re
from typing import Dict, Any

from app.knowledge_graph.data import CATEGORIES, DENIAL_KNOWLEDGE_BASE

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "NovaArc-KG"))

# Sanitizer for Obsidian filenames
def clean_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', '', name).strip()
    return cleaned[:80]

def build_vault():
    print(f"Building complete NovaArc Obsidian Vault at: {VAULT_ROOT}")

    # Subdirectories
    dirs = [
        os.path.join(VAULT_ROOT, ".obsidian"),
        os.path.join(VAULT_ROOT, ".obsidian", "snippets"),
        os.path.join(VAULT_ROOT, "01_Categories"),
        os.path.join(VAULT_ROOT, "02_Denial_Codes"),
        os.path.join(VAULT_ROOT, "03_Scenarios"),
        os.path.join(VAULT_ROOT, "04_Investigation_Checks"),
        os.path.join(VAULT_ROOT, "05_Payer_Call_Scripts"),
        os.path.join(VAULT_ROOT, "06_Forms_and_EDI"),
        os.path.join(VAULT_ROOT, "07_Resolution_Playbooks"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 1. Write .obsidian/app.json
    app_config = {
        "cssTheme": "",
        "enabledCssSnippets": ["novaarc-cinematic"],
        "showFrontmatter": True,
        "foldHeading": True,
        "foldIndent": True
    }
    with open(os.path.join(VAULT_ROOT, ".obsidian", "app.json"), "w", encoding="utf-8") as f:
        json.dump(app_config, f, indent=2)

    # 2. Write .obsidian/snippets/novaarc-cinematic.css
    css_content = """/* ═══════════════════════════════════════════════════════════════
   NOVAARC CINEMATIC GRAPH — TOP TIER OBSIDIAN THEME
   ═══════════════════════════════════════════════════════════════ */

/* 🌌 PURE COSMIC BLACK BACKDROP */
.graph-view.color-fill,
.workspace-leaf-content[data-type="graph"] .view-content {
  background: radial-gradient(ellipse at center, #0a0a15 0%, #000000 100%) !important;
}

/* ✨ NODE GLOW HALO EFFECT */
.graph-view.color-circle {
  filter: drop-shadow(0 0 6px currentColor) 
          drop-shadow(0 0 12px currentColor);
  transition: all 0.3s ease;
}

.graph-view.color-circle:hover {
  filter: drop-shadow(0 0 20px currentColor) 
          drop-shadow(0 0 40px currentColor)
          drop-shadow(0 0 60px currentColor);
  transform: scale(1.4);
}

/* 🌠 EDGE FILAMENTS — GLOWING SILVER */
.graph-view.color-line {
  stroke: rgba(200, 220, 255, 0.40) !important;
  stroke-width: 1.3px !important;
  filter: drop-shadow(0 0 2px rgba(200, 220, 255, 0.5));
}

/* ⚡ HIGHLIGHTED CONNECTIONS ON HOVER */
.graph-view.color-line-highlight {
  stroke: #ffffff !important;
  stroke-width: 2.8px !important;
  filter: drop-shadow(0 0 8px #ffffff) 
          drop-shadow(0 0 16px rgba(255, 255, 255, 0.6));
  animation: pulse-line 1.5s infinite;
}

@keyframes pulse-line {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* 🏷️ NODE LABELS — ENTERPRISE TYPOGRAPHY */
.graph-view.color-text {
  fill: #e8ecf5 !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  font-weight: 700 !important;
  font-size: 13px !important;
  text-shadow: 0 0 6px rgba(0, 0, 0, 0.9);
}

/* 🎯 HUB NODES (CATEGORIES) — LARGER + BRIGHTER */
.graph-view.color-circle[data-tag*="hub"] {
  r: 14 !important;
  filter: drop-shadow(0 0 15px currentColor) 
          drop-shadow(0 0 30px currentColor);
}

/* 🌟 LEAF NODES — SUBTLE STARLIGHT */
.graph-view.color-circle[data-tag*="action"],
.graph-view.color-circle[data-tag*="script"] {
  r: 3.2 !important;
  opacity: 0.88;
}

/* 🎬 GRAPH CONTROLS — GLASSMORPHISM PANEL */
.graph-controls {
  background: rgba(15, 15, 25, 0.85) !important;
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
}

/* 🔍 SEARCH BAR — CYBERPUNK INPUT */
.graph-controls input[type="text"] {
  background: rgba(0, 0, 0, 0.6) !important;
  border: 1px solid rgba(100, 200, 255, 0.3) !important;
  color: #ffffff !important;
  border-radius: 8px !important;
}

.graph-controls input[type="text"]:focus {
  border-color: #00d4ff !important;
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.6);
}
"""
    with open(os.path.join(VAULT_ROOT, ".obsidian", "snippets", "novaarc-cinematic.css"), "w", encoding="utf-8") as f:
        f.write(css_content)

    # 3. Write .obsidian/graph.json (Obsidian graph view settings)
    graph_config = {
        "collapse-filter": False,
        "search": "",
        "showTags": True,
        "showAttachments": False,
        "hideUnresolved": False,
        "showOrphans": True,
        "collapse-color-groups": False,
        "colorGroups": [
            {"query": "tag:#hub/category", "color": {"a": 1, "rgb": 3900150}},        # #3b82f6 Cobalt
            {"query": "tag:#carc/code", "color": {"a": 1, "rgb": 16007006}},          # #f43f5e Ruby
            {"query": "tag:#scenario/clinical", "color": {"a": 1, "rgb": 9133302}},   # #8b5cf6 Amethyst
            {"query": "tag:#action/check", "color": {"a": 1, "rgb": 1096065}},         # #10b981 Emerald
            {"query": "tag:#script/call", "color": {"a": 1, "rgb": 16102923}},         # #f59e0b Amber
            {"query": "tag:#form/cms1500", "color": {"a": 1, "rgb": 959977}},          # #0ea5e9 Cerulean
            {"query": "tag:#resolution/playbook", "color": {"a": 1, "rgb": 15485081}}, # #ec4899 Rose
            {"query": "tag:#eligibility", "color": {"a": 1, "rgb": 6514417}}           # #6366f1 Indigo
        ],
        "collapse-display": False,
        "showArrow": True,
        "textFadeMultiplier": 1.2,
        "nodeSizeMultiplier": 1.35,
        "lineSizeMultiplier": 1.8,
        "collapse-forces": False,
        "centerStrength": 0.42,
        "repelStrength": 28,
        "linkStrength": 0.58,
        "linkDistance": 220
    }
    with open(os.path.join(VAULT_ROOT, ".obsidian", "graph.json"), "w", encoding="utf-8") as f:
        json.dump(graph_config, f, indent=2)

    # 4. Write JUGGL-COSMOS.md
    juggl_content = """---
title: NovaArc Cosmic Constellation
tags:
  - hub/category
---

# 🌌 NovaArc Denial Knowledge Graph — Live View

```juggl
---
layout: cola
animateIn: true
autoZoom: true
autoAddNodes: true
mode: workspace
navigator: true
toolbar: true
metaKeyHover: true
mergeEdges: true
styleGroups:
  - filter: 'tag:#hub/category'
    color: '#3b82f6'
    shape: 'ellipse'
    size: 60
    icon: '⚡'
  - filter: 'tag:#carc/code'
    color: '#f43f5e'
    shape: 'diamond'
    size: 40
  - filter: 'tag:#scenario/clinical'
    color: '#8b5cf6'
    shape: 'hexagon'
    size: 30
  - filter: 'tag:#action/check'
    color: '#10b981'
    shape: 'round-rectangle'
    size: 20
  - filter: 'tag:#script/call'
    color: '#f59e0b'
    shape: 'octagon'
    size: 20
  - filter: 'tag:#form/cms1500'
    color: '#0ea5e9'
    shape: 'triangle'
    size: 22
  - filter: 'tag:#resolution/playbook'
    color: '#ec4899'
    shape: 'star'
    size: 28
---
```
"""
    with open(os.path.join(VAULT_ROOT, "JUGGL-COSMOS.md"), "w", encoding="utf-8") as f:
        f.write(juggl_content)

    # 5. Write 📊 Command Center.md
    dashboard_content = """# 🎛️ NovaArc Command Center — Live KG Analytics

## 🔥 Top 10 Most Connected Denial Codes

```dataview
TABLE 
  length(file.outlinks) AS "Connections",
  category AS "Category",
  severity AS "Severity"
FROM #carc/code
SORT length(file.outlinks) DESC
LIMIT 10
```

## 🩺 Critical Scenarios (High Priority)

```dataview
LIST
FROM #scenario/clinical
WHERE severity = "critical"
```

## 📋 CMS-1500 Box Coverage Heatmap

```dataview
TABLE 
  file.link AS "Requirement",
  cms_box AS "Box #",
  frequency AS "Freq"
FROM #form/cms1500
SORT frequency DESC
```

## 🎯 Category → Denial Count

```dataview
TABLE 
  length(rows) AS "Total Denials"
FROM #carc/code
GROUP BY category
SORT length(rows) DESC
```
"""
    with open(os.path.join(VAULT_ROOT, "📊 Command Center.md"), "w", encoding="utf-8") as f:
        f.write(dashboard_content)

    # Category name map
    cat_map = {c["id"]: c for c in CATEGORIES}
    cat_notes = {}
    for c in CATEGORIES:
        safe_name = clean_filename(c["name"])
        cat_notes[c["id"]] = safe_name

    # Cross-links between CARC codes
    cross_links_map = {
        "CO-16": ["CO-4", "CO-216"],
        "CO-197": ["CO-16"],
        "CO-4": ["CO-97"],
        "CO-29": ["CO-22"],
        "CO-50": ["CO-16"],
        "CO-18": ["CO-97"],
        "CO-27": ["CO-22"],
    }

    # Track codes per category for Category note outlinks
    category_codes: Dict[str, list] = {c["id"]: [] for c in CATEGORIES}
    for code_str, d in DENIAL_KNOWLEDGE_BASE.items():
        cid = d.get("category_id")
        if cid in category_codes:
            category_codes[cid].append(code_str)

    # 6. Generate Category Notes (01_Categories)
    for c in CATEGORIES:
        safe_title = cat_notes[c["id"]]
        codes = category_codes.get(c["id"], [])
        links_str = "\n".join([f"- [[{cd}]]" for cd in codes])
        cat_md = f"""---
id: "{c['id']}"
title: "{c['name']}"
color: "{c['color']}"
total_codes: {len(codes)}
tags:
  - hub/category
---

# ⚡ {c['name']}

**Category ID:** `{c['id']}`  
**Accent Tone:** `{c['color']}`

{c['description']}

## 📌 Included CARC Denial Codes ({len(codes)})

{links_str}

---
*Part of [[📊 Command Center]] · [[JUGGL-COSMOS]]*
"""
        with open(os.path.join(VAULT_ROOT, "01_Categories", f"{safe_title}.md"), "w", encoding="utf-8") as f:
            f.write(cat_md)

    # 7. Generate CARC Code Notes & Connected Trees
    for code_str, data in DENIAL_KNOWLEDGE_BASE.items():
        cat_id = data.get("category_id", "CAT_MISSING_INFO")
        cat_title = cat_notes.get(cat_id, "Missing Information")
        scenarios = data.get("scenarios", [])
        
        # Scenarios links
        sc_links = "\n".join([f"- [[{sc['id']}]] — *{sc['title']}*" for sc in scenarios])
        
        # Cross-code links
        related_codes = cross_links_map.get(code_str, [])
        cross_str = "\n".join([f"- [[{rc}]]" for rc in related_codes]) if related_codes else "- None (Independent Domain)"

        severity = "critical" if code_str in ["CO-16", "CO-197", "CO-216", "CO-29", "CO-50"] else "moderate"

        code_md = f"""---
code: "{code_str}"
short_name: "{data.get('short_name', code_str)}"
category: "{cat_title}"
severity: "{severity}"
scenarios_count: {len(scenarios)}
tags:
  - carc/code
---

# 🎯 CARC {code_str}: {data.get('short_name', code_str)}

**Category:** [[{cat_title}]]  
**Standard Description:** {data.get('description', '')}

---

## 🩺 Clinical Scenarios ({len(scenarios)})
{sc_links}

---

## 🔗 Related CARC Interconnects
{cross_str}

---
*Part of [[{cat_title}]] · [[📊 Command Center]]*
"""
        with open(os.path.join(VAULT_ROOT, "02_Denial_Codes", f"{code_str}.md"), "w", encoding="utf-8") as f:
            f.write(code_md)

        # 8. Generate Scenarios and their connected leaves
        for sc in scenarios:
            sc_id = sc["id"]
            sc_title = sc["title"]
            sc_clean = sc_id.replace("-", "_")

            inv_steps = sc.get("investigation_steps", [])
            call_script = sc.get("call_script", {})
            form_req = sc.get("form_requirements", {})
            act_plan = sc.get("action_plan", [])

            # Generate individual leaf notes
            inv_links = []
            for idx, step_text in enumerate(inv_steps):
                inv_note_name = f"INV_{sc_clean}_{idx+1}"
                inv_links.append(f"- [[{inv_note_name}]]")
                inv_md = f"""---
scenario: "{sc_id}"
step_num: {idx+1}
tags:
  - action/check
---

# 🔍 {sc_id} Investigation Check #{idx+1}

**Scenario:** [[{sc_id}]]  
**Denial Code:** [[{code_str}]]

### Verification Step:
> {step_text}

---
*Linked to [[{sc_id}]]*
"""
                with open(os.path.join(VAULT_ROOT, "04_Investigation_Checks", f"{inv_note_name}.md"), "w", encoding="utf-8") as f:
                    f.write(inv_md)

            call_links = []
            for q_key, q_val in call_script.items():
                call_note_name = f"CALL_{sc_clean}_{q_key}"
                call_links.append(f"- [[{call_note_name}]]")
                call_md = f"""---
scenario: "{sc_id}"
question_key: "{q_key}"
tags:
  - script/call
---

# 📞 {sc_id} Payer Call Question ({q_key.upper()})

**Scenario:** [[{sc_id}]]  
**Denial Code:** [[{code_str}]]

### Question Script:
> "{q_val}"

---
*Linked to [[{sc_id}]]*
"""
                with open(os.path.join(VAULT_ROOT, "05_Payer_Call_Scripts", f"{call_note_name}.md"), "w", encoding="utf-8") as f:
                    f.write(call_md)

            form_links = []
            if form_req:
                form_note_name = f"FORM_{sc_clean}"
                form_links.append(f"- [[{form_note_name}]]")
                req_docs = ", ".join(form_req.get("required_documents", []))
                form_md = f"""---
scenario: "{sc_id}"
cms_box: "{form_req.get('box_number', 'N/A')}"
form_name: "{form_req.get('form_name', 'CMS-1500')}"
frequency: 1
tags:
  - form/cms1500
---

# 📋 Form Requirement: {form_req.get('box_number', 'CMS-1500')}

**Scenario:** [[{sc_id}]]  
**Form Standard:** `{form_req.get('form_name', 'CMS-1500')}`  
**Box / Segment:** `{form_req.get('box_number', 'N/A')}`

### Required Clinical Attachments:
{req_docs}

---
*Linked to [[{sc_id}]]*
"""
                with open(os.path.join(VAULT_ROOT, "06_Forms_and_EDI", f"{form_note_name}.md"), "w", encoding="utf-8") as f:
                    f.write(form_md)

            act_links = []
            for idx, act_text in enumerate(act_plan):
                act_note_name = f"ACT_{sc_clean}_{idx+1}"
                act_links.append(f"- [[{act_note_name}]]")
                act_md = f"""---
scenario: "{sc_id}"
step_num: {idx+1}
tags:
  - resolution/playbook
---

# ⚡ Playbook Action #{idx+1} for {sc_id}

**Scenario:** [[{sc_id}]]  
**Denial Code:** [[{code_str}]]

### Resolution Step:
> {act_text}

---
*Linked to [[{sc_id}]]*
"""
                with open(os.path.join(VAULT_ROOT, "07_Resolution_Playbooks", f"{act_note_name}.md"), "w", encoding="utf-8") as f:
                    f.write(act_md)

            # Write Scenario Master Note
            sc_md = f"""---
scenario_id: "{sc_id}"
title: "{sc_title}"
code: "{code_str}"
category: "{cat_title}"
severity: "{severity}"
tags:
  - scenario/clinical
---

# 🩺 {sc_title}

**CARC Code:** [[{code_str}]]  
**Category:** [[{cat_title}]]  
**Root Cause:** {sc.get('root_cause', '')}

---

## 🔍 Pre-Call Investigation Checklist
{chr(10).join(inv_links)}

## 📞 Payer Call Script Questions
{chr(10).join(call_links)}

## 📋 Form & Box Requirements
{chr(10).join(form_links)}

## ⚡ Resolution Action Plan Playbook
{chr(10).join(act_links)}

## 📝 Standard Pre-formatted AR Caller Note
```text
{sc.get('standard_notes', '')}
```

---
*Back to [[{code_str}]] · Category [[{cat_title}]]*
"""
            with open(os.path.join(VAULT_ROOT, "03_Scenarios", f"{sc_id}.md"), "w", encoding="utf-8") as f:
                f.write(sc_md)

    # 9. Write Root README.md
    readme_content = f"""# 🌌 NovaArc RCM — Denial Knowledge Graph Obsidian Vault

Welcome to the **NovaArc Denial Knowledge Graph Obsidian Vault**!  
This vault represents **354 interconnected clinical RCM ontologies**, matching the exact cinematic constellation architecture.

---

## 🚀 Quick Launch Guide in Obsidian

1. Open **Obsidian**.
2. Click **"Open folder as vault"**.
3. Select this directory:  
   `{VAULT_ROOT}`
4. Hit **Ctrl + G** (or **Cmd + G** on Mac) to open the **Interactive Graph View**.
5. The **Cosmic Cinematic Obsidian Theme** and **Color Groups** will automatically activate!

---

## 🎨 Color Legend (8 Jewel-Tone Hubs)

- ⚡ **Category Hubs** (`#hub/category`): Cobalt Sapphire (`#3b82f6`)
- 🎯 **CARC Codes** (`#carc/code`): Ruby Crimson (`#f43f5e`)
- 🩺 **Clinical Scenarios** (`#scenario/clinical`): Amethyst Violet (`#8b5cf6`)
- 🔍 **Investigation Checks** (`#action/check`): Emerald Jade (`#10b981`)
- 📞 **Payer Call Scripts** (`#script/call`): Amber Topaz (`#f59e0b`)
- 📋 **CMS-1500 & EDI Forms** (`#form/cms1500`): Cerulean Sky (`#0ea5e9`)
- ⚡ **Resolution Playbooks** (`#resolution/playbook`): Tourmaline Rose (`#ec4899`)

---

## 📊 Live Interactive Dashboards & Views

- 🎛️ **[[📊 Command Center]]**: Dataview analytics table ranking top connected codes, critical scenarios, and CMS-1500 box heatmaps.
- 🌌 **[[JUGGL-COSMOS]]**: Cytoscape.js powered live cluster visualization.
"""
    with open(os.path.join(VAULT_ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("Obsidian Vault generation finished successfully!")

if __name__ == "__main__":
    build_vault()
