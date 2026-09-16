import json
import os
import math
import random
from app.knowledge_graph.graph_engine import denial_kg

def build_viewer():
    graph_data = denial_kg.to_d3_graph()
    raw_nodes = graph_data["nodes"]
    raw_links = graph_data["links"]
    categories = graph_data["categories"]

    # 1. Propagate Category IDs to all 354 nodes
    node_map = {n["id"]: dict(n) for n in raw_nodes}
    for nid, n in node_map.items():
        if n["type"] == "category":
            n["cat_id"] = n["id"]
        elif n.get("properties") and n["properties"].get("category_id"):
            n["cat_id"] = n["properties"]["category_id"]
        else:
            n["cat_id"] = None

    for _ in range(4):
        for l in raw_links:
            src = node_map.get(l["source"])
            tgt = node_map.get(l["target"])
            if src and tgt:
                if src["cat_id"] and not tgt["cat_id"]:
                    tgt["cat_id"] = src["cat_id"]
                elif tgt["cat_id"] and not src["cat_id"]:
                    src["cat_id"] = tgt["cat_id"]

    # 2. Compute 3D Spherical & 2D Coordinates with pristine physics
    CAT_SPHERICAL_ANCHORS = {}
    CAT_2D_ANCHORS = {}
    num_cats = len(categories)
    for i, c in enumerate(categories):
        # 3D spherical Fibonacci distribution
        phi = math.acos(-1.0 + (2.0 * i + 1.0) / num_cats)
        theta = math.sqrt(num_cats * math.pi) * i
        CAT_SPHERICAL_ANCHORS[c["id"]] = (
            math.sin(phi) * math.cos(theta),
            math.sin(phi) * math.sin(theta),
            math.cos(phi),
        )
        # 2D radial layout
        angle_2d = (i / num_cats) * math.pi * 2
        CAT_2D_ANCHORS[c["id"]] = (
            math.cos(angle_2d) * 190,
            math.sin(angle_2d) * 190,
        )

    random.seed(42)
    node_list = list(node_map.values())
    for n in node_list:
        cid = n["cat_id"] or "CAT_MISSING_INFO"
        ux, uy, uz = CAT_SPHERICAL_ANCHORS.get(cid, (0, 0, 1))

        # Shell radius based on ontological hierarchy
        if n["type"] == "category":
            r3 = 280.0
            r2 = 190.0
            jitter = 0.0
        elif n["type"] == "denial_code":
            r3 = 315.0
            r2 = 250.0
            jitter = 0.22
        elif n["type"] == "scenario":
            r3 = 350.0
            r2 = 310.0
            jitter = 0.38
        else:
            r3 = 380.0
            r2 = 360.0
            jitter = 0.52

        # 3D Jitter on sphere surface
        jx = (random.random() - 0.5) * jitter
        jy = (random.random() - 0.5) * jitter
        jz = (random.random() - 0.5) * jitter
        norm = math.sqrt((ux + jx)**2 + (uy + jy)**2 + (uz + jz)**2) or 1.0
        n["x3"] = round(((ux + jx) / norm) * r3, 2)
        n["y3"] = round(((uy + jy) / norm) * r3, 2)
        n["z3"] = round(((uz + jz) / norm) * r3, 2)
        n["target_r3"] = r3

        # 2D Coordinates around category cluster
        cx2, cy2 = CAT_2D_ANCHORS.get(cid, (0, 0))
        angle_off = random.random() * math.pi * 2
        dist_off = 0 if n["type"] == "category" else (40 + random.random() * (r2 - 190))
        n["x2"] = round(cx2 + math.cos(angle_off) * dist_off, 2)
        n["y2"] = round(cy2 + math.sin(angle_off) * dist_off, 2)

    # 3D Relaxation to eliminate overlap & tension
    node_idx_map = {n["id"]: i for i, n in enumerate(node_list)}
    resolved_links = []
    for l in raw_links:
        if l["source"] in node_idx_map and l["target"] in node_idx_map:
            resolved_links.append((node_idx_map[l["source"]], node_idx_map[l["target"]]))

    for _ in range(50):
        # Repulsion
        for i in range(len(node_list)):
            a = node_list[i]
            for j in range(i + 1, min(i + 45, len(node_list))):
                b = node_list[j]
                dx = b["x3"] - a["x3"]
                dy = b["y3"] - a["y3"]
                dz = b["z3"] - a["z3"]
                dist = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
                if dist < 24.0:
                    force = (24.0 - dist) / dist * 0.16
                    fx, fy, fz = dx * force, dy * force, dz * force
                    if a["type"] != "category":
                        a["x3"] -= fx; a["y3"] -= fy; a["z3"] -= fz
                    if b["type"] != "category":
                        b["x3"] += fx; b["y3"] += fy; b["z3"] += fz

        # Link springs
        for si, ti in resolved_links:
            a = node_list[si]
            b = node_list[ti]
            dx = b["x3"] - a["x3"]
            dy = b["y3"] - a["y3"]
            dz = b["z3"] - a["z3"]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
            target_d = 30.0 if a["type"] == "category" or b["type"] == "category" else 20.0
            force = (dist - target_d) * 0.035
            fx, fy, fz = (dx / dist) * force, (dy / dist) * force, (dz / dist) * force
            if a["type"] != "category":
                a["x3"] += fx; a["y3"] += fy; a["z3"] += fz
            if b["type"] != "category":
                b["x3"] += fx; b["y3"] += fy; b["z3"] += fz

        # Re-project to spherical shell
        for n in node_list:
            if n["type"] == "category":
                continue
            r = math.sqrt(n["x3"]**2 + n["y3"]**2 + n["z3"]**2) or 1.0
            scale = n["target_r3"] / r
            n["x3"] = round(n["x3"] * scale, 2)
            n["y3"] = round(n["y3"] * scale, 2)
            n["z3"] = round(n["z3"] * scale, 2)

    # 2D Relaxation (with symmetric damping to prevent runaway vertical lines)
    for _ in range(60):
        for si, ti in resolved_links:
            a = node_list[si]
            b = node_list[ti]
            dx = b["x2"] - a["x2"]
            dy = b["y2"] - a["y2"]
            dist = math.sqrt(dx*dx + dy*dy) or 1.0
            target_d = 45.0 if a["type"] == "category" or b["type"] == "category" else 22.0
            force = (dist - target_d) * 0.03
            fx, fy = (dx / dist) * force, (dy / dist) * force
            if a["type"] != "category":
                a["x2"] += fx; a["y2"] += fy
            if b["type"] != "category":
                b["x2"] -= fx; b["y2"] -= fy

    # Prepare final clean payload
    clean_graph_data = {
        "nodes": node_list,
        "links": raw_links,
        "categories": categories,
    }
    graph_json = json.dumps(clean_graph_data)

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NovaArc RCM — Denial Knowledge Graph (Obsidian Engine)</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: #030407;
      color: #e5e7eb;
      font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      overflow: hidden;
      width: 100vw;
      height: 100vh;
      display: flex;
      user-select: none;
      -webkit-font-smoothing: antialiased;
    }

    #canvas-container {
      flex: 1;
      position: relative;
      height: 100%;
      min-width: 0;
      background: radial-gradient(circle at center, #090b10 0%, #020305 100%);
      overflow: hidden;
    }

    canvas {
      display: block;
      width: 100%;
      height: 100%;
      cursor: grab;
    }
    canvas:active { cursor: grabbing; }

    /* Top Floating Controls - Obsidian Glassmorphism */
    .top-bar {
      position: absolute;
      top: 14px;
      left: 16px;
      right: 16px;
      display: flex;
      gap: 10px;
      align-items: center;
      z-index: 10;
      pointer-events: none;
    }
    .top-bar > * { pointer-events: auto; }

    .brand-pill {
      background: rgba(18, 20, 28, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 7px 16px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      color: #f3f4f6;
      display: flex;
      align-items: center;
      gap: 8px;
      backdrop-filter: blur(14px);
      letter-spacing: 0.01em;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    .brand-pill .dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #3b82f6;
      box-shadow: 0 0 8px #3b82f6;
    }

    .search-wrapper {
      position: relative;
      flex: 1;
      max-width: 320px;
    }
    .search-input {
      width: 100%;
      background: rgba(18, 20, 28, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 7px 14px 7px 32px;
      border-radius: 6px;
      color: #f3f4f6;
      font-size: 12px;
      outline: none;
      backdrop-filter: blur(14px);
      transition: all 0.15s ease;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .search-input::placeholder { color: #6b7280; }
    .search-input:focus {
      border-color: rgba(59, 130, 246, 0.6);
      background: rgba(22, 25, 36, 0.95);
      box-shadow: 0 0 12px rgba(59, 130, 246, 0.25);
    }
    .search-icon {
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      width: 13px;
      height: 13px;
      stroke: #6b7280;
      pointer-events: none;
    }

    .category-pills {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      align-items: center;
    }
    .cat-chip {
      background: rgba(18, 20, 28, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.09);
      padding: 5px 11px;
      border-radius: 5px;
      font-size: 11px;
      font-weight: 500;
      color: #9ca3af;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      backdrop-filter: blur(10px);
      transition: all 0.15s ease;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    .cat-chip .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }
    .cat-chip:hover {
      background: rgba(30, 34, 46, 0.9);
      border-color: rgba(255, 255, 255, 0.25);
      color: #f3f4f6;
      transform: translateY(-1px);
    }
    .cat-chip.active {
      background: rgba(40, 46, 62, 0.95);
      border-color: rgba(255, 255, 255, 0.35);
      color: #ffffff;
      box-shadow: 0 0 10px rgba(255, 255, 255, 0.15);
    }

    /* Bottom Control Bar */
    .bottom-bar {
      position: absolute;
      bottom: 16px;
      left: 16px;
      display: flex;
      gap: 8px;
      align-items: center;
      z-index: 10;
      pointer-events: auto;
    }
    .ctrl-btn {
      background: rgba(18, 20, 28, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #d1d5db;
      padding: 6px 13px;
      border-radius: 6px;
      font-size: 11.5px;
      font-weight: 500;
      cursor: pointer;
      backdrop-filter: blur(12px);
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    .ctrl-btn:hover {
      background: rgba(30, 34, 46, 0.95);
      border-color: rgba(255, 255, 255, 0.25);
      color: #fff;
    }
    .ctrl-btn.active {
      background: rgba(45, 52, 70, 0.95);
      border-color: #3b82f6;
      color: #60a5fa;
    }

    .stats-tag {
      background: rgba(18, 20, 28, 0.80);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: #838a98;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 11px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      backdrop-filter: blur(10px);
    }

    /* Tooltip */
    #node-tooltip {
      position: absolute;
      pointer-events: none;
      background: rgba(12, 14, 20, 0.95);
      border: 1px solid rgba(255, 255, 255, 0.15);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 11px;
      color: #f3f4f6;
      display: none;
      z-index: 50;
      backdrop-filter: blur(14px);
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.6);
      transform: translate(12px, -50%);
      max-width: 260px;
    }
    #node-tooltip .tt-type {
      font-size: 9.5px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 700;
      margin-bottom: 2px;
    }
    #node-tooltip .tt-title {
      font-weight: 500;
      color: #e5e7eb;
      line-height: 1.35;
    }

    /* Right Obsidian Inspector Sidebar */
    .sidebar {
      width: 440px;
      height: 100%;
      background: #090a0f;
      border-left: 1px solid rgba(255, 255, 255, 0.08);
      padding: 24px;
      overflow-y: auto;
      z-index: 20;
      display: flex;
      flex-direction: column;
      gap: 18px;
      box-shadow: -8px 0 24px rgba(0, 0, 0, 0.5);
    }
    .sidebar::-webkit-scrollbar { width: 5px; }
    .sidebar::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.15);
      border-radius: 3px;
    }

    .node-type-badge {
      display: inline-block;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: 3px 8px;
      border-radius: 4px;
      margin-bottom: 8px;
      width: fit-content;
    }

    .sidebar-title {
      font-size: 17px;
      font-weight: 600;
      color: #f9fafb;
      line-height: 1.35;
      letter-spacing: -0.01em;
    }

    .sidebar-desc {
      font-size: 12.5px;
      color: #9ca3af;
      line-height: 1.5;
      margin-top: 6px;
    }

    .breadcrumb-path {
      font-size: 11px;
      color: #6b7280;
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }
    .breadcrumb-path span { color: #9ca3af; }

    .section-card {
      background: rgba(18, 20, 28, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 8px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .section-card h4 {
      font-size: 11.5px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #9ca3af;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 7px;
    }

    .checklist-item {
      font-size: 12px;
      color: #e5e7eb;
      display: flex;
      align-items: flex-start;
      gap: 8px;
      line-height: 1.45;
    }
    .checklist-item::before {
      content: "✓";
      color: #10b981;
      font-weight: 700;
      font-size: 11px;
    }

    .script-item {
      background: rgba(10, 12, 16, 0.8);
      border-left: 2px solid rgba(255, 255, 255, 0.3);
      padding: 8px 12px;
      border-radius: 0 4px 4px 0;
      font-size: 12px;
      color: #e5e7eb;
      line-height: 1.4;
    }
    .script-item strong {
      color: #93c5fd;
      font-size: 11px;
      display: block;
      margin-bottom: 3px;
    }

    .notes-box {
      background: #050608;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 5px;
      padding: 12px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 11px;
      color: #d1d5db;
      white-space: pre-wrap;
      line-height: 1.5;
      max-height: 180px;
      overflow-y: auto;
    }
    .copy-btn {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 4px 9px;
      border-radius: 4px;
      font-size: 10.5px;
      font-weight: 500;
      color: #e5e7eb;
      cursor: pointer;
      transition: all 0.15s;
    }
    .copy-btn:hover {
      background: rgba(255, 255, 255, 0.15);
      color: #fff;
    }

    .sub-item-link {
      padding: 8px 11px;
      border-radius: 6px;
      background: rgba(14, 16, 22, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.06);
      font-size: 11.5px;
      color: #d1d5db;
      cursor: pointer;
      transition: all 0.15s;
    }
    .sub-item-link:hover {
      background: rgba(28, 32, 44, 0.9);
      border-color: rgba(255, 255, 255, 0.2);
      color: #fff;
      transform: translateX(2px);
    }

    .hint-box {
      font-size: 12px;
      color: #6b7280;
      text-align: center;
      padding: 36px 16px;
      line-height: 1.6;
    }
  </style>
</head>
<body>
  <div id="canvas-container">
    <div class="top-bar">
      <div class="brand-pill">
        <span class="dot"></span>
        <span>NovaArc Knowledge Graph</span>
      </div>

      <div class="search-wrapper">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input type="text" class="search-input" id="search-box" placeholder="Search CARC, scenario, checklist, CPT..." autocomplete="off" />
      </div>

      <div class="category-pills" id="category-pills"></div>
    </div>

    <canvas id="graph-canvas"></canvas>

    <div class="bottom-bar">
      <button class="ctrl-btn active" id="btn-mode" title="Toggle 3D Sphere / 2D Constellation">🌐 3D Sphere</button>
      <button class="ctrl-btn active" id="btn-rotate" title="Toggle Celestial Orbit">✨ Orbit</button>
      <button class="ctrl-btn active" id="btn-labels" title="Toggle Labels">🏷️ Labels</button>
      <button class="ctrl-btn" id="btn-reset" title="Reset View">↺ Reset</button>
      <div class="stats-tag" id="stats-counter">354 nodes · 354 connections · 8 categories</div>
    </div>

    <div id="node-tooltip">
      <div class="tt-type" id="tt-type"></div>
      <div class="tt-title" id="tt-title"></div>
    </div>
  </div>

  <div class="sidebar" id="sidebar">
    <div id="sidebar-content">
      <div class="sidebar-header">
        <span class="node-type-badge" id="badge-type" style="background: rgba(59, 130, 246, 0.2); color: #93c5fd;">CATEGORY</span>
        <h2 class="sidebar-title" id="node-title">Healthcare Denial Knowledge Graph</h2>
        <p class="sidebar-desc" id="node-desc">Multi-hop ontological mesh connecting CARC/RARC denial codes, operational scenarios, investigation checklists, CMS-1500 box mappings, and resolution playbooks.</p>
      </div>

      <div id="dynamic-sections" style="display: flex; flex-direction: column; gap: 14px; margin-top: 16px;">
        <div class="hint-box">
          <svg style="width: 32px; height: 32px; stroke: #4b5563; fill: none; margin-bottom: 12px;" viewBox="0 0 24 24" stroke-width="1.5">
            <circle cx="12" cy="12" r="9"></circle>
            <path d="M12 3v18M3 12h18"></path>
          </svg><br/>
          Click any node in the spherical galaxy to inspect its root-cause investigation checklist, CMS-1500 form fields, payer call script, and resolution actions.
        </div>
      </div>
    </div>
  </div>

  <script>
    const graphData = """ + graph_json + """;

    const canvas = document.getElementById('graph-canvas');
    const ctx = canvas.getContext('2d');
    let width = 0;
    let height = 0;

    function resizeCanvas() {
      const container = document.getElementById('canvas-container');
      width = canvas.width = container ? container.clientWidth : window.innerWidth - 440;
      height = canvas.height = container ? container.clientHeight : window.innerHeight;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Official Jewel Palettes for the 8 Core Categories
    const CATEGORY_PALETTES = {
      'CAT_MISSING_INFO':       { accent: '#3b82f6', name: 'Missing Info' },
      'CAT_PRIOR_AUTH':          { accent: '#8b5cf6', name: 'Prior Auth' },
      'CAT_TIMELY_FILING':       { accent: '#ef4444', name: 'Timely Filing' },
      'CAT_COB':                 { accent: '#f59e0b', name: 'COB' },
      'CAT_MEDICAL_NECESSITY':   { accent: '#10b981', name: 'Med Necessity' },
      'CAT_CODING_MODIFIERS':    { accent: '#06b6d4', name: 'Coding & Mod' },
      'CAT_DUPLICATE_BUNDLING':  { accent: '#ec4899', name: 'Duplicate & NCCI' },
      'CAT_ELIGIBILITY':         { accent: '#6366f1', name: 'Eligibility' }
    };

    // Render Category Filter Chips
    const catContainer = document.getElementById('category-pills');
    if (graphData.categories) {
      graphData.categories.forEach(function(cat) {
        const pal = CATEGORY_PALETTES[cat.id] || { accent: cat.color || '#9ca3af', name: cat.name.split(' ')[0] };
        const chip = document.createElement('div');
        chip.className = 'cat-chip';
        chip.id = 'chip-' + cat.id;
        chip.innerHTML = '<span class="dot" style="background:' + pal.accent + '"></span>' + (pal.name || cat.name);
        chip.title = cat.name;
        chip.addEventListener('click', function() {
          selectCategory(cat.id);
        });
        catContainer.appendChild(chip);
      });
    }

    // Node & Link Processing
    const nodes = graphData.nodes.map(function(n) {
      const pal = CATEGORY_PALETTES[n.cat_id] || { accent: '#9ca3af' };
      let r = 2.8;
      let col = '#848e9c';

      if (n.type === 'category') {
        r = 11.0;
        col = pal.accent;
      } else if (n.type === 'denial_code') {
        r = 6.8;
        col = pal.accent;
      } else if (n.type === 'scenario') {
        r = 4.4;
        col = '#9ca6b5';
      } else if (n.type === 'investigation_step') {
        r = 2.8;
        col = '#738094';
      } else if (n.type === 'payer_question') {
        r = 2.8;
        col = '#738094';
      } else if (n.type === 'form_requirement') {
        r = 3.2;
        col = '#93c5fd';
      } else if (n.type === 'action_plan') {
        r = 3.2;
        col = '#6ee7b7';
      }

      return Object.assign({}, n, {
        color: col,
        radius: r,
        categoryColor: pal.accent,
        // Projected runtime values
        projX: 0,
        projY: 0,
        projZ: 0,
        projScale: 1.0,
        alpha: 1.0
      });
    });

    const nodeMap = new Map();
    nodes.forEach(function(n) { nodeMap.set(n.id, n); });

    const links = graphData.links.map(function(l) {
      return Object.assign({}, l, {
        sourceNode: nodeMap.get(l.source),
        targetNode: nodeMap.get(l.target)
      });
    }).filter(function(l) { return l.sourceNode && l.targetNode; });

    // Update bottom stats counter dynamically
    document.getElementById('stats-counter').textContent =
      nodes.length + ' nodes · ' + links.length + ' connections · ' + graphData.categories.length + ' categories';

    // Camera & Interaction State
    let is3DMode = true;
    let autoRotate = true;
    let showLabels = true;

    // 3D Angles
    let rotX = -0.32;
    let rotY = 0.55;
    let targetRotX = null;
    let targetRotY = null;
    let zoom3D = 1.0;
    let pan3D = { x: 0, y: 0 };

    // 2D Pan/Zoom
    let transform2D = { x: 0, y: 0, scale: 1.0 };
    let targetTransform2D = null;

    let isDragging = false;
    let isPanning = false;
    let startMouse = { x: 0, y: 0 };
    let draggedNode = null;
    let hoveredNode = null;
    let selectedNode = null;
    let filterQuery = '';

    // Celestial Ambient Background Stars (Pre-generated for deep cosmic ambiance)
    const AMBIENT_STARS = [];
    for (let s = 0; s < 120; s++) {
      AMBIENT_STARS.push({
        x: (Math.random() - 0.5) * 2000,
        y: (Math.random() - 0.5) * 1400,
        r: Math.random() * 1.2 + 0.3,
        alpha: Math.random() * 0.45 + 0.15
      });
    }

    // Mouse Listeners
    canvas.addEventListener('mousedown', function(e) {
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      // Hit-test on nodes
      let clicked = null;
      for (let i = nodes.length - 1; i >= 0; i--) {
        const n = nodes[i];
        const screenX = is3DMode ? n.projX : (width / 2 + transform2D.x + n.x2 * transform2D.scale);
        const screenY = is3DMode ? n.projY : (height / 2 + transform2D.y + n.y2 * transform2D.scale);
        const hitR = Math.max(n.radius * (is3DMode ? n.projScale : transform2D.scale) * 1.8, 9);
        const dx = mouseX - screenX;
        const dy = mouseY - screenY;
        if (dx * dx + dy * dy < hitR * hitR) {
          clicked = n;
          break;
        }
      }

      if (clicked) {
        selectNode(clicked);
        return;
      }

      if (e.button === 2 || e.shiftKey) {
        isPanning = true;
      } else {
        isDragging = true;
      }
      startMouse = { x: e.clientX, y: e.clientY };
      targetRotX = null;
      targetRotY = null;
      targetTransform2D = null;
    });

    window.addEventListener('mousemove', function(e) {
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      if (isDragging) {
        const dx = e.clientX - startMouse.x;
        const dy = e.clientY - startMouse.y;
        if (is3DMode) {
          rotY += dx * 0.0055;
          rotX = Math.max(-1.4, Math.min(1.4, rotX + dy * 0.0055));
        } else {
          transform2D.x += dx;
          transform2D.y += dy;
        }
        startMouse = { x: e.clientX, y: e.clientY };
      } else if (isPanning) {
        const dx = e.clientX - startMouse.x;
        const dy = e.clientY - startMouse.y;
        if (is3DMode) {
          pan3D.x += dx;
          pan3D.y += dy;
        } else {
          transform2D.x += dx;
          transform2D.y += dy;
        }
        startMouse = { x: e.clientX, y: e.clientY };
      } else {
        // Hover detection
        let found = null;
        for (let i = nodes.length - 1; i >= 0; i--) {
          const n = nodes[i];
          const screenX = is3DMode ? n.projX : (width / 2 + transform2D.x + n.x2 * transform2D.scale);
          const screenY = is3DMode ? n.projY : (height / 2 + transform2D.y + n.y2 * transform2D.scale);
          const hitR = Math.max(n.radius * (is3DMode ? n.projScale : transform2D.scale) * 1.8, 9);
          const dx = mouseX - screenX;
          const dy = mouseY - screenY;
          if (dx * dx + dy * dy < hitR * hitR) {
            found = n;
            break;
          }
        }
        if (found !== hoveredNode) {
          hoveredNode = found;
          updateTooltip(hoveredNode, mouseX, mouseY);
        } else if (hoveredNode) {
          updateTooltip(hoveredNode, mouseX, mouseY);
        }
      }
    });

    window.addEventListener('mouseup', function() {
      isDragging = false;
      isPanning = false;
    });

    canvas.addEventListener('wheel', function(e) {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      if (is3DMode) {
        zoom3D = Math.max(0.45, Math.min(2.8, zoom3D * zoomFactor));
      } else {
        transform2D.scale = Math.max(0.35, Math.min(3.2, transform2D.scale * zoomFactor));
      }
    });

    canvas.addEventListener('contextmenu', function(e) { e.preventDefault(); });

    // Tooltip Helper
    const tooltipEl = document.getElementById('node-tooltip');
    const ttType = document.getElementById('tt-type');
    const ttTitle = document.getElementById('tt-title');

    function updateTooltip(node, x, y) {
      if (!node) {
        tooltipEl.style.display = 'none';
        return;
      }
      ttType.textContent = node.type.replace(/_/g, ' ');
      ttType.style.color = node.categoryColor || '#93c5fd';
      ttTitle.textContent = node.label;
      tooltipEl.style.left = x + 'px';
      tooltipEl.style.top = y + 'px';
      tooltipEl.style.display = 'block';
    }

    // Main Obsidian Spherical Render Loop
    function render() {
      ctx.clearRect(0, 0, width, height);

      // Ambient Space Dust / Constellation Starfield
      ctx.fillStyle = '#ffffff';
      AMBIENT_STARS.forEach(function(star) {
        ctx.globalAlpha = star.alpha;
        ctx.beginPath();
        ctx.arc(width / 2 + star.x, height / 2 + star.y, star.r, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.globalAlpha = 1.0;

      // Auto-rotation in 3D mode
      if (is3DMode && autoRotate && !isDragging && !isPanning && !hoveredNode && !targetRotX) {
        rotY += 0.0018;
      }

      // Smooth camera interpolation
      if (targetRotX !== null && targetRotY !== null) {
        rotX += (targetRotX - rotX) * 0.10;
        rotY += (targetRotY - rotY) * 0.10;
        if (Math.abs(targetRotX - rotX) < 0.005 && Math.abs(targetRotY - rotY) < 0.005) {
          targetRotX = null;
          targetRotY = null;
        }
      }

      if (targetTransform2D !== null) {
        transform2D.x += (targetTransform2D.x - transform2D.x) * 0.12;
        transform2D.y += (targetTransform2D.y - transform2D.y) * 0.12;
        transform2D.scale += (targetTransform2D.scale - transform2D.scale) * 0.12;
        if (Math.abs(targetTransform2D.x - transform2D.x) < 0.5 &&
            Math.abs(targetTransform2D.y - transform2D.y) < 0.5) {
          targetTransform2D = null;
        }
      }

      // 1. Calculate Node Coordinates (3D Perspective Projection or 2D)
      const cosY = Math.cos(rotY), sinY = Math.sin(rotY);
      const cosX = Math.cos(rotX), sinX = Math.sin(rotX);
      const cameraDist = 880;
      const fov = 720;
      const centerX = width / 2 + (is3DMode ? pan3D.x : transform2D.x);
      const centerY = height / 2 + (is3DMode ? pan3D.y : transform2D.y);

      nodes.forEach(function(n) {
        if (is3DMode) {
          // 3D rotation
          const x1 = n.x3 * cosY + n.z3 * sinY;
          const z1 = -n.x3 * sinY + n.z3 * cosY;
          const y2 = n.y3 * cosX - z1 * sinX;
          const z2 = n.y3 * sinX + z1 * cosX;

          const factor = fov / (cameraDist - z2 * zoom3D);
          n.projX = centerX + x1 * zoom3D * factor;
          n.projY = centerY + y2 * zoom3D * factor;
          n.projZ = z2;
          n.projScale = factor;

          // Depth attenuation
          const depthNorm = (z2 + 380) / 760; // 0 (far) to 1 (near)
          n.alpha = Math.max(0.18, Math.min(1.0, 0.25 + depthNorm * 0.75));
        } else {
          n.projX = centerX + n.x2 * transform2D.scale;
          n.projY = centerY + n.y2 * transform2D.scale;
          n.projZ = 0;
          n.projScale = transform2D.scale;
          n.alpha = 1.0;
        }
      });

      // Active Connection Tracing
      const activeFocus = selectedNode || hoveredNode;
      const activeNeighbors = new Set();
      if (activeFocus) {
        links.forEach(function(l) {
          if (l.sourceNode === activeFocus) activeNeighbors.add(l.targetNode);
          if (l.targetNode === activeFocus) activeNeighbors.add(l.sourceNode);
        });
      }

      // 2. Draw Links (Obsidian Celestial Filaments with Depth)
      // Draw background/unfocused links first, then highlighted active connection pathways on top
      links.forEach(function(l) {
        const a = l.sourceNode;
        const b = l.targetNode;

        const isDirect = activeFocus && (a === activeFocus || b === activeFocus);
        const isNeighbor = activeFocus && !isDirect && activeNeighbors.has(a) && activeNeighbors.has(b);
        const isDimmed = activeFocus && !isDirect && !isNeighbor;

        // Skip direct connections for top layer rendering
        if (isDirect) return;

        ctx.beginPath();
        ctx.moveTo(a.projX, a.projY);
        ctx.lineTo(b.projX, b.projY);

        if (isDimmed) {
          ctx.strokeStyle = 'rgba(150, 175, 210, 0.08)';
          ctx.lineWidth = 0.5;
          ctx.globalAlpha = 0.20;
        } else {
          const depthAlpha = is3DMode ? ((a.alpha + b.alpha) / 2) : 1.0;
          if (a.type === 'category' || b.type === 'category') {
            ctx.strokeStyle = 'rgba(215, 230, 255, ' + (0.55 * depthAlpha) + ')';
            ctx.lineWidth = 1.6;
          } else if (a.type === 'denial_code' || b.type === 'denial_code') {
            ctx.strokeStyle = 'rgba(190, 212, 245, ' + (0.42 * depthAlpha) + ')';
            ctx.lineWidth = 1.2;
          } else if (l.relation === 'RELATED_TO') {
            ctx.strokeStyle = 'rgba(245, 158, 11, ' + (0.60 * depthAlpha) + ')';
            ctx.lineWidth = 1.3;
          } else {
            ctx.strokeStyle = 'rgba(165, 188, 220, ' + (0.30 * depthAlpha) + ')';
            ctx.lineWidth = 0.9;
          }
          ctx.globalAlpha = 1.0;
        }
        ctx.stroke();
      });

      // Highlighted Active Direct Connections (Rendered Crisp & Bright on Top)
      if (activeFocus) {
        links.forEach(function(l) {
          const a = l.sourceNode;
          const b = l.targetNode;
          const isDirect = (a === activeFocus || b === activeFocus);
          if (!isDirect) return;

          ctx.beginPath();
          ctx.moveTo(a.projX, a.projY);
          ctx.lineTo(b.projX, b.projY);

          // Luminous White Connection Filament
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2.6;
          ctx.globalAlpha = 1.0;
          ctx.shadowColor = '#ffffff';
          ctx.shadowBlur = 8;
          ctx.stroke();
          ctx.shadowBlur = 0;
        });
      }
      ctx.globalAlpha = 1.0;

      // 3. Draw Nodes (Constellation Stars & Category Jewel Hubs)
      // In 3D mode, sort back-to-front for realistic depth rendering
      const sortedNodes = is3DMode ? nodes.slice().sort(function(a, b) { return a.projZ - b.projZ; }) : nodes;

      sortedNodes.forEach(function(n) {
        const isSelected = n === selectedNode;
        const isHovered = n === hoveredNode;
        const isDirect = activeFocus && (n === activeFocus);
        const isNeighbor = activeFocus && activeNeighbors.has(n);
        const isConnected = isDirect || isNeighbor;
        const isDimmed = activeFocus && !isConnected;
        const isMatch = filterQuery && (
          n.label.toLowerCase().indexOf(filterQuery) !== -1 ||
          (n.description && n.description.toLowerCase().indexOf(filterQuery) !== -1)
        );

        const r = Math.max(1.8, n.radius * (is3DMode ? n.projScale : transform2D.scale) * (isSelected ? 1.4 : (isHovered ? 1.25 : 1.0)));

        // Outer Glow Halo for Hubs & Active Focus
        if (isSelected || isHovered) {
          ctx.beginPath();
          ctx.arc(n.projX, n.projY, r + 6, 0, Math.PI * 2);
          ctx.fillStyle = n.categoryColor || '#ffffff';
          ctx.globalAlpha = 0.38;
          ctx.fill();
        } else if (n.type === 'category' || n.type === 'denial_code') {
          ctx.beginPath();
          ctx.arc(n.projX, n.projY, r + 3, 0, Math.PI * 2);
          ctx.fillStyle = n.categoryColor;
          ctx.globalAlpha = isDimmed ? 0.05 : (0.22 * n.alpha);
          ctx.fill();
        }

        // Search Match Highlight Ring
        if (isMatch) {
          ctx.beginPath();
          ctx.arc(n.projX, n.projY, r + 4.5, 0, Math.PI * 2);
          ctx.strokeStyle = '#fbbf24';
          ctx.lineWidth = 2.0;
          ctx.globalAlpha = 1.0;
          ctx.stroke();
        }

        // Node Solid Core
        ctx.beginPath();
        ctx.arc(n.projX, n.projY, r, 0, Math.PI * 2);
        ctx.fillStyle = isSelected ? '#ffffff' : (isHovered ? '#ffffff' : n.color);
        ctx.globalAlpha = isDimmed ? 0.15 : (is3DMode ? n.alpha : 1.0);
        ctx.fill();

        // Node Outline
        ctx.strokeStyle = isSelected ? '#ffffff' : (isHovered ? n.categoryColor : 'rgba(0, 0, 0, 0.6)');
        ctx.lineWidth = isSelected ? 2.0 : (isHovered ? 1.6 : 0.6);
        ctx.stroke();
        ctx.globalAlpha = 1.0;

        // Clean Obsidian Typography
        const curScale = is3DMode ? (n.projScale * zoom3D) : transform2D.scale;
        const shouldShowLabel = showLabels && (
          isSelected || isHovered || isMatch || isConnected ||
          n.type === 'category' ||
          (n.type === 'denial_code' && curScale > 0.75) ||
          (n.type === 'scenario' && curScale > 1.25)
        );

        if (shouldShowLabel && !isDimmed) {
          const fontSize = n.type === 'category' ? 11.5 : (n.type === 'denial_code' ? 10.5 : 9.5);
          ctx.font = (n.type === 'category' || isSelected ? '600 ' : '400 ') + fontSize + 'px -apple-system, Inter, sans-serif';

          const maxChars = n.type === 'category' ? 26 : (n.type === 'denial_code' ? 20 : 16);
          const displayLabel = n.label.length > maxChars ? n.label.slice(0, maxChars - 2) + '...' : n.label;

          ctx.shadowColor = '#000000';
          ctx.shadowBlur = 6;
          ctx.fillStyle = isSelected ? '#ffffff' : (n.type === 'category' ? '#f9fafb' : '#9ca3af');
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          ctx.fillText(displayLabel, n.projX, n.projY + r + 3);
          ctx.shadowBlur = 0;
        }
      });

      requestAnimationFrame(render);
    }

    render();

    // Node Selection & Inspection
    function selectNode(node) {
      selectedNode = node;
      displayNodeDetails(node);

      if (is3DMode) {
        // Rotate sphere to face selected node directly toward camera
        const r = Math.sqrt(node.x3 * node.x3 + node.y3 * node.y3 + node.z3 * node.z3) || 1;
        targetRotY = -Math.atan2(node.x3, node.z3);
        targetRotX = Math.asin(node.y3 / r);
        zoom3D = Math.max(zoom3D, 1.15);
      } else {
        targetTransform2D = {
          x: -node.x2 * transform2D.scale,
          y: -node.y2 * transform2D.scale,
          scale: Math.max(transform2D.scale, 1.15)
        };
      }
    }

    function selectCategory(catId) {
      document.querySelectorAll('.cat-chip').forEach(function(c) { c.classList.remove('active'); });
      const chip = document.getElementById('chip-' + catId);
      if (chip) chip.classList.add('active');

      const catNode = nodes.find(function(n) { return n.id === catId; });
      if (catNode) {
        selectNode(catNode);
      }
    }

    // Search Input
    const searchBox = document.getElementById('search-box');
    searchBox.addEventListener('input', function(e) {
      filterQuery = e.target.value.toLowerCase().trim();
      if (filterQuery) {
        const match = nodes.find(function(n) {
          return n.label.toLowerCase().indexOf(filterQuery) !== -1 ||
                 (n.description && n.description.toLowerCase().indexOf(filterQuery) !== -1);
        });
        if (match) {
          selectNode(match);
        }
      }
    });

    // View Mode Toggle (3D Sphere vs 2D Constellation)
    const btnMode = document.getElementById('btn-mode');
    btnMode.addEventListener('click', function() {
      is3DMode = !is3DMode;
      btnMode.textContent = is3DMode ? '🌐 3D Sphere' : '🌌 2D Constellation';
      btnMode.classList.toggle('active', is3DMode);
    });

    // Orbit Toggle
    const btnRotate = document.getElementById('btn-rotate');
    btnRotate.addEventListener('click', function() {
      autoRotate = !autoRotate;
      btnRotate.textContent = autoRotate ? '✨ Orbit' : '✨ Orbit: Off';
      btnRotate.classList.toggle('active', autoRotate);
    });

    // Labels Toggle
    const btnLabels = document.getElementById('btn-labels');
    btnLabels.addEventListener('click', function() {
      showLabels = !showLabels;
      btnLabels.textContent = showLabels ? '🏷️ Labels' : '🏷️ Labels: Off';
      btnLabels.classList.toggle('active', showLabels);
    });

    // Reset Camera
    const btnReset = document.getElementById('btn-reset');
    btnReset.addEventListener('click', function() {
      rotX = -0.32;
      rotY = 0.55;
      targetRotX = null;
      targetRotY = null;
      zoom3D = 1.0;
      pan3D = { x: 0, y: 0 };
      transform2D = { x: 0, y: 0, scale: 1.0 };
      targetTransform2D = null;
      selectedNode = null;
      filterQuery = '';
      searchBox.value = '';
      document.querySelectorAll('.cat-chip').forEach(function(c) { c.classList.remove('active'); });
    });

    // Detailed Obsidian Inspector Sidebar
    function displayNodeDetails(node) {
      const badge = document.getElementById('badge-type');
      const title = document.getElementById('node-title');
      const desc = document.getElementById('node-desc');
      const container = document.getElementById('dynamic-sections');

      badge.textContent = node.type.replace(/_/g, ' ').toUpperCase();
      badge.style.background = 'rgba(' + hexToRgb(node.categoryColor || '#3b82f6') + ', 0.18)';
      badge.style.color = node.categoryColor || '#93c5fd';

      title.textContent = node.label;
      desc.textContent = node.description || 'Knowledge graph operational entity.';

      let html = '';

      // Direct Connected Neighbors list
      const connectedEdges = links.filter(function(l) { return l.sourceNode === node || l.targetNode === node; });
      const neighborNodes = connectedEdges.map(function(l) { return l.sourceNode === node ? l.targetNode : l.sourceNode; });

      // Breadcrumb context
      let breadcrumb = '';
      if (node.cat_id) {
        const cat = graphData.categories.find(function(c) { return c.id === node.cat_id; });
        if (cat) breadcrumb += '<span>' + cat.name + '</span>';
      }
      if (node.properties && node.properties.code) {
        breadcrumb += ' <span>›</span> <span>' + node.properties.code + '</span>';
      }
      if (breadcrumb) {
        html += '<div class="breadcrumb-path">' + breadcrumb + '</div>';
      }

      // If Category: List CARC Codes
      if (node.type === 'category') {
        const childCodes = links.filter(function(l) { return l.sourceNode === node; }).map(function(l) { return l.targetNode; });
        html += '<div class="section-card"><h4><span>📑</span> Included Denial Codes (' + childCodes.length + ')</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
        childCodes.forEach(function(c) {
          html += '<div class="sub-item-link" onclick="window.selectNodeById(\\'' + c.id + '\\')"><strong>' + c.label + '</strong><div style="font-size: 11px; color: #848e9c; margin-top: 2px;">' + (c.description || '') + '</div></div>';
        });
        html += '</div></div>';
      }

      // If Denial Code: List Scenarios
      if (node.type === 'denial_code') {
        const childScenarios = links.filter(function(l) { return l.sourceNode === node; }).map(function(l) { return l.targetNode; });
        html += '<div class="section-card"><h4><span>📂</span> Clinical Scenarios (' + childScenarios.length + ')</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
        childScenarios.forEach(function(s) {
          html += '<div class="sub-item-link" onclick="window.selectNodeById(\\'' + s.id + '\\')"><strong>' + s.label + '</strong><div style="font-size: 11px; color: #848e9c; margin-top: 2px;">' + (s.description || '') + '</div></div>';
        });
        html += '</div></div>';
      }

      // If Scenario: Show Investigation, CMS-1500, Script, Action Plan, Notes
      if (node.type === 'scenario') {
        const children = links.filter(function(l) { return l.sourceNode === node; }).map(function(l) { return l.targetNode; });
        const invNodes = children.filter(function(c) { return c.type === 'investigation_step'; });
        const callNodes = children.filter(function(c) { return c.type === 'payer_question'; });
        const formNode = children.find(function(c) { return c.type === 'form_requirement'; });
        const actNodes = children.filter(function(c) { return c.type === 'action_plan'; });

        if (invNodes.length > 0) {
          html += '<div class="section-card"><h4><span>🔍</span> Investigation Checklist (' + invNodes.length + ' Checks)</h4>';
          invNodes.forEach(function(item) {
            html += '<div class="checklist-item">' + (item.description || item.label) + '</div>';
          });
          html += '</div>';
        }

        if (formNode && formNode.properties) {
          html += '<div class="section-card"><h4><span>📋</span> CMS-1500 & Clearinghouse Fields</h4><div style="font-size: 12px; color: #d1d5db; line-height: 1.5;"><strong>Form:</strong> ' + (formNode.properties.form_name || 'CMS-1500') + '<br/><strong>Box / Segment:</strong> <span style="color: #93c5fd; font-weight: 600;">' + (formNode.properties.box_number || 'Field Spec') + '</span></div>';
          if (formNode.properties.required_documents) {
            html += '<div style="margin-top: 6px; font-size: 11px; color: #848e9c;"><strong>Required Attachments:</strong> ' + formNode.properties.required_documents.join(', ') + '</div>';
          }
          html += '</div>';
        }

        if (callNodes.length > 0) {
          html += '<div class="section-card"><h4><span>📞</span> Payer Call Script Questions</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
          callNodes.forEach(function(cq) {
            const key = (cq.properties && cq.properties.question_key) ? cq.properties.question_key.toUpperCase() : 'CALL SCRIPT';
            html += '<div class="script-item"><strong>' + key + ':</strong> "' + (cq.description || cq.label) + '"</div>';
          });
          html += '</div></div>';
        }

        if (actNodes.length > 0) {
          html += '<div class="section-card"><h4><span>⚡</span> Step-by-Step Resolution Playbook</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
          actNodes.forEach(function(act, idx) {
            html += '<div style="font-size: 12px; color: #e5e7eb; line-height: 1.4;"><span style="color: #6ee7b7; font-weight: 600;">' + (idx + 1) + '.</span> ' + (act.description || act.label) + '</div>';
          });
          html += '</div></div>';
        }

        if (node.properties && node.properties.standard_notes) {
          html += '<div class="section-card"><div style="display: flex; justify-content: space-between; align-items: center;"><h4><span>📝</span> Standard AR Notes</h4><button class="copy-btn" onclick="copyNotes()">Copy Notes</button></div><div class="notes-box" id="ar-notes-text">' + node.properties.standard_notes + '</div></div>';
        }
      }

      // If Leaf Node (Investigation, Call, Form, Action): Link back to parent Scenario
      if (node.type === 'investigation_step' || node.type === 'payer_question' || node.type === 'form_requirement' || node.type === 'action_plan') {
        const parentScenario = neighborNodes.find(function(n) { return n.type === 'scenario'; });
        if (parentScenario) {
          html += '<div class="section-card"><h4><span>📂</span> Parent Clinical Scenario</h4><div class="sub-item-link" onclick="window.selectNodeById(\\'' + parentScenario.id + '\\')"><strong>' + parentScenario.label + '</strong><div style="font-size: 11px; color: #848e9c; margin-top: 2px;">' + (parentScenario.description || '') + '</div></div></div>';
        }
      }

      // Direct Connected Nodes Section
      if (neighborNodes.length > 0 && node.type !== 'category') {
        html += '<div class="section-card"><h4><span>🔗</span> Connected Nodes (' + neighborNodes.length + ')</h4><div style="display: flex; flex-wrap: wrap; gap: 6px;">';
        neighborNodes.slice(0, 10).forEach(function(nbr) {
          html += '<button class="ctrl-btn" style="font-size: 10.5px; padding: 4px 8px;" onclick="window.selectNodeById(\\'' + nbr.id + '\\')">' + nbr.label.slice(0, 22) + '</button>';
        });
        html += '</div></div>';
      }

      container.innerHTML = html || '<div class="hint-box">Select a node in the constellation to inspect its clinical root cause and resolution playbook.</div>';
    }

    function hexToRgb(hex) {
      hex = hex.replace('#', '');
      if (hex.length === 3) hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
      const num = parseInt(hex, 16);
      return (num >> 16) + ', ' + ((num >> 8) & 255) + ', ' + (num & 255);
    }

    window.copyNotes = function() {
      const box = document.getElementById('ar-notes-text');
      if (box) {
        navigator.clipboard.writeText(box.innerText);
        const btn = document.querySelector('.copy-btn');
        if (btn) {
          btn.textContent = '✓ Copied';
          setTimeout(function() { btn.textContent = 'Copy Notes'; }, 2000);
        }
      }
    };

    window.selectNodeById = function(id) {
      const target = nodes.find(function(n) { return n.id === id; });
      if (target) {
        selectNode(target);
      }
    };
  </script>
</body>
</html>"""

    out_path = os.path.join(os.path.dirname(__file__), "viewer.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Obsidian-Style Spherical Knowledge Graph Viewer successfully built at: {out_path} ({len(html_content)} bytes)")

if __name__ == "__main__":
    build_viewer()
