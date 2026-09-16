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
  <title>NovaArc RCM — Denial Knowledge Graph 3D Sphere</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: #030712;
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
      background: radial-gradient(circle at 50% 50%, #0c1427 0%, #030712 100%);
      overflow: hidden;
    }

    canvas {
      display: block;
      width: 100%;
      height: 100%;
      cursor: grab;
    }
    canvas:active { cursor: grabbing; }

    /* Top Floating Header & Search */
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
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(56, 189, 248, 0.35);
      backdrop-filter: blur(12px);
      padding: 8px 18px;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 700;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 4px 25px rgba(0, 0, 0, 0.6), 0 0 15px rgba(56, 189, 248, 0.15);
      letter-spacing: 0.02em;
    }
    .brand-pill .pulse-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #00f0ff;
      box-shadow: 0 0 12px #00f0ff, 0 0 20px #00f0ff;
      animation: pulseGlow 2s infinite alternate;
    }
    @keyframes pulseGlow {
      from { opacity: 0.6; transform: scale(0.9); }
      to { opacity: 1; transform: scale(1.15); }
    }

    .search-wrapper {
      position: relative;
      flex: 1;
      max-width: 420px;
    }
    .search-input {
      width: 100%;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(148, 163, 184, 0.25);
      backdrop-filter: blur(12px);
      padding: 9px 18px 9px 40px;
      border-radius: 9999px;
      color: #fff;
      font-size: 13px;
      outline: none;
      transition: all 0.25s ease;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }
    .search-input:focus {
      border-color: #38bdf8;
      box-shadow: 0 0 15px rgba(56, 189, 248, 0.35);
      background: rgba(15, 23, 42, 0.95);
    }
    .search-icon {
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: #94a3b8;
      font-size: 14px;
      pointer-events: none;
    }

    .category-pills {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .cat-chip {
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid rgba(148, 163, 184, 0.2);
      backdrop-filter: blur(8px);
      padding: 6px 12px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      color: #cbd5e1;
      transition: all 0.2s;
    }
    .cat-chip:hover, .cat-chip.active {
      border-color: #38bdf8;
      color: #fff;
      background: rgba(30, 58, 138, 0.4);
      transform: translateY(-1px);
    }
    .cat-chip .dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
    }

    /* Floating Center HUD inside Sphere */
    .sphere-center-hud {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      pointer-events: none;
      text-align: center;
      opacity: 0.85;
      transition: opacity 0.3s;
      z-index: 2;
    }
    .sphere-center-hud h2 {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      background: linear-gradient(135deg, #ffffff 0%, #38bdf8 50%, #818cf8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 35px rgba(56, 189, 248, 0.5);
    }
    .sphere-center-hud p {
      font-size: 11px;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: #94a3b8;
      margin-top: 4px;
      font-weight: 600;
    }
    .sphere-center-hud .stats-badge {
      display: inline-block;
      margin-top: 8px;
      padding: 3px 10px;
      border-radius: 9999px;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      font-size: 10px;
      font-weight: 700;
      color: #7dd3fc;
    }

    /* Bottom Control Bar */
    .bottom-bar {
      position: absolute;
      bottom: 20px;
      left: 20px;
      display: flex;
      gap: 10px;
      align-items: center;
      z-index: 10;
    }
    .ctrl-btn {
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(148, 163, 184, 0.25);
      backdrop-filter: blur(12px);
      padding: 8px 14px;
      border-radius: 8px;
      color: #e2e8f0;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .ctrl-btn:hover {
      background: rgba(30, 41, 59, 0.9);
      border-color: #38bdf8;
      color: #38bdf8;
    }
    .ctrl-btn.active {
      background: rgba(14, 165, 233, 0.2);
      border-color: #0284c7;
      color: #38bdf8;
    }

    /* 3D Floating Tooltip */
    #node-tooltip {
      position: absolute;
      display: none;
      pointer-events: none;
      background: rgba(11, 17, 32, 0.95);
      border: 1px solid rgba(56, 189, 248, 0.4);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.8), 0 0 15px rgba(56, 189, 248, 0.2);
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 12px;
      color: #fff;
      z-index: 25;
      transform: translate(-50%, -130%);
      white-space: nowrap;
      transition: opacity 0.15s;
    }
    #node-tooltip .tt-type {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #38bdf8;
      font-weight: 700;
      margin-bottom: 2px;
    }
    #node-tooltip .tt-title {
      font-weight: 700;
      font-size: 13px;
    }

    /* Detail Inspector Sidebar */
    .sidebar {
      width: 440px;
      height: 100%;
      background: #090e1a;
      border-left: 1px solid rgba(148, 163, 184, 0.15);
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 18px;
      box-shadow: -15px 0 35px rgba(0, 0, 0, 0.7);
      z-index: 20;
      user-select: text;
    }
    .sidebar::-webkit-scrollbar { width: 6px; }
    .sidebar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }

    .sidebar-header {
      border-bottom: 1px solid rgba(148, 163, 184, 0.15);
      padding-bottom: 16px;
    }
    .node-type-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 10px;
      box-shadow: 0 0 10px currentColor;
    }
    .sidebar-title {
      font-size: 20px;
      font-weight: 800;
      color: #f8fafc;
      line-height: 1.3;
    }
    .sidebar-desc {
      font-size: 13px;
      color: #94a3b8;
      line-height: 1.5;
      margin-top: 8px;
    }

    .section-card {
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid rgba(148, 163, 184, 0.18);
      border-radius: 10px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .section-card h4 {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #38bdf8;
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
      color: #38bdf8;
      font-weight: bold;
    }
    .script-item {
      background: rgba(2, 6, 23, 0.6);
      border-left: 3px solid #ec4899;
      padding: 8px 12px;
      border-radius: 0 6px 6px 0;
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
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s;
    }
    .copy-btn:hover { background: #1d4ed8; }
    .notes-box {
      background: #030712;
      border: 1px solid #1e293b;
      padding: 12px;
      border-radius: 8px;
      font-family: 'Consolas', 'Courier New', monospace;
      font-size: 11px;
      color: #94a3b8;
      white-space: pre-wrap;
      max-height: 140px;
      overflow-y: auto;
      line-height: 1.45;
    }
    .sub-item-link {
      padding: 10px;
      background: rgba(15, 23, 42, 0.65);
      border: 1px solid rgba(148, 163, 184, 0.12);
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
      border-left: 3px solid #34d399;
      transition: all 0.2s;
    }
    .sub-item-link:hover {
      background: rgba(30, 41, 59, 0.8);
      border-color: #38bdf8;
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
        <span class="pulse-dot"></span>
        <span>NovaArc Knowledge Sphere</span>
      </div>

      <div class="search-wrapper">
        <span class="search-icon">🔍</span>
        <input type="text" id="search-box" class="search-input" placeholder="Search CARC, scenario, modifier (e.g. CO-16, 25, auth, NPI)..." />
      </div>

      <div class="category-pills" id="category-pills">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- Center HUD inside 3D Sphere -->
    <div class="sphere-center-hud" id="sphere-hud">
      <h2>NovaArc RCM</h2>
      <p>Denial Intelligence Sphere</p>
      <div class="stats-badge" id="hud-stats">""" + f"{len(graph_data['nodes'])} NODES • {len(graph_data['links'])} RELATIONS" + """</div>
    </div>

    <!-- Bottom Controls -->
    <div class="bottom-bar">
      <button class="ctrl-btn active" id="btn-rotate">⏸ Pause Rotation</button>
      <button class="ctrl-btn" id="btn-reset">🎯 Reset View</button>
      <button class="ctrl-btn active" id="btn-labels">🏷️ Labels: ON</button>
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
        <div class="node-type-badge" id="badge-type" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8;">DENIAL INTELLIGENCE SPHERE</div>
        <h3 class="sidebar-title" id="node-title">Knowledge Graph 3D Sphere</h3>
      </div>
    </div>
    <div class="sidebar-desc" id="node-desc">
      Click and drag the glowing 3D sphere to rotate. Click any glowing orb to inspect detailed denial root-cause scenarios, CMS-1500 box mappings, payer call scripts, and step-by-step resolution playbooks.
    </div>

    <div id="dynamic-sections" style="display: flex; flex-direction: column; gap: 14px;">
      <div class="hint-box">
        ✨ <strong>Interactive Controls:</strong><br/>
        • <strong>Left Click + Drag:</strong> Rotate sphere in 3D<br/>
        • <strong>Mouse Wheel:</strong> Zoom in & out<br/>
        • <strong>Click Node:</strong> Lock camera and open clinical/operational playbook
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

    // Color definitions per type
    const TYPE_COLORS = {
      category: '#38bdf8',           // Neon Cyan
      denial_code: '#60a5fa',        // Electric Sky Blue
      scenario: '#34d399',           // Vibrant Mint/Green
      investigation_step: '#fbbf24', // Amber Yellow
      payer_question: '#f43f5e',     // Bright Coral/Pink
      form_requirement: '#c084fc',   // Electric Purple
      action_plan: '#2dd4bf'         // Bright Teal
    };

    // Category anchor angles on sphere (8 octahedral/equatorial points)
    const CAT_ANCHORS = {
      'CAT_MISSING_INFO': { phi: Math.PI * 0.35, theta: 0 },
      'CAT_PRIOR_AUTH': { phi: Math.PI * 0.35, theta: Math.PI * 0.5 },
      'CAT_TIMELY_FILING': { phi: Math.PI * 0.35, theta: Math.PI },
      'CAT_COB': { phi: Math.PI * 0.35, theta: Math.PI * 1.5 },
      'CAT_MEDICAL_NECESSITY': { phi: Math.PI * 0.65, theta: Math.PI * 0.25 },
      'CAT_CODING_MODIFIERS': { phi: Math.PI * 0.65, theta: Math.PI * 0.75 },
      'CAT_DUPLICATE_BUNDLING': { phi: Math.PI * 0.65, theta: Math.PI * 1.25 },
      'CAT_ELIGIBILITY': { phi: Math.PI * 0.65, theta: Math.PI * 1.75 }
    };

    // Build category chips in header
    const catContainer = document.getElementById('category-pills');
    if (graphData.categories) {
      graphData.categories.forEach(function(cat) {
        const chip = document.createElement('div');
        chip.className = 'cat-chip';
        chip.innerHTML = '<span class="dot" style="background:' + (cat.color || '#38bdf8') + '; box-shadow: 0 0 6px ' + (cat.color || '#38bdf8') + '"></span>' + cat.name.split(' ')[0];
        chip.title = cat.name;
        chip.addEventListener('click', function() {
          selectCategory(cat.id);
        });
        catContainer.appendChild(chip);
      });
    }

    // Sphere Radius
    const SPHERE_RADIUS = 280;

    // Initialize 3D Node positions on spherical shell
    const nodes = graphData.nodes.map(function(n, i) {
      let phi, theta;
      let r = SPHERE_RADIUS + (Math.random() - 0.5) * 40;

      if (n.type === 'category') {
        const anchor = CAT_ANCHORS[n.id] || { phi: Math.PI * 0.5, theta: (i / 8) * Math.PI * 2 };
        phi = anchor.phi;
        theta = anchor.theta;
        r = SPHERE_RADIUS + 15;
      } else {
        // Fibonacci sphere distribution with cluster gravitation
        const k = i + 0.5;
        phi = Math.acos(1 - 2 * k / graphData.nodes.length);
        theta = Math.PI * (1 + Math.sqrt(5)) * k;
      }

      // Convert spherical (r, phi, theta) to Cartesian (x, y, z)
      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.cos(phi);
      const z = r * Math.sin(phi) * Math.sin(theta);

      return Object.assign({}, n, {
        x: x, y: y, z: z,
        baseX: x, baseY: y, baseZ: z,
        radius: n.radius || (n.type === 'category' ? 14 : (n.type === 'denial_code' ? 10 : (n.type === 'scenario' ? 8 : 6))),
        color: TYPE_COLORS[n.type] || n.color || '#38bdf8',
        projX: 0, projY: 0, projScale: 1
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

    // Attract nodes toward connected neighbors in 3D to form organic constellations
    for (let step = 0; step < 60; step++) {
      links.forEach(function(l) {
        const a = l.sourceNode;
        const b = l.targetNode;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dz = b.z - a.z;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
        const factor = (dist - 70) * 0.015;
        if (a.type !== 'category') {
          a.x += (dx / dist) * factor;
          a.y += (dy / dist) * factor;
          a.z += (dz / dist) * factor;
        }
        if (b.type !== 'category') {
          b.x -= (dx / dist) * factor;
          b.y -= (dy / dist) * factor;
          b.z -= (dz / dist) * factor;
        }
      });

      // Keep them constrained to spherical shell
      nodes.forEach(function(n) {
        const d = Math.sqrt(n.x * n.x + n.y * n.y + n.z * n.z) || 1;
        const targetR = SPHERE_RADIUS + (n.type === 'category' ? 20 : (n.type === 'scenario' ? -10 : 0));
        n.x = (n.x / d) * targetR;
        n.y = (n.y / d) * targetR;
        n.z = (n.z / d) * targetR;
      });
    }

    // 150 Background Cosmic Stars
    const cosmicStars = [];
    for (let i = 0; i < 180; i++) {
      const starR = 500 + Math.random() * 400;
      const sPhi = Math.acos(1 - 2 * Math.random());
      const sTheta = Math.random() * Math.PI * 2;
      cosmicStars.push({
        x: starR * Math.sin(sPhi) * Math.cos(sTheta),
        y: starR * Math.cos(sPhi),
        z: starR * Math.sin(sPhi) * Math.sin(sTheta),
        size: Math.random() * 1.6 + 0.5,
        alpha: Math.random() * 0.7 + 0.2
      });
    }

    // 3D Camera and Rotation State
    let rotationX = 0.25;  // Pitch
    let rotationY = 0.5;   // Yaw
    let velX = 0;
    let velY = 0.0025;      // Auto-rotation speed
    let autoRotate = true;
    let showLabels = true;
    let zoom = 1.0;
    const CAMERA_DISTANCE = 750;
    const FOV = 550;

    let isDragging = false;
    let lastMouseX = 0;
    let lastMouseY = 0;
    let hoveredNode = null;
    let selectedNode = null;
    let filterQuery = '';

    // Smooth focus animation target
    let targetRotX = null;
    let targetRotY = null;

    // Mouse & Touch Interaction
    canvas.addEventListener('mousedown', function(e) {
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      // Check click on node
      const clicked = findNodeAtScreen(mouseX, mouseY);
      if (clicked) {
        selectNode(clicked);
        return;
      }

      isDragging = true;
      lastMouseX = e.clientX;
      lastMouseY = e.clientY;
      velX = 0;
      velY = 0;
      targetRotX = null;
      targetRotY = null;
    });

    window.addEventListener('mousemove', function(e) {
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      if (isDragging) {
        const dx = e.clientX - lastMouseX;
        const dy = e.clientY - lastMouseY;
        velY = dx * 0.005;
        velX = dy * 0.005;
        rotationY += velY;
        rotationX += velX;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
      } else {
        // Hover detection
        const prevHovered = hoveredNode;
        hoveredNode = findNodeAtScreen(mouseX, mouseY);
        if (hoveredNode !== prevHovered) {
          updateTooltip(hoveredNode, mouseX, mouseY);
        }
      }
    });

    window.addEventListener('mouseup', function() {
      isDragging = false;
    });

    canvas.addEventListener('wheel', function(e) {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      zoom = Math.max(0.45, Math.min(2.8, zoom * zoomFactor));
    });

    function findNodeAtScreen(mx, my) {
      // Find closest node in front (depth sorted)
      let closest = null;
      let minDistance = 14;

      for (let i = nodes.length - 1; i >= 0; i--) {
        const n = nodes[i];
        if (n.projZ < -150) continue; // Skip far back
        const dx = mx - n.projX;
        const dy = my - n.projY;
        const hitRadius = Math.max(n.projRadius * 1.5, 12);
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < hitRadius && dist < minDistance) {
          minDistance = dist;
          closest = n;
        }
      }
      return closest;
    }

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

    // Camera 3D Math & Project
    function project3D(x, y, z, rotX, rotY) {
      // Yaw (Y-axis rotation)
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const x1 = x * cosY - z * sinY;
      const z1 = z * cosY + x * sinY;

      // Pitch (X-axis rotation)
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);
      const y2 = y * cosX - z1 * sinX;
      const z2 = z1 * cosX + y * sinX;

      // Perspective Projection
      const k = (FOV / (CAMERA_DISTANCE - z2)) * zoom;
      const screenX = width / 2 + x1 * k;
      const screenY = height / 2 + y2 * k;

      return {
        x: screenX,
        y: screenY,
        z: z2,
        scale: k
      };
    }

    // Main 3D Render Loop
    function render() {
      // Handle Auto-rotation & Momentum
      if (targetRotX !== null && targetRotY !== null) {
        // Smooth camera lerp to focused node
        rotationX += (targetRotX - rotationX) * 0.08;
        rotationY += (targetRotY - rotationY) * 0.08;
        if (Math.abs(targetRotX - rotationX) < 0.002 && Math.abs(targetRotY - rotationY) < 0.002) {
          targetRotX = null;
          targetRotY = null;
        }
      } else if (!isDragging) {
        if (autoRotate) {
          velY = 0.0022;
        }
        rotationY += velY;
        rotationX += velX;
        velX *= 0.94;
        if (!autoRotate) velY *= 0.94;
      }

      ctx.clearRect(0, 0, width, height);

      // 1. Draw Cosmic Star Dust
      ctx.save();
      cosmicStars.forEach(function(s) {
        const p = project3D(s.x, s.y, s.z, rotationX, rotationY);
        if (p.z > -CAMERA_DISTANCE + 50) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, s.size * Math.max(0.5, p.scale), 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(255, 255, 255, ' + (s.alpha * Math.min(1, Math.max(0.1, (p.z + 500) / 1000))) + ')';
          ctx.fill();
        }
      });
      ctx.restore();

      // 2. Project Nodes
      nodes.forEach(function(n) {
        const p = project3D(n.x, n.y, n.z, rotationX, rotationY);
        n.projX = p.x;
        n.projY = p.y;
        n.projZ = p.z;
        n.projScale = p.scale;
        n.projRadius = Math.max(2, n.radius * p.scale);
      });

      // 3. Draw Links with Depth Fading
      links.forEach(function(l) {
        const a = l.sourceNode;
        const b = l.targetNode;
        const avgZ = (a.projZ + b.projZ) / 2;

        const isHighlighted = (selectedNode && (a === selectedNode || b === selectedNode)) ||
                              (hoveredNode && (a === hoveredNode || b === hoveredNode));

        // Depth alpha factor
        let baseAlpha = (avgZ + SPHERE_RADIUS) / (SPHERE_RADIUS * 2);
        baseAlpha = Math.max(0.04, Math.min(0.85, baseAlpha));

        ctx.beginPath();
        ctx.moveTo(a.projX, a.projY);
        ctx.lineTo(b.projX, b.projY);

        if (isHighlighted) {
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.9)';
          ctx.lineWidth = 2.4;
          ctx.shadowColor = '#00f0ff';
          ctx.shadowBlur = 10;
        } else {
          ctx.strokeStyle = 'rgba(100, 149, 237, ' + (baseAlpha * 0.35) + ')';
          ctx.lineWidth = Math.max(0.5, 1 * ((a.projScale + b.projScale) / 2));
          ctx.shadowBlur = 0;
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
      });

      // 4. Sort Nodes by Depth (Z-buffer rendering)
      const sortedNodes = nodes.slice().sort(function(a, b) {
        return a.projZ - b.projZ;
      });

      // 5. Draw Glowing Sphere Nodes
      sortedNodes.forEach(function(n) {
        const isSelected = n === selectedNode;
        const isHovered = n === hoveredNode;
        const isMatch = filterQuery && (
          n.label.toLowerCase().indexOf(filterQuery) !== -1 ||
          (n.description && n.description.toLowerCase().indexOf(filterQuery) !== -1)
        );

        // Alpha calculation based on depth
        let depthAlpha = (n.projZ + SPHERE_RADIUS) / (SPHERE_RADIUS * 2);
        depthAlpha = Math.max(0.2, Math.min(1.0, depthAlpha));

        const r = n.projRadius * (isSelected ? 1.6 : (isHovered ? 1.4 : 1.0));

        // Outer Glow Halo
        if (isSelected || isHovered || isMatch || n.type === 'category') {
          const glowR = r * (isSelected ? 3.5 : 2.5);
          const glowGrad = ctx.createRadialGradient(n.projX, n.projY, r * 0.3, n.projX, n.projY, glowR);
          glowGrad.addColorStop(0, n.color);
          glowGrad.addColorStop(1, 'rgba(0,0,0,0)');

          ctx.beginPath();
          ctx.arc(n.projX, n.projY, glowR, 0, Math.PI * 2);
          ctx.fillStyle = glowGrad;
          ctx.globalAlpha = isSelected ? 0.9 : 0.45;
          ctx.fill();
          ctx.globalAlpha = 1.0;
        }

        // Core Node Orb
        ctx.beginPath();
        ctx.arc(n.projX, n.projY, Math.max(2, r), 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.shadowColor = n.color;
        ctx.shadowBlur = isSelected ? 20 : (isHovered ? 14 : 6);
        ctx.globalAlpha = isSelected ? 1.0 : depthAlpha;
        ctx.fill();
        ctx.globalAlpha = 1.0;
        ctx.shadowBlur = 0;

        // White Rim Highlight
        ctx.strokeStyle = isSelected ? '#ffffff' : 'rgba(255, 255, 255, ' + (depthAlpha * 0.6) + ')';
        ctx.lineWidth = isSelected ? 2.5 : 1;
        ctx.stroke();

        // Node Labels in 3D
        const shouldShowLabel = showLabels && (
          isSelected || isHovered || isMatch ||
          n.type === 'category' ||
          (n.type === 'denial_code' && n.projZ > 50) ||
          (n.projZ > 120 && n.type === 'scenario')
        );

        if (shouldShowLabel) {
          const fontSize = Math.max(10, Math.round(11 * n.projScale));
          ctx.font = (isSelected || n.type === 'category' ? 'bold ' : '500 ') + fontSize + 'px -apple-system, sans-serif';
          ctx.fillStyle = isSelected ? '#38bdf8' : (n.projZ > 0 ? '#f8fafc' : 'rgba(203, 213, 225, ' + depthAlpha + ')');
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';

          const maxChars = n.type === 'category' ? 30 : 20;
          const displayLabel = n.label.length > maxChars ? n.label.slice(0, maxChars - 2) + '...' : n.label;
          ctx.fillText(displayLabel, n.projX, n.projY + r + 4);
        }
      });

      requestAnimationFrame(render);
    }

    // Trigger Initial Render
    render();

    // Select and inspect a node
    function selectNode(node) {
      selectedNode = node;
      displayNodeDetails(node);

      // Rotate sphere so selected node faces directly towards camera (+Z)
      // Vector: (node.x, node.y, node.z)
      // We want this vector after yaw & pitch to align with (0, 0, +R)
      const targetYaw = -Math.atan2(node.x, node.z);
      const hyp = Math.sqrt(node.x * node.x + node.z * node.z);
      const targetPitch = Math.atan2(node.y, hyp);

      targetRotX = targetPitch;
      targetRotY = targetYaw;
      autoRotate = false;
      document.getElementById('btn-rotate').textContent = '▶ Resume Rotation';
      document.getElementById('btn-rotate').classList.remove('active');
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
    const btnRotate = document.getElementById('btn-rotate');
    btnRotate.addEventListener('click', function() {
      autoRotate = !autoRotate;
      btnRotate.textContent = autoRotate ? '⏸ Pause Rotation' : '▶ Resume Rotation';
      btnRotate.classList.toggle('active', autoRotate);
      if (autoRotate) {
        targetRotX = null;
        targetRotY = null;
      }
    });

    const btnReset = document.getElementById('btn-reset');
    btnReset.addEventListener('click', function() {
      targetRotX = 0.25;
      targetRotY = 0.5;
      zoom = 1.0;
      selectedNode = null;
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
      badge.style.background = 'rgba(' + hexToRgb(node.color) + ', 0.2)';
      badge.style.borderColor = node.color;
      badge.style.color = node.color;

      title.textContent = node.label;
      desc.textContent = node.description || 'Knowledge graph celestial entity.';

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
          html += '<div class="section-card"><h4><span>📋</span> CMS-1500 & Clearinghouse Fields</h4><div style="font-size: 12px; color: #f1f5f9; line-height: 1.5;"><strong>Form:</strong> ' + (form.properties.form_name || 'CMS-1500') + '<br/><strong>Box/Segment:</strong> <span style="color: #c084fc; font-weight: bold;">' + (form.properties.box_number || 'N/A') + '</span></div>';
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

      container.innerHTML = html || '<div class="hint-box">Sphere entity selected. Orbit or drag to inspect interconnections.</div>';
    }

    function hexToRgb(hex) {
      if (!hex || hex[0] !== '#') return '56, 189, 248';
      const bigint = parseInt(hex.slice(1), 16);
      const r = (bigint >> 16) & 255;
      const g = (bigint >> 8) & 255;
      const b = bigint & 255;
      return r + ', ' + g + ', ' + b;
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

    print(f"3D Sphere Viewer successfully built at: {out_path} ({len(html_content)} bytes)")

if __name__ == "__main__":
    build_viewer()
