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
  <title>NovaArc RCM — Denial Knowledge Graph Cluster Explorer</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: #12141a;
      color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      overflow: hidden;
      width: 100vw;
      height: 100vh;
      display: flex;
      user-select: none;
    }

    #canvas-container {
      flex: 1;
      position: relative;
      height: 100%;
      min-width: 0;
      background-color: #12141a;
      overflow: hidden;
    }

    canvas {
      display: block;
      width: 100%;
      height: 100%;
      cursor: grab;
    }
    canvas:active { cursor: grabbing; }

    /* Top Floating Header & Filter Controls */
    .top-bar {
      position: absolute;
      top: 16px;
      left: 20px;
      right: 20px;
      display: flex;
      gap: 12px;
      align-items: center;
      z-index: 10;
      pointer-events: none;
    }
    .top-bar > * { pointer-events: auto; }

    .brand-pill {
      background: #1a1e29;
      border: 1px solid #2e384d;
      padding: 8px 18px;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 700;
      color: #e2e8f0;
      display: flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
      letter-spacing: 0.01em;
    }
    .brand-pill .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #3b82f6;
    }

    .search-wrapper {
      position: relative;
      flex: 1;
      max-width: 380px;
    }
    .search-input {
      width: 100%;
      background: #1a1e29;
      border: 1px solid #2e384d;
      padding: 9px 18px 9px 38px;
      border-radius: 9999px;
      color: #fff;
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .search-input:focus {
      border-color: #3b82f6;
      box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
      background: #202634;
    }
    .search-icon {
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: #94a3b8;
      font-size: 13px;
      pointer-events: none;
    }

    .category-pills {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .cat-chip {
      background: #1a1e29;
      border: 1px solid #2e384d;
      padding: 6px 12px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      color: #cbd5e1;
      transition: all 0.15s ease;
    }
    .cat-chip:hover, .cat-chip.active {
      border-color: #94a3b8;
      color: #fff;
      background: #252c3c;
      transform: translateY(-1px);
    }
    .cat-chip .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    /* Floating Center Stats */
    .cluster-stats-hud {
      position: absolute;
      bottom: 20px;
      left: 20px;
      display: flex;
      gap: 8px;
      align-items: center;
      z-index: 10;
    }
    .ctrl-btn {
      background: #1a1e29;
      border: 1px solid #2e384d;
      padding: 7px 13px;
      border-radius: 6px;
      color: #cbd5e1;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    .ctrl-btn:hover {
      background: #242c3d;
      border-color: #64748b;
      color: #fff;
    }
    .ctrl-btn.active {
      background: #1e3a8a;
      border-color: #3b82f6;
      color: #93c5fd;
    }

    .stats-tag {
      background: rgba(18, 20, 26, 0.85);
      border: 1px solid #2e384d;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 11px;
      color: #94a3b8;
      font-weight: 600;
      letter-spacing: 0.02em;
    }

    /* Floating Tooltip */
    #node-tooltip {
      position: absolute;
      display: none;
      pointer-events: none;
      background: #1a1e29;
      border: 1px solid #3b4252;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7);
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 12px;
      color: #fff;
      z-index: 25;
      transform: translate(-50%, -130%);
      white-space: nowrap;
    }
    #node-tooltip .tt-type {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 700;
      margin-bottom: 2px;
    }
    #node-tooltip .tt-title {
      font-weight: 600;
      font-size: 13px;
    }

    /* Detail Inspector Sidebar */
    .sidebar {
      width: 440px;
      height: 100%;
      background: #161a24;
      border-left: 1px solid #252d3d;
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 18px;
      box-shadow: -10px 0 25px rgba(0, 0, 0, 0.5);
      z-index: 20;
      user-select: text;
    }
    .sidebar::-webkit-scrollbar { width: 6px; }
    .sidebar::-webkit-scrollbar-thumb { background: #2a3447; border-radius: 3px; }

    .sidebar-header {
      border-bottom: 1px solid #252d3d;
      padding-bottom: 16px;
    }
    .node-type-badge {
      display: inline-block;
      padding: 3px 9px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }
    .sidebar-title {
      font-size: 19px;
      font-weight: 700;
      color: #f8fafc;
      line-height: 1.35;
    }
    .sidebar-desc {
      font-size: 13px;
      color: #94a3b8;
      line-height: 1.5;
      margin-top: 8px;
    }

    .section-card {
      background: #1b202e;
      border: 1px solid #283347;
      border-radius: 8px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .section-card h4 {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #93c5fd;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .checklist-item {
      font-size: 12px;
      color: #cbd5e1;
      display: flex;
      gap: 8px;
      line-height: 1.45;
    }
    .checklist-item::before {
      content: "•";
      color: #60a5fa;
      font-weight: bold;
    }
    .script-item {
      background: #121620;
      border-left: 3px solid #f472b6;
      padding: 8px 12px;
      border-radius: 0 4px 4px 0;
      font-size: 12px;
      color: #f1f5f9;
      font-style: italic;
      line-height: 1.4;
    }
    .copy-btn {
      background: #2563eb;
      color: #fff;
      border: none;
      padding: 6px 12px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: background 0.15s;
    }
    .copy-btn:hover { background: #1d4ed8; }
    .notes-box {
      background: #0f121a;
      border: 1px solid #252d3d;
      padding: 12px;
      border-radius: 6px;
      font-family: 'Consolas', 'Courier New', monospace;
      font-size: 11px;
      color: #cbd5e1;
      white-space: pre-wrap;
      max-height: 140px;
      overflow-y: auto;
      line-height: 1.45;
    }
    .sub-item-link {
      padding: 10px;
      background: #151a24;
      border: 1px solid #283347;
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
      border-left: 3px solid #3b82f6;
      transition: background 0.15s, border-color 0.15s, transform 0.15s;
    }
    .sub-item-link:hover {
      background: #1f2736;
      border-color: #60a5fa;
      transform: translateX(3px);
    }
    .hint-box {
      font-size: 12px;
      color: #64748b;
      text-align: center;
      margin-top: 20px;
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
        <span class="search-icon">🔍</span>
        <input type="text" id="search-box" class="search-input" placeholder="Search CARC, scenario, modifier (e.g. CO-16, CO-216, auth)..." />
      </div>

      <div class="category-pills" id="category-pills">
        <!-- Category chips rendered dynamically -->
      </div>
    </div>

    <!-- Bottom Controls -->
    <div class="cluster-stats-hud">
      <button class="ctrl-btn" id="btn-reset">🎯 Center Graph</button>
      <button class="ctrl-btn active" id="btn-labels">🏷️ Labels: ON</button>
      <div class="stats-tag" id="hud-stats">""" + f"{len(graph_data['nodes'])} NODES • {len(graph_data['links'])} RELATIONS" + """</div>
    </div>

    <!-- Tooltip -->
    <div id="node-tooltip">
      <div class="tt-type" id="tt-type">Scenario</div>
      <div class="tt-title" id="tt-title">Node Title</div>
    </div>

    <canvas id="graph-canvas"></canvas>
  </div>

  <div class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div>
        <div class="node-type-badge" id="badge-type" style="background: #1e3a8a; color: #93c5fd;">EXPLORER</div>
        <h3 class="sidebar-title" id="node-title">Denial Knowledge Graph</h3>
      </div>
    </div>
    <div class="sidebar-desc" id="node-desc">
      Click on any category cluster or code node to inspect root-cause scenarios, CMS-1500 box mappings, payer call scripts, and step-by-step resolution playbooks.
    </div>

    <div id="dynamic-sections" style="display: flex; flex-direction: column; gap: 14px;">
      <div class="hint-box">
        ✨ <strong>Interactive Controls:</strong><br/>
        • <strong>Left Click + Drag:</strong> Pan network view<br/>
        • <strong>Mouse Wheel:</strong> Zoom in & out<br/>
        • <strong>Hover Node:</strong> Highlight cluster & connections<br/>
        • <strong>Click Node:</strong> Lock focus & open resolution playbook
      </div>
    </div>
  </div>

  <script>
    const graphData = """ + graph_json + """;

    const canvas = document.getElementById('graph-canvas');
    const ctx = canvas.getContext('2d');

    let width = 800;
    let height = 800;

    function resizeCanvas() {
      const container = document.getElementById('canvas-container');
      const w = container ? container.clientWidth : 0;
      const h = container ? container.clientHeight : 0;
      width = canvas.width = Math.max(w || (window.innerWidth - 440), 500);
      height = canvas.height = Math.max(h || window.innerHeight, 500);
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Proper Scientific Community Palettes (Harmonious, Non-Neon, Gephi-Style)
    const CLUSTER_PALETTES = {
      'CAT_MISSING_INFO': {
        primary: '#2563eb',       // Royal Blue
        light: '#60a5fa',
        tint: '#93c5fd',
        line: 'rgba(59, 130, 246, 0.35)'
      },
      'CAT_PRIOR_AUTH': {
        primary: '#059669',       // Deep Mint / Forest Green
        light: '#34d399',
        tint: '#6ee7b7',
        line: 'rgba(16, 185, 129, 0.35)'
      },
      'CAT_TIMELY_FILING': {
        primary: '#dc2626',       // Ruby / Crimson Red
        light: '#f87171',
        tint: '#fca5a5',
        line: 'rgba(239, 68, 68, 0.35)'
      },
      'CAT_COB': {
        primary: '#d97706',       // Amber / Warm Honey
        light: '#fbbf24',
        tint: '#fde68a',
        line: 'rgba(245, 158, 11, 0.35)'
      },
      'CAT_MEDICAL_NECESSITY': {
        primary: '#7c3aed',       // Royal Violet
        light: '#a78bfa',
        tint: '#c4b5fd',
        line: 'rgba(139, 92, 246, 0.35)'
      },
      'CAT_CODING_MODIFIERS': {
        primary: '#0891b2',       // Cerulean / Deep Teal
        light: '#22d3ee',
        tint: '#67e8f9',
        line: 'rgba(6, 182, 212, 0.35)'
      },
      'CAT_DUPLICATE_BUNDLING': {
        primary: '#db2777',       // Deep Rose / Mulberry
        light: '#f472b6',
        tint: '#fbcfe8',
        line: 'rgba(236, 72, 153, 0.35)'
      },
      'CAT_ELIGIBILITY': {
        primary: '#4f46e5',       // Deep Indigo
        light: '#818cf8',
        tint: '#a5b4fc',
        line: 'rgba(99, 102, 241, 0.35)'
      }
    };

    // Category cluster center coordinates (8 well-separated orbital anchor points)
    const CLUSTER_CENTERS = {
      'CAT_MISSING_INFO':       { angle: 0,                   dist: 280 },
      'CAT_PRIOR_AUTH':          { angle: Math.PI * 0.25,      dist: 280 },
      'CAT_TIMELY_FILING':       { angle: Math.PI * 0.5,       dist: 280 },
      'CAT_COB':                 { angle: Math.PI * 0.75,      dist: 280 },
      'CAT_MEDICAL_NECESSITY':   { angle: Math.PI,             dist: 280 },
      'CAT_CODING_MODIFIERS':    { angle: Math.PI * 1.25,      dist: 280 },
      'CAT_DUPLICATE_BUNDLING':  { angle: Math.PI * 1.5,       dist: 280 },
      'CAT_ELIGIBILITY':         { angle: Math.PI * 1.75,      dist: 280 }
    };

    // Build category chips in header
    const catContainer = document.getElementById('category-pills');
    if (graphData.categories) {
      graphData.categories.forEach(function(cat) {
        const pal = CLUSTER_PALETTES[cat.id] || { primary: '#3b82f6' };
        const chip = document.createElement('div');
        chip.className = 'cat-chip';
        chip.innerHTML = '<span class="dot" style="background:' + pal.primary + '"></span>' + cat.name.split(' ')[0];
        chip.title = cat.name;
        chip.addEventListener('click', function() {
          selectCategory(cat.id);
        });
        catContainer.appendChild(chip);
      });
    }

    // Helper to determine node's category ID
    function getNodeCategoryId(node) {
      if (node.type === 'category') return node.id;
      if (node.properties && node.properties.category_id) return node.properties.category_id;
      return null;
    }

    // Initialize Nodes with Community Cluster Layout
    const nodes = graphData.nodes.map(function(n) {
      let catId = getNodeCategoryId(n);
      return Object.assign({}, n, {
        categoryId: catId,
        x: 0, y: 0, vx: 0, vy: 0,
        radius: (n.type === 'category' ? 14 : (n.type === 'denial_code' ? 9 : (n.type === 'scenario' ? 6.5 : 4.5))),
        color: '#94a3b8',
        lineColor: 'rgba(148, 163, 184, 0.25)'
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

    // Propagate category ID down to child scenarios and leaves
    links.forEach(function(l) {
      if (l.sourceNode.categoryId && !l.targetNode.categoryId) {
        l.targetNode.categoryId = l.sourceNode.categoryId;
      }
    });
    // Second pass for leaves
    links.forEach(function(l) {
      if (l.sourceNode.categoryId && !l.targetNode.categoryId) {
        l.targetNode.categoryId = l.sourceNode.categoryId;
      }
    });

    // Assign Proper Non-Neon Palette Colors to all Nodes & Edges based on their cluster
    nodes.forEach(function(n, i) {
      const pal = CLUSTER_PALETTES[n.categoryId] || { primary: '#2563eb', light: '#60a5fa', tint: '#93c5fd', line: 'rgba(59,130,246,0.3)' };
      if (n.type === 'category') {
        n.color = pal.primary;
      } else if (n.type === 'denial_code') {
        n.color = pal.light;
      } else if (n.type === 'scenario') {
        n.color = pal.tint;
      } else {
        n.color = pal.light;
      }
      n.lineColor = pal.line;

      // Position nodes in their cluster neighborhood
      const cluster = CLUSTER_CENTERS[n.categoryId] || { angle: (i / nodes.length) * Math.PI * 2, dist: 250 };
      const cx = Math.cos(cluster.angle) * cluster.dist;
      const cy = Math.sin(cluster.angle) * cluster.dist;

      if (n.type === 'category') {
        n.x = cx;
        n.y = cy;
      } else if (n.type === 'denial_code') {
        const offsetAngle = Math.random() * Math.PI * 2;
        const offsetDist = 50 + Math.random() * 60;
        n.x = cx + Math.cos(offsetAngle) * offsetDist;
        n.y = cy + Math.sin(offsetAngle) * offsetDist;
      } else {
        const offsetAngle = Math.random() * Math.PI * 2;
        const offsetDist = 90 + Math.random() * 85;
        n.x = cx + Math.cos(offsetAngle) * offsetDist;
        n.y = cy + Math.sin(offsetAngle) * offsetDist;
      }
    });

    // Assign line colors based on source cluster
    links.forEach(function(l) {
      l.color = l.sourceNode.lineColor || 'rgba(148, 163, 184, 0.25)';
    });

    // Run Force Relaxation to create organic community clusters
    for (let step = 0; step < 90; step++) {
      // Repulsion between all nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          let dx = b.x - a.x;
          let dy = b.y - a.y;
          let dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const minDist = (a.radius + b.radius) * 4.0;
          if (dist < minDist) {
            const force = (minDist - dist) / dist * 0.25;
            const fx = dx * force;
            const fy = dy * force;
            if (a.type !== 'category') { a.vx -= fx; a.vy -= fy; }
            if (b.type !== 'category') { b.vx += fx; b.vy += fy; }
          }
        }
      }

      // Spring attraction along links
      links.forEach(function(l) {
        const a = l.sourceNode;
        const b = l.targetNode;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const targetDist = 35 + (a.radius + b.radius);
        const force = (dist - targetDist) * 0.035;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        if (a.type !== 'category') { a.vx += fx; a.vy += fy; }
        if (b.type !== 'category') { b.vx -= fx; b.vy -= fy; }
      });

      // Gravity toward cluster center
      nodes.forEach(function(n) {
        if (n.type === 'category') return;
        const cluster = CLUSTER_CENTERS[n.categoryId];
        if (cluster) {
          const cx = Math.cos(cluster.angle) * cluster.dist;
          const cy = Math.sin(cluster.angle) * cluster.dist;
          n.vx += (cx - n.x) * 0.008;
          n.vy += (cy - n.y) * 0.008;
        }
        n.x += n.vx;
        n.y += n.vy;
        n.vx *= 0.75;
        n.vy *= 0.75;
      });
    }

    // Pan & Zoom Camera State
    let transform = { x: 0, y: 0, scale: 0.95 };
    let isDragging = false;
    let draggedNode = null;
    let startPan = { x: 0, y: 0 };
    let hoveredNode = null;
    let selectedNode = null;
    let filterQuery = '';
    let showLabels = true;

    // Smooth camera target
    let targetTransform = null;

    canvas.addEventListener('mousedown', function(e) {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - width / 2 - transform.x) / transform.scale;
      const mouseY = (e.clientY - rect.top - height / 2 - transform.y) / transform.scale;

      // Check click on node
      for (let i = nodes.length - 1; i >= 0; i--) {
        const n = nodes[i];
        const dx = mouseX - n.x;
        const dy = mouseY - n.y;
        const hitR = Math.max(n.radius * 1.6, 10);
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
        // Hover detection
        let found = null;
        for (let i = nodes.length - 1; i >= 0; i--) {
          const n = nodes[i];
          const dx = mouseX - n.x;
          const dy = mouseY - n.y;
          const hitR = Math.max(n.radius * 1.5, 9);
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
      transform.scale = Math.max(0.35, Math.min(3.2, transform.scale * zoomFactor));
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

    // Render Loop
    function draw() {
      if (targetTransform) {
        transform.x += (targetTransform.x - transform.x) * 0.1;
        transform.y += (targetTransform.y - transform.y) * 0.1;
        transform.scale += (targetTransform.scale - transform.scale) * 0.1;
        if (Math.abs(targetTransform.x - transform.x) < 0.5 &&
            Math.abs(targetTransform.y - transform.y) < 0.5 &&
            Math.abs(targetTransform.scale - transform.scale) < 0.005) {
          targetTransform = null;
        }
      }

      ctx.clearRect(0, 0, width, height);

      ctx.save();
      ctx.translate(width / 2 + transform.x, height / 2 + transform.y);
      ctx.scale(transform.scale, transform.scale);

      const activeFocus = selectedNode || hoveredNode;

      // 1. Draw Links (Matching their source cluster community color)
      links.forEach(function(l) {
        const a = l.sourceNode;
        const b = l.targetNode;

        const isConnected = activeFocus && (a === activeFocus || b === activeFocus);
        const isDimmed = activeFocus && !isConnected;

        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);

        if (isConnected) {
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2.2;
          ctx.globalAlpha = 0.95;
        } else if (isDimmed) {
          ctx.strokeStyle = l.color;
          ctx.lineWidth = 0.6;
          ctx.globalAlpha = 0.08;
        } else {
          ctx.strokeStyle = l.color;
          ctx.lineWidth = 0.9;
          ctx.globalAlpha = 0.35;
        }
        ctx.stroke();
      });
      ctx.globalAlpha = 1.0;

      // 2. Draw Nodes (Proper Solid Matte Orbs with Crisp Stroke)
      nodes.forEach(function(n) {
        const isSelected = n === selectedNode;
        const isHovered = n === hoveredNode;
        const isConnected = activeFocus && (
          n === activeFocus ||
          links.some(function(l) {
            return (l.sourceNode === activeFocus && l.targetNode === n) ||
                   (l.targetNode === activeFocus && l.sourceNode === n);
          })
        );
        const isDimmed = activeFocus && !isConnected;
        const isMatch = filterQuery && (
          n.label.toLowerCase().indexOf(filterQuery) !== -1 ||
          (n.description && n.description.toLowerCase().indexOf(filterQuery) !== -1)
        );

        const r = n.radius * (isSelected ? 1.4 : (isHovered ? 1.25 : 1.0));

        // Soft outer focus ring if selected or hovered
        if (isSelected || isHovered) {
          ctx.beginPath();
          ctx.arc(n.x, n.y, r + 5, 0, Math.PI * 2);
          ctx.fillStyle = n.color;
          ctx.globalAlpha = 0.22;
          ctx.fill();
          ctx.globalAlpha = 1.0;
        }

        // Node Body
        ctx.beginPath();
        ctx.arc(n.x, n.y, Math.max(2, r), 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.globalAlpha = isDimmed ? 0.2 : 1.0;
        ctx.fill();

        // Node Rim
        ctx.strokeStyle = isSelected ? '#ffffff' : (isHovered ? '#f1f5f9' : 'rgba(0, 0, 0, 0.45)');
        ctx.lineWidth = isSelected ? 2.5 : (isHovered ? 1.8 : 0.8);
        ctx.stroke();
        ctx.globalAlpha = 1.0;

        // Clean Matte Typography (with contrast halo)
        const shouldShowLabel = showLabels && (
          isSelected || isHovered || isMatch || isConnected ||
          n.type === 'category' ||
          (n.type === 'denial_code' && transform.scale > 0.6) ||
          (n.type === 'scenario' && transform.scale > 1.2)
        );

        if (shouldShowLabel && !isDimmed) {
          const fontSize = n.type === 'category' ? 12 : (n.type === 'denial_code' ? 11 : 10);
          ctx.font = (n.type === 'category' || isSelected ? '700 ' : '500 ') + fontSize + 'px -apple-system, sans-serif';

          const maxChars = n.type === 'category' ? 28 : (n.type === 'denial_code' ? 20 : 16);
          const displayLabel = n.label.length > maxChars ? n.label.slice(0, maxChars - 2) + '...' : n.label;

          // Dark halo behind text for readability
          ctx.shadowColor = '#12141a';
          ctx.shadowBlur = 4;
          ctx.fillStyle = isSelected ? '#ffffff' : (n.type === 'category' ? '#f8fafc' : '#cbd5e1');
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

    // Select and inspect a node
    function selectNode(node) {
      selectedNode = node;
      displayNodeDetails(node);

      // Smooth pan to center selected node
      targetTransform = {
        x: -node.x * transform.scale,
        y: -node.y * transform.scale,
        scale: Math.max(transform.scale, 1.0)
      };
    }

    // Filter by Category
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

    // Control Buttons
    const btnReset = document.getElementById('btn-reset');
    btnReset.addEventListener('click', function() {
      targetTransform = { x: 0, y: 0, scale: 0.95 };
      selectedNode = null;
      filterQuery = '';
      searchBox.value = '';
    });

    const btnLabels = document.getElementById('btn-labels');
    btnLabels.addEventListener('click', function() {
      showLabels = !showLabels;
      btnLabels.textContent = showLabels ? '🏷️ Labels: ON' : '🏷️ Labels: OFF';
      btnLabels.classList.toggle('active', showLabels);
    });

    // Sidebar Detail Renderer
    function displayNodeDetails(node) {
      const badge = document.getElementById('badge-type');
      const title = document.getElementById('node-title');
      const desc = document.getElementById('node-desc');
      const container = document.getElementById('dynamic-sections');

      badge.textContent = node.type.replace('_', ' ').toUpperCase();
      badge.style.background = node.color;
      badge.style.color = '#ffffff';

      title.textContent = node.label;
      desc.textContent = node.description || 'Knowledge graph operational entity.';

      let html = '';

      // If Category: show child codes
      if (node.type === 'category') {
        const childCodes = links.filter(function(l) { return l.sourceNode === node; }).map(function(l) { return l.targetNode; });
        html += '<div class="section-card"><h4><span>📑</span> Denial Codes in Category (' + childCodes.length + ')</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
        childCodes.forEach(function(c) {
          html += '<div class="sub-item-link" onclick="window.selectNodeById(\\'' + c.id + '\\')"><strong>' + c.label + '</strong><div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">' + (c.description || '') + '</div></div>';
        });
        html += '</div></div>';
      }

      // If Denial Code: show scenarios
      if (node.type === 'denial_code') {
        const codeKey = node.properties.code || node.label.split(':')[0].trim();
        const connectedScenarios = nodes.filter(function(n) {
          return n.type === 'scenario' && n.properties && n.properties.code === codeKey;
        });
        html += '<div class="section-card"><h4><span>📂</span> Associated Operational Scenarios (' + connectedScenarios.length + ')</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
        connectedScenarios.forEach(function(s) {
          html += '<div class="sub-item-link" onclick="window.selectNodeById(\\'' + s.id + '\\')"><strong>' + s.label + '</strong><div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">' + (s.description || '') + '</div></div>';
        });
        html += '</div></div>';
      }

      // If Scenario: show investigation, CMS-1500, phone questions, and action playbook
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
          html += '<div class="section-card"><h4><span>📋</span> CMS-1500 & Clearinghouse Fields</h4><div style="font-size: 12px; color: #f1f5f9; line-height: 1.5;"><strong>Form:</strong> ' + (form.properties.form_name || 'CMS-1500') + '<br/><strong>Box/Segment:</strong> <span style="color: #60a5fa; font-weight: bold;">' + (form.properties.box_number || 'N/A') + '</span></div>';
          if (form.properties.required_documents) {
            html += '<div style="margin-top: 6px; font-size: 11px; color: #94a3b8;"><strong>Required Attachments:</strong> ' + form.properties.required_documents.join(', ') + '</div>';
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
            html += '<div style="font-size: 12px; color: #a7f3d0; line-height: 1.4;">✓ ' + s + '</div>';
          });
          html += '</div></div>';
        }

        if (node.properties && node.properties.standard_notes) {
          html += '<div class="section-card"><div style="display: flex; justify-content: space-between; align-items: center;"><h4><span>📝</span> Standard AR Call Notes</h4><button class="copy-btn" onclick="copyNotes()">Copy Notes</button></div><div class="notes-box" id="ar-notes-text">' + node.properties.standard_notes + '</div></div>';
        }
      }

      container.innerHTML = html || '<div class="hint-box">Cluster node selected. Pan or drag to inspect neighborhood.</div>';
    }

    window.copyNotes = function() {
      const box = document.getElementById('ar-notes-text');
      if (box) {
        navigator.clipboard.writeText(box.innerText);
        const btn = document.querySelector('.copy-btn');
        if (btn) {
          btn.textContent = '✓ Copied!';
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

    print(f"Cluster Graph Viewer successfully built at: {out_path} ({len(html_content)} bytes)")

if __name__ == "__main__":
    build_viewer()
