import json
import os
from app.knowledge_graph.graph_engine import denial_kg

def build_viewer():
    graph_data = denial_kg.to_d3_graph()
    graph_json = json.dumps(graph_data)

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NovaArc RCM — Denial Knowledge Graph (Obsidian Engine)</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: #000000;
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
      background-color: #000000;
      overflow: hidden;
    }

    canvas {
      display: block;
      width: 100%;
      height: 100%;
      cursor: grab;
    }
    canvas:active { cursor: grabbing; }

    /* Top Floating Header & Filter Controls - Obsidian Minimalist Style */
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
      background: rgba(18, 19, 24, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 7px 16px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      color: #f3f4f6;
      display: flex;
      align-items: center;
      gap: 8px;
      backdrop-filter: blur(12px);
      letter-spacing: 0.01em;
    }
    .brand-pill .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #3b82f6;
    }

    .search-wrapper {
      position: relative;
      flex: 1;
      max-width: 320px;
    }
    .search-input {
      width: 100%;
      background: rgba(18, 19, 24, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 7px 14px 7px 32px;
      border-radius: 6px;
      color: #f3f4f6;
      font-size: 12px;
      outline: none;
      backdrop-filter: blur(12px);
      transition: border-color 0.15s;
    }
    .search-input::placeholder {
      color: #6b7280;
    }
    .search-input:focus {
      border-color: rgba(255, 255, 255, 0.28);
      background: rgba(24, 26, 32, 0.95);
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
      background: rgba(18, 19, 24, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.08);
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
    }
    .cat-chip .dot {
      width: 5px;
      height: 5px;
      border-radius: 50%;
    }
    .cat-chip:hover {
      background: rgba(30, 33, 42, 0.9);
      border-color: rgba(255, 255, 255, 0.2);
      color: #f3f4f6;
    }
    .cat-chip.active {
      background: rgba(45, 50, 64, 0.95);
      border-color: rgba(255, 255, 255, 0.3);
      color: #ffffff;
    }

    /* Bottom Toolbar */
    .bottom-bar {
      position: absolute;
      bottom: 16px;
      left: 16px;
      display: flex;
      gap: 8px;
      align-items: center;
      z-index: 10;
    }
    .ctrl-btn {
      background: rgba(18, 19, 24, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 6px 12px;
      border-radius: 5px;
      color: #cbd5e1;
      font-size: 11px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      backdrop-filter: blur(10px);
      transition: all 0.15s;
    }
    .ctrl-btn:hover {
      background: rgba(32, 35, 45, 0.95);
      border-color: rgba(255, 255, 255, 0.2);
      color: #fff;
    }
    .ctrl-btn.active {
      background: rgba(45, 50, 65, 0.95);
      border-color: rgba(255, 255, 255, 0.35);
      color: #fff;
    }

    .stats-tag {
      background: rgba(18, 19, 24, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 6px 12px;
      border-radius: 5px;
      font-size: 11px;
      color: #6b7280;
      font-weight: 500;
      backdrop-filter: blur(10px);
    }

    /* Floating Tooltip */
    #node-tooltip {
      position: absolute;
      display: none;
      pointer-events: none;
      background: rgba(14, 15, 19, 0.95);
      border: 1px solid rgba(255, 255, 255, 0.15);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
      padding: 8px 12px;
      border-radius: 5px;
      font-size: 12px;
      color: #fff;
      z-index: 25;
      transform: translate(-50%, -130%);
      white-space: nowrap;
      backdrop-filter: blur(12px);
    }
    #node-tooltip .tt-type {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 600;
      color: #9ca3af;
      margin-bottom: 2px;
    }
    #node-tooltip .tt-title {
      font-weight: 600;
      font-size: 12px;
      color: #f3f4f6;
    }

    /* Detail Inspector Sidebar - Obsidian Minimalist Style */
    .sidebar {
      width: 420px;
      height: 100%;
      background: rgba(10, 11, 15, 0.96);
      border-left: 1px solid rgba(255, 255, 255, 0.08);
      padding: 22px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      z-index: 20;
      user-select: text;
      backdrop-filter: blur(16px);
    }
    .sidebar::-webkit-scrollbar { width: 5px; }
    .sidebar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 3px; }

    .sidebar-header {
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding-bottom: 14px;
    }
    .node-type-badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      background: rgba(255, 255, 255, 0.08);
      color: #d1d5db;
      margin-bottom: 8px;
    }
    .sidebar-title {
      font-size: 17px;
      font-weight: 700;
      color: #f9fafb;
      line-height: 1.35;
    }
    .sidebar-desc {
      font-size: 12px;
      color: #9ca3af;
      line-height: 1.5;
      margin-top: 6px;
    }

    .section-card {
      background: rgba(18, 20, 26, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 6px;
      padding: 13px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .section-card h4 {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #d1d5db;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .checklist-item {
      font-size: 11.5px;
      color: #9ca3af;
      display: flex;
      gap: 8px;
      line-height: 1.45;
    }
    .checklist-item::before {
      content: "•";
      color: #d1d5db;
      font-weight: bold;
    }
    .script-item {
      background: rgba(12, 13, 17, 0.85);
      border-left: 2px solid rgba(255, 255, 255, 0.3);
      padding: 7px 11px;
      border-radius: 0 4px 4px 0;
      font-size: 11.5px;
      color: #e5e7eb;
      line-height: 1.4;
    }
    .script-item strong {
      color: #9ca3af;
      font-size: 10.5px;
      text-transform: uppercase;
      margin-right: 4px;
    }
    .notes-box {
      background: #050608;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 5px;
      padding: 10px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 10.5px;
      color: #d1d5db;
      white-space: pre-wrap;
      line-height: 1.5;
      max-height: 160px;
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
    .hint-box {
      font-size: 11.5px;
      color: #6b7280;
      text-align: center;
      padding: 24px 12px;
      line-height: 1.5;
    }
    .sub-item-link {
      padding: 7px 10px;
      border-radius: 5px;
      background: rgba(12, 13, 17, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.05);
      font-size: 11.5px;
      color: #d1d5db;
      cursor: pointer;
      transition: all 0.15s;
    }
    .sub-item-link:hover {
      background: rgba(25, 28, 36, 0.85);
      border-color: rgba(255, 255, 255, 0.15);
      color: #fff;
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
        <input type="text" class="search-input" id="search-box" placeholder="Search node, code, scenario..." autocomplete="off" />
      </div>

      <div class="category-pills" id="category-pills"></div>
    </div>

    <canvas id="graph-canvas"></canvas>

    <div class="bottom-bar">
      <button class="ctrl-btn" id="btn-reset" title="Reset Camera">↺ Reset View</button>
      <button class="ctrl-btn active" id="btn-labels" title="Toggle Labels">🏷️ Labels</button>
      <div class="stats-tag" id="stats-counter">205 nodes · 197 links</div>
    </div>

    <div id="node-tooltip">
      <div class="tt-type" id="tt-type"></div>
      <div class="tt-title" id="tt-title"></div>
    </div>
  </div>

  <div class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <span class="node-type-badge" id="badge-type">Category</span>
      <h2 class="sidebar-title" id="node-title">Missing Information & Documentation</h2>
      <p class="sidebar-desc" id="node-desc">Claims failing due to absent operative reports, medical records, or unsigned certifications.</p>
    </div>

    <div id="dynamic-sections" style="display: flex; flex-direction: column; gap: 14px;">
      <div class="hint-box">
        Click on any node in the Obsidian constellation to inspect its investigation checklist, CMS-1500 field mapping, and payer script.
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
      const w = container ? container.clientWidth : 0;
      const h = container ? container.clientHeight : 0;
      width = canvas.width = Math.max(w || (window.innerWidth - 420), 500);
      height = canvas.height = Math.max(h || window.innerHeight, 500);
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Obsidian Muted Tag Accents for Hubs (leaves stay graphite silver)
    const CLUSTER_PALETTES = {
      'CAT_MISSING_INFO':       { accent: '#3b82f6', name: 'Missing Info' },
      'CAT_PRIOR_AUTH':          { accent: '#10b981', name: 'Prior Auth' },
      'CAT_TIMELY_FILING':       { accent: '#f43f5e', name: 'Timely Filing' },
      'CAT_COB':                 { accent: '#f59e0b', name: 'COB' },
      'CAT_MEDICAL_NECESSITY':   { accent: '#8b5cf6', name: 'Med Necessity' },
      'CAT_CODING_MODIFIERS':    { accent: '#0ea5e9', name: 'Coding & Mod' },
      'CAT_ELIGIBILITY':         { accent: '#6366f1', name: 'Eligibility' }
    };

    const CLUSTER_CENTERS = {
      'CAT_MISSING_INFO':       { angle: 0,                   dist: 175 },
      'CAT_PRIOR_AUTH':          { angle: Math.PI * 0.25,      dist: 175 },
      'CAT_TIMELY_FILING':       { angle: Math.PI * 0.5,       dist: 175 },
      'CAT_COB':                 { angle: Math.PI * 0.75,      dist: 175 },
      'CAT_MEDICAL_NECESSITY':   { angle: Math.PI,             dist: 175 },
      'CAT_CODING_MODIFIERS':    { angle: Math.PI * 1.25,      dist: 175 },
      'CAT_DUPLICATE_BUNDLING':  { angle: Math.PI * 1.5,       dist: 175 },
      'CAT_ELIGIBILITY':         { angle: Math.PI * 1.75,      dist: 175 }
    };

    // Category Filter Chips
    const catContainer = document.getElementById('category-pills');
    if (graphData.categories) {
      graphData.categories.forEach(function(cat) {
        const pal = CLUSTER_PALETTES[cat.id] || { accent: '#9ca3af' };
        const chip = document.createElement('div');
        chip.className = 'cat-chip';
        chip.innerHTML = '<span class="dot" style="background:' + pal.accent + '"></span>' + (pal.name || cat.name.split(' ')[0]);
        chip.title = cat.name;
        chip.addEventListener('click', function() {
          selectCategory(cat.id);
        });
        catContainer.appendChild(chip);
      });
    }

    function getNodeCategoryId(node) {
      if (node.type === 'category') return node.id;
      if (node.properties && node.properties.category_id) return node.properties.category_id;
      return null;
    }

    // Initialize Nodes with Obsidian Design Hierarchy
    const nodes = graphData.nodes.map(function(n) {
      let catId = getNodeCategoryId(n);
      return Object.assign({}, n, {
        categoryId: catId,
        x: 0, y: 0, vx: 0, vy: 0,
        radius: (n.type === 'category' ? 10.5 : (n.type === 'denial_code' ? 6.5 : (n.type === 'scenario' ? 4.2 : 2.6))),
        color: '#848a98'
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

    // Propagate category ID to child nodes
    for (let p = 0; p < 3; p++) {
      links.forEach(function(l) {
        if (l.sourceNode.categoryId && !l.targetNode.categoryId) {
          l.targetNode.categoryId = l.sourceNode.categoryId;
        }
        if (l.targetNode.categoryId && !l.sourceNode.categoryId) {
          l.sourceNode.categoryId = l.targetNode.categoryId;
        }
      });
    }

    // Obsidian Palette Assignment:
    // Category hubs and CARC code hubs have color accents; leaves are graphite silver stars
    nodes.forEach(function(n, i) {
      const pal = CLUSTER_PALETTES[n.categoryId] || { accent: '#9ca3af' };
      if (n.type === 'category') {
        n.color = pal.accent;
        n.radius = 10.5;
      } else if (n.type === 'denial_code') {
        n.color = pal.accent;
        n.radius = 6.4;
      } else if (n.type === 'scenario') {
        n.color = '#9aa2b1';
        n.radius = 4.2;
      } else {
        // Child checkpoints, form boxes, scripts, actions: pure Obsidian graphite-silver stars
        n.color = '#798394';
        n.radius = 2.6;
      }

      // Initial orbital position
      const cluster = CLUSTER_CENTERS[n.categoryId] || { angle: (i / nodes.length) * Math.PI * 2, dist: 160 };
      const cx = Math.cos(cluster.angle) * cluster.dist;
      const cy = Math.sin(cluster.angle) * cluster.dist;

      if (n.type === 'category') {
        n.x = cx;
        n.y = cy;
      } else if (n.type === 'denial_code') {
        const offsetAngle = Math.random() * Math.PI * 2;
        const offsetDist = 30 + Math.random() * 45;
        n.x = cx + Math.cos(offsetAngle) * offsetDist;
        n.y = cy + Math.sin(offsetAngle) * offsetDist;
      } else if (n.type === 'scenario') {
        const offsetAngle = Math.random() * Math.PI * 2;
        const offsetDist = 50 + Math.random() * 60;
        n.x = cx + Math.cos(offsetAngle) * offsetDist;
        n.y = cy + Math.sin(offsetAngle) * offsetDist;
      } else {
        const offsetAngle = Math.random() * Math.PI * 2;
        const offsetDist = 65 + Math.random() * 75;
        n.x = cx + Math.cos(offsetAngle) * offsetDist;
        n.y = cy + Math.sin(offsetAngle) * offsetDist;
      }
    });

    // Organic Force Relaxation for Constellation Density
    for (let step = 0; step < 130; step++) {
      // Repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          let dx = b.x - a.x;
          let dy = b.y - a.y;
          let dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const minDist = (a.radius + b.radius) * 2.7;
          if (dist < minDist) {
            const force = (minDist - dist) / dist * 0.30;
            const fx = dx * force;
            const fy = dy * force;
            if (a.type !== 'category') { a.vx -= fx; a.vy -= fy; }
            if (b.type !== 'category') { b.vx += fx; b.vy += fy; }
          }
        }
      }

      // Link spring attraction
      links.forEach(function(l) {
        const a = l.sourceNode;
        const b = l.targetNode;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        let targetDist = 20 + (a.radius + b.radius);
        if (a.type === 'category' || b.type === 'category') targetDist = 44;
        else if (a.type === 'denial_code' || b.type === 'denial_code') targetDist = 28;
        const force = (dist - targetDist) * 0.048;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        if (a.type !== 'category') { a.vx -= fx; a.vy -= fy; }
        if (b.type !== 'category') { b.vx += fx; b.vy += fy; }
      });

      // Gravity toward cluster anchor and central cosmic cohesion
      nodes.forEach(function(n) {
        if (n.type === 'category') return;
        const cluster = CLUSTER_CENTERS[n.categoryId];
        if (cluster) {
          const cx = Math.cos(cluster.angle) * cluster.dist;
          const cy = Math.sin(cluster.angle) * cluster.dist;
          n.vx += (cx - n.x) * 0.011;
          n.vy += (cy - n.y) * 0.011;
        }
        // Subtle global pull to prevent stray drift
        n.vx -= n.x * 0.0016;
        n.vy -= n.y * 0.0016;

        n.x += n.vx;
        n.y += n.vy;
        n.vx *= 0.70;
      });
    }

    // Camera State
    let transform = { x: 0, y: 0, scale: 1.0 };
    let isDragging = false;
    let draggedNode = null;
    let startPan = { x: 0, y: 0 };
    let hoveredNode = null;
    let selectedNode = null;
    let filterQuery = '';
    let showLabels = true;
    let targetTransform = null;

    canvas.addEventListener('mousedown', function(e) {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - width / 2 - transform.x) / transform.scale;
      const mouseY = (e.clientY - rect.top - height / 2 - transform.y) / transform.scale;

      for (let i = nodes.length - 1; i >= 0; i--) {
        const n = nodes[i];
        const dx = mouseX - n.x;
        const dy = mouseY - n.y;
        const hitR = Math.max(n.radius * 1.8, 10);
        if (dx * dx + dy * dy < hitR * hitR) {
          draggedNode = n;
          selectNode(n);
          targetTransform = null;
          return;
        }
      }

      isDragging = true;
      startPan = { x: e.clientX - transform.x, y: e.clientY - transform.y };
      targetTransform = null;
    });

    window.addEventListener('mousemove', function(e) {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - width / 2 - transform.x) / transform.scale;
      const mouseY = (e.clientY - rect.top - height / 2 - transform.y) / transform.scale;

      if (draggedNode) {
        draggedNode.x = mouseX;
        draggedNode.y = mouseY;
        draggedNode.vx = 0;
        draggedNode.vy = 0;
      } else if (isDragging) {
        transform.x = e.clientX - startPan.x;
        transform.y = e.clientY - startPan.y;
      } else {
        let found = null;
        for (let i = nodes.length - 1; i >= 0; i--) {
          const n = nodes[i];
          const dx = mouseX - n.x;
          const dy = mouseY - n.y;
          const hitR = Math.max(n.radius * 1.6, 9);
          if (dx * dx + dy * dy < hitR * hitR) {
            found = n;
            break;
          }
        }
        if (found !== hoveredNode) {
          hoveredNode = found;
          updateTooltip(hoveredNode, e.clientX - rect.left, e.clientY - rect.top);
        }
      }
    });

    window.addEventListener('mouseup', function() {
      draggedNode = null;
      isDragging = false;
    });

    canvas.addEventListener('wheel', function(e) {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      transform.scale = Math.max(0.35, Math.min(3.5, transform.scale * zoomFactor));
    });

    const tooltipEl = document.getElementById('node-tooltip');
    const ttType = document.getElementById('tt-type');
    const ttTitle = document.getElementById('tt-title');

    function updateTooltip(node, x, y) {
      if (!node) {
        tooltipEl.style.display = 'none';
        return;
      }
      ttType.textContent = node.type.replace('_', ' ');
      ttType.style.color = node.color;
      ttTitle.textContent = node.label;
      tooltipEl.style.left = x + 'px';
      tooltipEl.style.top = y + 'px';
      tooltipEl.style.display = 'block';
    }

    // Obsidian Render Loop
    function draw() {
      if (targetTransform) {
        transform.x += (targetTransform.x - transform.x) * 0.12;
        transform.y += (targetTransform.y - transform.y) * 0.12;
        transform.scale += (targetTransform.scale - transform.scale) * 0.12;
        if (Math.abs(targetTransform.x - transform.x) < 0.4 &&
            Math.abs(targetTransform.y - transform.y) < 0.4 &&
            Math.abs(targetTransform.scale - transform.scale) < 0.005) {
          targetTransform = null;
        }
      }

      ctx.clearRect(0, 0, width, height);

      ctx.save();
      ctx.translate(width / 2 + transform.x, height / 2 + transform.y);
      ctx.scale(transform.scale, transform.scale);

      const activeFocus = selectedNode || hoveredNode;
      const activeNeighbors = new Set();
      if (activeFocus) {
        links.forEach(function(l) {
          if (l.sourceNode === activeFocus) activeNeighbors.add(l.targetNode);
          if (l.targetNode === activeFocus) activeNeighbors.add(l.sourceNode);
        });
      }

      // 1. Draw Links (Obsidian High-Contrast Graphite Filaments)
      links.forEach(function(l) {
        const a = l.sourceNode;
        const b = l.targetNode;

        const isDirect = activeFocus && (a === activeFocus || b === activeFocus);
        const isNeighbor = activeFocus && !isDirect && activeNeighbors.has(a) && activeNeighbors.has(b);
        const isDimmed = activeFocus && !isDirect && !isNeighbor;

        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);

        if (isDirect) {
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2.4;
          ctx.globalAlpha = 1.0;
        } else if (isNeighbor) {
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.70)';
          ctx.lineWidth = 1.5;
          ctx.globalAlpha = 0.88;
        } else if (isDimmed) {
          ctx.strokeStyle = 'rgba(180, 195, 220, 0.12)';
          ctx.lineWidth = 0.65;
          ctx.globalAlpha = 0.30;
        } else {
          // PROMINENT, CRISP OBSIDIAN LINKS (Properly visible like reference)
          if (a.type === 'category' || b.type === 'category') {
            ctx.strokeStyle = 'rgba(225, 235, 255, 0.65)'; // Category spine
            ctx.lineWidth = 1.5;
          } else if (a.type === 'denial_code' || b.type === 'denial_code') {
            ctx.strokeStyle = 'rgba(200, 215, 240, 0.52)'; // Major code branches
            ctx.lineWidth = 1.25;
          } else {
            ctx.strokeStyle = 'rgba(175, 192, 220, 0.40)'; // Fine constellation filaments
            ctx.lineWidth = 1.0;
          }
          ctx.globalAlpha = 1.0;
        }
        ctx.stroke();
      });
      ctx.globalAlpha = 1.0;

      // 2. Draw Nodes (Obsidian Constellation Stars & Jewel Hubs)
      nodes.forEach(function(n) {
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

        const r = n.radius * (isSelected ? 1.4 : (isHovered ? 1.25 : 1.0));

        // Soft outer focus halo for hubs & active nodes
        if (isSelected || isHovered) {
          ctx.beginPath();
          ctx.arc(n.x, n.y, r + 5, 0, Math.PI * 2);
          ctx.fillStyle = n.color;
          ctx.globalAlpha = 0.32;
          ctx.fill();
          ctx.globalAlpha = 1.0;
        } else if (n.type === 'category' || n.type === 'denial_code') {
          ctx.beginPath();
          ctx.arc(n.x, n.y, r + 2.5, 0, Math.PI * 2);
          ctx.fillStyle = n.color;
          ctx.globalAlpha = isDimmed ? 0.05 : 0.18;
          ctx.fill();
          ctx.globalAlpha = 1.0;
        }

        // Node Body
        ctx.beginPath();
        ctx.arc(n.x, n.y, Math.max(1.8, r), 0, Math.PI * 2);
        ctx.fillStyle = isSelected ? '#ffffff' : (isHovered ? '#ffffff' : n.color);
        ctx.globalAlpha = isDimmed ? 0.20 : 1.0;
        ctx.fill();

        // Node Edge Outline
        ctx.strokeStyle = isSelected ? '#ffffff' : (isHovered ? n.color : 'rgba(0, 0, 0, 0.5)');
        ctx.lineWidth = isSelected ? 2.0 : (isHovered ? 1.6 : 0.5);
        ctx.stroke();
        ctx.globalAlpha = 1.0;

        // Clean Obsidian Typography
        const shouldShowLabel = showLabels && (
          isSelected || isHovered || isMatch || isConnected ||
          n.type === 'category' ||
          (n.type === 'denial_code' && transform.scale > 0.65) ||
          (n.type === 'scenario' && transform.scale > 1.3)
        );

        if (shouldShowLabel && !isDimmed) {
          const fontSize = n.type === 'category' ? 11.5 : (n.type === 'denial_code' ? 10.5 : 9.5);
          ctx.font = (n.type === 'category' || isSelected ? '600 ' : '400 ') + fontSize + 'px -apple-system, Inter, sans-serif';

          const maxChars = n.type === 'category' ? 26 : (n.type === 'denial_code' ? 18 : 14);
          const displayLabel = n.label.length > maxChars ? n.label.slice(0, maxChars - 2) + '...' : n.label;

          ctx.shadowColor = '#000000';
          ctx.shadowBlur = 5;
          ctx.fillStyle = isSelected ? '#ffffff' : (n.type === 'category' ? '#f3f4f6' : '#9ca3af');
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          ctx.fillText(displayLabel, n.x, n.y + r + 3);
          ctx.shadowBlur = 0;
        }
      });

      ctx.restore();
      requestAnimationFrame(draw);
    }

    draw();

    function selectNode(node) {
      selectedNode = node;
      displayNodeDetails(node);

      targetTransform = {
        x: -node.x * transform.scale,
        y: -node.y * transform.scale,
        scale: Math.max(transform.scale, 1.05)
      };
    }

    function selectCategory(catId) {
      const catNode = nodes.find(function(n) { return n.id === catId; });
      if (catNode) {
        selectNode(catNode);
      }
    }

    // Search Box
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

    const btnReset = document.getElementById('btn-reset');
    btnReset.addEventListener('click', function() {
      targetTransform = { x: 0, y: 0, scale: 1.0 };
      selectedNode = null;
      filterQuery = '';
      searchBox.value = '';
    });

    const btnLabels = document.getElementById('btn-labels');
    btnLabels.addEventListener('click', function() {
      showLabels = !showLabels;
      btnLabels.textContent = showLabels ? '🏷️ Labels' : '🏷️ Labels: Off';
      btnLabels.classList.toggle('active', showLabels);
    });

    function displayNodeDetails(node) {
      const badge = document.getElementById('badge-type');
      const title = document.getElementById('node-title');
      const desc = document.getElementById('node-desc');
      const container = document.getElementById('dynamic-sections');

      badge.textContent = node.type.replace('_', ' ').toUpperCase();
      badge.style.background = 'rgba(255, 255, 255, 0.08)';
      badge.style.color = '#e5e7eb';

      title.textContent = node.label;
      desc.textContent = node.description || 'Knowledge graph operational entity.';

      let html = '';

      if (node.type === 'category') {
        const childCodes = links.filter(function(l) { return l.sourceNode === node; }).map(function(l) { return l.targetNode; });
        html += '<div class="section-card"><h4><span>📑</span> Denial Codes (' + childCodes.length + ')</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
        childCodes.forEach(function(c) {
          html += '<div class="sub-item-link" onclick="window.selectNodeById(\\'' + c.id + '\\')"><strong>' + c.label + '</strong><div style="font-size: 11px; color: #6b7280; margin-top: 2px;">' + (c.description || '') + '</div></div>';
        });
        html += '</div></div>';
      }

      if (node.type === 'denial_code') {
        const codeKey = node.properties.code || node.label.split(':')[0].trim();
        const connectedScenarios = nodes.filter(function(n) {
          return n.type === 'scenario' && n.properties && n.properties.code === codeKey;
        });
        html += '<div class="section-card"><h4><span>📂</span> Associated Scenarios (' + connectedScenarios.length + ')</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
        connectedScenarios.forEach(function(s) {
          html += '<div class="sub-item-link" onclick="window.selectNodeById(\\'' + s.id + '\\')"><strong>' + s.label + '</strong><div style="font-size: 11px; color: #6b7280; margin-top: 2px;">' + (s.description || '') + '</div></div>';
        });
        html += '</div></div>';
      }

      if (node.type === 'scenario') {
        const children = links.filter(function(l) { return l.sourceNode === node; }).map(function(l) { return l.targetNode; });
        const inv = children.find(function(c) { return c.type === 'investigation_step'; });
        const form = children.find(function(c) { return c.type === 'form_requirement'; });
        const script = children.find(function(c) { return c.type === 'payer_question'; });
        const act = children.find(function(c) { return c.type === 'action_plan'; });

        if (inv && inv.properties && inv.properties.steps) {
          html += '<div class="section-card"><h4><span>🔍</span> Investigation Checklist</h4>';
          inv.properties.steps.forEach(function(s) {
            html += '<div class="checklist-item">' + s + '</div>';
          });
          html += '</div>';
        }

        if (form && form.properties) {
          html += '<div class="section-card"><h4><span>📋</span> CMS-1500 & Clearinghouse Fields</h4><div style="font-size: 11.5px; color: #d1d5db; line-height: 1.5;"><strong>Form:</strong> ' + (form.properties.form_name || 'CMS-1500') + '<br/><strong>Box/Segment:</strong> <span style="color: #93c5fd; font-weight: 600;">' + (form.properties.box_number || 'N/A') + '</span></div>';
          if (form.properties.required_documents) {
            html += '<div style="margin-top: 6px; font-size: 11px; color: #6b7280;"><strong>Required Attachments:</strong> ' + form.properties.required_documents.join(', ') + '</div>';
          }
          html += '</div>';
        }

        if (script && script.properties) {
          html += '<div class="section-card"><h4><span>📞</span> Payer Call Script Questions</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
          for (let k in script.properties) {
            html += '<div class="script-item"><strong>' + k.toUpperCase() + ':</strong> "' + script.properties[k] + '"</div>';
          }
          html += '</div></div>';
        }

        if (act && act.properties && act.properties.steps) {
          html += '<div class="section-card"><h4><span>⚡</span> Step-by-Step Resolution Playbook</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
          act.properties.steps.forEach(function(s) {
            html += '<div style="font-size: 11.5px; color: #e5e7eb; line-height: 1.4;">✓ ' + s + '</div>';
          });
          html += '</div></div>';
        }

        if (node.properties && node.properties.standard_notes) {
          html += '<div class="section-card"><div style="display: flex; justify-content: space-between; align-items: center;"><h4><span>📝</span> Standard AR Notes</h4><button class="copy-btn" onclick="copyNotes()">Copy Notes</button></div><div class="notes-box" id="ar-notes-text">' + node.properties.standard_notes + '</div></div>';
        }
      }

      container.innerHTML = html || '<div class="hint-box">Select a node in the constellation to inspect its investigation checklist and resolution steps.</div>';
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

    print(f"Obsidian-Style Graph Viewer successfully built at: {out_path} ({len(html_content)} bytes)")

if __name__ == "__main__":
    build_viewer()
