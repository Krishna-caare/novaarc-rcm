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
  <title>NovaArc RCM — Denial Knowledge Graph Explorer</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: #070a12;
      color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      overflow: hidden;
      width: 100vw;
      height: 100vh;
      display: flex;
    }
    #canvas-container {
      flex: 1;
      position: relative;
      height: 100%;
      background: radial-gradient(circle at center, #111a2e 0%, #050811 100%);
    }
    canvas {
      display: block;
      width: 100%;
      height: 100%;
      cursor: grab;
    }
    canvas:active { cursor: grabbing; }

    /* Top Bar */
    .top-bar {
      position: absolute;
      top: 16px;
      left: 16px;
      right: 16px;
      display: flex;
      gap: 12px;
      align-items: center;
      z-index: 10;
      pointer-events: none;
    }
    .top-bar > * { pointer-events: auto; }
    .brand-badge {
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid rgba(59, 130, 246, 0.4);
      backdrop-filter: blur(8px);
      padding: 8px 16px;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 600;
      color: #60a5fa;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }
    .brand-badge .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #38bdf8;
      box-shadow: 0 0 10px #38bdf8;
    }
    .search-input {
      flex: 1;
      max-width: 380px;
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid rgba(148, 163, 184, 0.2);
      backdrop-filter: blur(8px);
      padding: 9px 16px;
      border-radius: 9999px;
      color: #fff;
      font-size: 13px;
      outline: none;
      transition: all 0.2s;
    }
    .search-input:focus {
      border-color: #3b82f6;
      box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
    }
    .legend-chips {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .legend-chip {
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid rgba(148, 163, 184, 0.2);
      padding: 5px 10px;
      border-radius: 6px;
      font-size: 11px;
      display: flex;
      align-items: center;
      gap: 5px;
      cursor: pointer;
      user-select: none;
      transition: all 0.2s;
    }
    .legend-chip:hover { border-color: #94a3b8; background: rgba(30, 41, 59, 0.8); }
    .legend-chip .orb-icon { width: 8px; height: 8px; border-radius: 50%; }

    /* Detail Sidebar */
    .sidebar {
      width: 450px;
      height: 100%;
      background: #0b1120;
      border-left: 1px solid rgba(148, 163, 184, 0.15);
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 18px;
      box-shadow: -10px 0 30px rgba(0, 0, 0, 0.6);
      z-index: 20;
    }
    .sidebar-header {
      border-bottom: 1px solid rgba(148, 163, 184, 0.15);
      padding-bottom: 16px;
    }
    .node-type-badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }
    .sidebar-title {
      font-size: 18px;
      font-weight: 700;
      color: #f8fafc;
      line-height: 1.3;
    }
    .sidebar-desc {
      font-size: 13px;
      color: #94a3b8;
      line-height: 1.5;
      margin-top: 6px;
    }
    .section-card {
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid rgba(148, 163, 184, 0.15);
      border-radius: 8px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .section-card h4 {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
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
      line-height: 1.4;
    }
    .checklist-item::before {
      content: "•";
      color: #38bdf8;
      font-weight: bold;
    }
    .script-item {
      background: rgba(15, 23, 42, 0.5);
      border-left: 2px solid #ec4899;
      padding: 6px 10px;
      border-radius: 0 4px 4px 0;
      font-size: 12px;
      color: #f1f5f9;
      font-style: italic;
    }
    .copy-btn {
      background: #2563eb;
      color: #fff;
      border: none;
      padding: 6px 10px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: background 0.2s;
    }
    .copy-btn:hover { background: #1d4ed8; }
    .notes-box {
      background: #050811;
      border: 1px solid #1e293b;
      padding: 10px;
      border-radius: 6px;
      font-family: monospace;
      font-size: 11px;
      color: #94a3b8;
      white-space: pre-wrap;
      max-height: 130px;
      overflow-y: auto;
    }
    .hint-text {
      font-size: 12px;
      color: #64748b;
      text-align: center;
      margin-top: 30px;
    }
  </style>
</head>
<body>
  <div id="canvas-container">
    <div class="top-bar">
      <div class="brand-badge">
        <span class="dot"></span>
        <span>NovaArc Knowledge Graph Orb</span>
      </div>
      <input type="text" id="search-box" class="search-input" placeholder="Search code or keyword (e.g. CO-16, operative, modifier 25)..." />
      <div class="legend-chips">
        <div class="legend-chip"><span class="orb-icon" style="background: #3b82f6;"></span> Category</div>
        <div class="legend-chip"><span class="orb-icon" style="background: #60a5fa;"></span> CARC Code</div>
        <div class="legend-chip"><span class="orb-icon" style="background: #34d399;"></span> Scenario</div>
        <div class="legend-chip"><span class="orb-icon" style="background: #c084fc;"></span> CMS-1500 Box</div>
        <div class="legend-chip"><span class="orb-icon" style="background: #2dd4bf;"></span> Action Plan</div>
      </div>
    </div>
    <canvas id="graph-canvas"></canvas>
  </div>

  <div class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div>
        <div class="node-type-badge" id="badge-type" style="background: #1e3a8a; color: #93c5fd;">Interactive Inspector</div>
        <h3 class="sidebar-title" id="node-title">Denial Knowledge Graph</h3>
      </div>
    </div>
    <div class="sidebar-desc" id="node-desc">
      Click on any glowing orbital node in the network to inspect its sub-scenarios, CMS-1500 box mappings, payer call scripts, and step-by-step resolution playbooks.
    </div>

    <div id="dynamic-sections" style="display: flex; flex-direction: column; gap: 14px;">
      <div class="hint-text">
        Tip: Drag nodes to explore orbital connections, or use mouse wheel to zoom in and out.
      </div>
    </div>
  </div>

  <script>
    const graphData = """ + graph_json + """;

    const canvas = document.getElementById('graph-canvas');
    const ctx = canvas.getContext('2d');
    let width = canvas.width = canvas.parentElement.clientWidth;
    let height = canvas.height = canvas.parentElement.clientHeight;

    window.addEventListener('resize', function() {
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    });

    const nodes = graphData.nodes.map(function(n, i) {
      const angle = (i / graphData.nodes.length) * Math.PI * 2;
      const dist = (n.radius || 15) * 8 + Math.random() * 80;
      return Object.assign({}, n, {
        x: width / 2 + Math.cos(angle) * dist + (Math.random() - 0.5) * 60,
        y: height / 2 + Math.sin(angle) * dist + (Math.random() - 0.5) * 60,
        vx: 0,
        vy: 0,
        radius: n.radius || 15,
        color: n.color || '#3b82f6'
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

    let transform = { x: 0, y: 0, scale: 0.9 };
    let isDraggingCanvas = false;
    let draggedNode = null;
    let startPan = { x: 0, y: 0 };
    let hoveredNode = null;
    let selectedNode = null;
    let filterQuery = '';

    canvas.addEventListener('wheel', function(e) {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      transform.scale = Math.max(0.2, Math.min(3.5, transform.scale * zoomFactor));
    });

    canvas.addEventListener('mousedown', function(e) {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - width / 2 - transform.x) / transform.scale + width / 2;
      const mouseY = (e.clientY - rect.top - height / 2 - transform.y) / transform.scale + height / 2;

      for (let i = nodes.length - 1; i >= 0; i--) {
        const n = nodes[i];
        const dx = mouseX - n.x;
        const dy = mouseY - n.y;
        if (dx * dx + dy * dy < n.radius * n.radius) {
          draggedNode = n;
          selectedNode = n;
          displayNodeDetails(n);
          return;
        }
      }

      isDraggingCanvas = true;
      startPan = { x: e.clientX - transform.x, y: e.clientY - transform.y };
    });

    window.addEventListener('mousemove', function(e) {
      if (draggedNode) {
        const rect = canvas.getBoundingClientRect();
        draggedNode.x = (e.clientX - rect.left - width / 2 - transform.x) / transform.scale + width / 2;
        draggedNode.y = (e.clientY - rect.top - height / 2 - transform.y) / transform.scale + height / 2;
        draggedNode.vx = 0;
        draggedNode.vy = 0;
      } else if (isDraggingCanvas) {
        transform.x = e.clientX - startPan.x;
        transform.y = e.clientY - startPan.y;
      } else {
        const rect = canvas.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left - width / 2 - transform.x) / transform.scale + width / 2;
        const mouseY = (e.clientY - rect.top - height / 2 - transform.y) / transform.scale + height / 2;
        hoveredNode = null;
        for (let i = nodes.length - 1; i >= 0; i--) {
          const n = nodes[i];
          const dx = mouseX - n.x;
          const dy = mouseY - n.y;
          if (dx * dx + dy * dy < n.radius * n.radius) {
            hoveredNode = n;
            break;
          }
        }
      }
    });

    window.addEventListener('mouseup', function() {
      draggedNode = null;
      isDraggingCanvas = false;
    });

    const searchBox = document.getElementById('search-box');
    searchBox.addEventListener('input', function(e) {
      filterQuery = e.target.value.toLowerCase().trim();
      if (filterQuery) {
        const match = nodes.find(function(n) {
          return n.label.toLowerCase().indexOf(filterQuery) !== -1 || (n.description && n.description.toLowerCase().indexOf(filterQuery) !== -1);
        });
        if (match) {
          transform.x = -(match.x - width / 2) * transform.scale;
          transform.y = -(match.y - height / 2) * transform.scale;
          selectedNode = match;
          displayNodeDetails(match);
        }
      }
    });

    function simulate() {
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          let dx = b.x - a.x;
          let dy = b.y - a.y;
          let dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const minDist = (a.radius + b.radius) * 2.2;
          if (dist < minDist) {
            const force = (minDist - dist) / dist * 0.4;
            const fx = dx * force;
            const fy = dy * force;
            a.vx -= fx;
            a.vy -= fy;
            b.vx += fx;
            b.vy += fy;
          }
        }
      }

      links.forEach(function(l) {
        const a = l.sourceNode;
        const b = l.targetNode;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const targetDist = 65 + (a.radius + b.radius);
        const force = (dist - targetDist) * 0.02;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      });

      nodes.forEach(function(n) {
        if (n === draggedNode) return;
        const cdx = width / 2 - n.x;
        const cdy = height / 2 - n.y;
        n.vx += cdx * 0.001;
        n.vy += cdy * 0.001;
        n.x += n.vx;
        n.y += n.vy;
        n.vx *= 0.84;
        n.vy *= 0.84;
      });
    }

    function draw() {
      simulate();
      ctx.clearRect(0, 0, width, height);

      ctx.save();
      ctx.translate(width / 2 + transform.x, height / 2 + transform.y);
      ctx.scale(transform.scale, transform.scale);
      ctx.translate(-width / 2, -height / 2);

      links.forEach(function(l) {
        const isHighlighted = selectedNode && (l.sourceNode === selectedNode || l.targetNode === selectedNode);
        ctx.beginPath();
        ctx.moveTo(l.sourceNode.x, l.sourceNode.y);
        ctx.lineTo(l.targetNode.x, l.targetNode.y);
        ctx.strokeStyle = isHighlighted ? 'rgba(96, 165, 250, 0.7)' : 'rgba(148, 163, 184, 0.15)';
        ctx.lineWidth = isHighlighted ? 2.5 : 1;
        ctx.stroke();
      });

      nodes.forEach(function(n) {
        const isSelected = n === selectedNode;
        const isHovered = n === hoveredNode;
        const isMatch = filterQuery && (n.label.toLowerCase().indexOf(filterQuery) !== -1 || (n.description && n.description.toLowerCase().indexOf(filterQuery) !== -1));

        if (isSelected || isHovered || isMatch) {
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius + 8, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(59, 130, 246, 0.25)';
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.shadowColor = n.color;
        ctx.shadowBlur = isSelected ? 22 : 8;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.strokeStyle = isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.35)';
        ctx.lineWidth = isSelected ? 2.5 : 1;
        ctx.stroke();

        if (n.radius >= 16 || isSelected || isHovered || isMatch) {
          ctx.font = Math.max(11, n.radius * 0.65) + 'px -apple-system, sans-serif';
          ctx.fillStyle = '#f8fafc';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          const shortLabel = n.label.length > 24 ? n.label.slice(0, 22) + '...' : n.label;
          ctx.fillText(shortLabel, n.x, n.y + n.radius + 12);
        }
      });

      ctx.restore();
      requestAnimationFrame(draw);
    }

    draw();

    function displayNodeDetails(node) {
      const badge = document.getElementById('badge-type');
      const title = document.getElementById('node-title');
      const desc = document.getElementById('node-desc');
      const container = document.getElementById('dynamic-sections');

      badge.textContent = node.type.replace('_', ' ');
      badge.style.background = node.color;
      badge.style.color = '#fff';
      title.textContent = node.label;
      desc.textContent = node.description || 'Knowledge graph entity node.';

      let html = '';

      if (node.type === 'denial_code') {
        const codeKey = node.properties.code || node.label.split(':')[0].trim();
        const connectedScenarios = nodes.filter(function(n) {
          return n.type === 'scenario' && n.properties && n.properties.code === codeKey;
        });
        html += '<div class="section-card"><h4><span>📂</span> Associated Operational Scenarios (' + connectedScenarios.length + ')</h4><div style="display: flex; flex-direction: column; gap: 6px;">';
        connectedScenarios.forEach(function(s) {
          html += '<div style="padding: 8px; background: rgba(15,23,42,0.6); border-radius: 4px; font-size: 12px; cursor: pointer; border-left: 2px solid #34d399;" onclick="selectNodeById(\'' + s.id + '\')"><strong>' + s.label + '</strong><div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">' + (s.description || '') + '</div></div>';
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
          html += '<div class="section-card"><h4><span>📋</span> Form & Field Requirements</h4><div style="font-size: 12px; color: #f1f5f9;"><strong>Form:</strong> ' + (form.properties.form_name || 'CMS-1500') + '<br/><strong>Box/Segment:</strong> <span style="color: #c084fc; font-weight: bold;">' + (form.properties.box_number || 'N/A') + '</span></div>';
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
          html += '<div class="section-card"><h4><span>⚡</span> Step-by-Step Resolution Playbook</h4><div style="display: flex; flex-direction: column; gap: 4px;">';
          act.properties.steps.forEach(function(s) {
            html += '<div style="font-size: 12px; color: #a7f3d0;">✓ ' + s + '</div>';
          });
          html += '</div></div>';
        }

        if (node.properties && node.properties.standard_notes) {
          html += '<div class="section-card"><div style="display: flex; justify-content: space-between; align-items: center;"><h4><span>📝</span> Standard AR Call Notes</h4><button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById(\\'ar-notes-text\\').innerText); this.innerText=\\'Copied!\\';">Copy Notes</button></div><div class="notes-box" id="ar-notes-text">' + node.properties.standard_notes + '</div></div>';
        }
      }

      container.innerHTML = html || '<div class="hint-text">Connected subgraph node. Drag to inspect connections.</div>';
    }

    window.selectNodeById = function(id) {
      const target = nodes.find(function(n) { return n.id === id; });
      if (target) {
        selectedNode = target;
        displayNodeDetails(target);
        transform.x = -(target.x - width / 2) * transform.scale;
        transform.y = -(target.y - height / 2) * transform.scale;
      }
    };
  </script>
</body>
</html>"""

    out_path = os.path.join(os.path.dirname(__file__), "viewer.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Viewer successfully built at: {out_path} ({len(html_content)} bytes)")

if __name__ == "__main__":
    build_viewer()
