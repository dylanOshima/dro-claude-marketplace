#!/usr/bin/env python3
"""Live dashboard server for Promptly evaluation runs.

Serves a single-page HTML dashboard with WebSocket updates.
Watches .promptly/results/ for new result files and pushes updates.

Usage:
    python3 serve_dashboard.py .promptly/
    python3 serve_dashboard.py .promptly/ --port 3117
"""

import argparse
import asyncio
import json
import os
import signal
import sys
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread

# Try to use websockets if available, fall back to polling
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Promptly - Evaluation Dashboard</title>
<style>
  :root {
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --text-dim: #8b949e; --accent: #58a6ff;
    --green: #3fb950; --yellow: #d29922; --red: #f85149;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); }
  .header { padding: 20px 32px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }
  .header h1 { font-size: 20px; font-weight: 600; }
  .status-badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
  .status-running { background: rgba(88, 166, 255, 0.15); color: var(--accent); }
  .status-completed { background: rgba(63, 185, 80, 0.15); color: var(--green); }
  .status-paused { background: rgba(210, 153, 34, 0.15); color: var(--yellow); }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 24px 32px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
  .card-title { font-size: 13px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
  .stat { font-size: 36px; font-weight: 700; }
  .stat-label { font-size: 13px; color: var(--text-dim); margin-top: 4px; }
  .full-width { grid-column: 1 / -1; }
  .chart-container { height: 280px; position: relative; }
  canvas { width: 100% !important; height: 100% !important; }
  .compare-controls { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; }
  .compare-controls select { background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 6px 12px; font-size: 13px; }
  .compare-controls label { font-size: 13px; color: var(--text-dim); }
  .diff-view { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .diff-panel { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 16px; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 13px; line-height: 1.6; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
  .diff-panel-title { font-size: 12px; color: var(--text-dim); margin-bottom: 8px; font-family: -apple-system, sans-serif; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 10px 12px; border-bottom: 2px solid var(--border); color: var(--text-dim); font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; }
  td { padding: 10px 12px; border-bottom: 1px solid var(--border); max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  td.expandable { cursor: pointer; }
  td.expandable:hover { white-space: normal; }
  .score-cell { font-weight: 600; font-variant-numeric: tabular-nums; }
  .score-high { color: var(--green); }
  .score-mid { color: var(--yellow); }
  .score-low { color: var(--red); }
  .results-filter { display: flex; gap: 12px; margin-bottom: 12px; }
  .results-filter select { background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 6px 12px; font-size: 13px; }
  .empty-state { text-align: center; padding: 60px 20px; color: var(--text-dim); }
  .empty-state h2 { font-size: 18px; margin-bottom: 8px; color: var(--text); }
  .pulse { animation: pulse 2s ease-in-out infinite; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
</style>
</head>
<body>

<div class="header">
  <h1>Promptly</h1>
  <div>
    <span id="status-badge" class="status-badge status-running">Waiting</span>
  </div>
</div>

<div id="app">
  <div class="empty-state">
    <h2 class="pulse">Waiting for evaluation results...</h2>
    <p>Results will appear here as iterations complete.</p>
  </div>
</div>

<script>
const state = {
  iterations: [],
  prompts: {},
  status: 'waiting',
  bestScore: 0,
  bestVersion: null,
  targetScore: 0.9,
};

function scoreClass(s) {
  if (s >= 0.8) return 'score-high';
  if (s >= 0.5) return 'score-mid';
  return 'score-low';
}

function renderApp() {
  if (state.iterations.length === 0) return;
  const app = document.getElementById('app');
  const latest = state.iterations[state.iterations.length - 1];

  app.innerHTML = `
    <div class="grid">
      <div class="card">
        <div class="card-title">Current Score</div>
        <div class="stat ${scoreClass(latest.overall_score)}">${(latest.overall_score * 100).toFixed(1)}%</div>
        <div class="stat-label">${latest.version} &middot; ${latest.total_rows} test cases</div>
      </div>
      <div class="card">
        <div class="card-title">Best Score</div>
        <div class="stat ${scoreClass(state.bestScore)}">${(state.bestScore * 100).toFixed(1)}%</div>
        <div class="stat-label">${state.bestVersion} &middot; ${state.iterations.length} iteration${state.iterations.length > 1 ? 's' : ''}</div>
      </div>
      <div class="card full-width">
        <div class="card-title">Score Progression</div>
        <div class="chart-container"><canvas id="chart"></canvas></div>
      </div>
      <div class="card full-width">
        <div class="card-title">Prompt Comparison</div>
        <div class="compare-controls">
          <label>Left:</label>
          <select id="compare-left" onchange="renderComparison()">
            ${state.iterations.map((it, i) => `<option value="${i}" ${i === 0 ? 'selected' : ''}>${it.version} (${(it.overall_score * 100).toFixed(1)}%)</option>`).join('')}
          </select>
          <label>Right:</label>
          <select id="compare-right" onchange="renderComparison()">
            ${state.iterations.map((it, i) => `<option value="${i}" ${i === state.iterations.length - 1 ? 'selected' : ''}>${it.version} (${(it.overall_score * 100).toFixed(1)}%)</option>`).join('')}
          </select>
        </div>
        <div id="comparison" class="diff-view"></div>
      </div>
      <div class="card full-width">
        <div class="card-title">Results</div>
        <div class="results-filter">
          <select id="results-version" onchange="renderResults()">
            ${state.iterations.map((it, i) => `<option value="${i}" ${i === state.iterations.length - 1 ? 'selected' : ''}>${it.version}</option>`).join('')}
          </select>
          <select id="results-category" onchange="renderResults()">
            <option value="all">All Categories</option>
            ${Object.keys(latest.scores_by_category || {}).map(c => `<option value="${c}">${c}</option>`).join('')}
          </select>
        </div>
        <div id="results-table"></div>
      </div>
    </div>`;

  renderChart();
  renderComparison();
  renderResults();
}

function renderChart() {
  const canvas = document.getElementById('chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * 2;
  canvas.height = rect.height * 2;
  ctx.scale(2, 2);

  const w = rect.width, h = rect.height;
  const pad = { top: 20, right: 20, bottom: 30, left: 50 };
  const plotW = w - pad.left - pad.right;
  const plotH = h - pad.top - pad.bottom;

  ctx.clearRect(0, 0, w, h);

  // Grid lines
  ctx.strokeStyle = '#30363d';
  ctx.lineWidth = 0.5;
  for (let i = 0; i <= 10; i++) {
    const y = pad.top + plotH - (plotH * i / 10);
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
  }

  // Target line
  const targetY = pad.top + plotH - (plotH * state.targetScore);
  ctx.strokeStyle = '#58a6ff44';
  ctx.lineWidth = 1;
  ctx.setLineDash([6, 4]);
  ctx.beginPath(); ctx.moveTo(pad.left, targetY); ctx.lineTo(w - pad.right, targetY); ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = '#58a6ff88';
  ctx.font = '11px -apple-system, sans-serif';
  ctx.fillText(`Target: ${(state.targetScore * 100).toFixed(0)}%`, w - pad.right - 70, targetY - 4);

  // Score line
  const data = state.iterations;
  if (data.length < 1) return;
  const xStep = data.length > 1 ? plotW / (data.length - 1) : plotW / 2;

  ctx.strokeStyle = '#58a6ff';
  ctx.lineWidth = 2;
  ctx.beginPath();
  data.forEach((d, i) => {
    const x = pad.left + (data.length > 1 ? i * xStep : plotW / 2);
    const y = pad.top + plotH - (plotH * d.overall_score);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Points
  data.forEach((d, i) => {
    const x = pad.left + (data.length > 1 ? i * xStep : plotW / 2);
    const y = pad.top + plotH - (plotH * d.overall_score);
    ctx.fillStyle = d.version === state.bestVersion ? '#3fb950' : '#58a6ff';
    ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
  });

  // Labels
  ctx.fillStyle = '#8b949e';
  ctx.font = '11px -apple-system, sans-serif';
  ctx.textAlign = 'center';
  data.forEach((d, i) => {
    const x = pad.left + (data.length > 1 ? i * xStep : plotW / 2);
    ctx.fillText(d.version, x, h - 8);
  });
  ctx.textAlign = 'right';
  for (let i = 0; i <= 10; i += 2) {
    const y = pad.top + plotH - (plotH * i / 10);
    ctx.fillText(`${i * 10}%`, pad.left - 8, y + 4);
  }
}

function renderComparison() {
  const leftIdx = parseInt(document.getElementById('compare-left')?.value || '0');
  const rightIdx = parseInt(document.getElementById('compare-right')?.value || '0');
  const container = document.getElementById('comparison');
  if (!container) return;

  const leftVer = state.iterations[leftIdx]?.version || '?';
  const rightVer = state.iterations[rightIdx]?.version || '?';
  const leftPrompt = state.prompts[leftVer] || 'Loading...';
  const rightPrompt = state.prompts[rightVer] || 'Loading...';

  container.innerHTML = `
    <div>
      <div class="diff-panel-title">${leftVer} (${(state.iterations[leftIdx]?.overall_score * 100 || 0).toFixed(1)}%)</div>
      <div class="diff-panel">${escapeHtml(leftPrompt)}</div>
    </div>
    <div>
      <div class="diff-panel-title">${rightVer} (${(state.iterations[rightIdx]?.overall_score * 100 || 0).toFixed(1)}%)</div>
      <div class="diff-panel">${escapeHtml(rightPrompt)}</div>
    </div>`;
}

function renderResults() {
  const vIdx = parseInt(document.getElementById('results-version')?.value || '0');
  const category = document.getElementById('results-category')?.value || 'all';
  const container = document.getElementById('results-table');
  if (!container) return;

  let results = state.iterations[vIdx]?.results || [];
  if (category !== 'all') results = results.filter(r => r.category === category);

  container.innerHTML = `<table>
    <thead><tr><th>Input</th><th>Expected</th><th>Actual</th><th>Score</th><th>Category</th></tr></thead>
    <tbody>${results.map(r => `
      <tr>
        <td class="expandable" title="${escapeAttr(r.input)}">${escapeHtml(r.input)}</td>
        <td class="expandable" title="${escapeAttr(r.expected_output)}">${escapeHtml(r.expected_output)}</td>
        <td class="expandable" title="${escapeAttr(r.actual_output)}">${escapeHtml(r.actual_output)}</td>
        <td class="score-cell ${scoreClass(r.score)}">${(r.score * 100).toFixed(1)}%</td>
        <td>${escapeHtml(r.category || '-')}</td>
      </tr>`).join('')}</tbody>
  </table>`;
}

function escapeHtml(s) { return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function escapeAttr(s) { return escapeHtml(s).replace(/"/g,'&quot;'); }

function updateStatus(s) {
  state.status = s;
  const badge = document.getElementById('status-badge');
  if (!badge) return;
  badge.textContent = s.charAt(0).toUpperCase() + s.slice(1);
  badge.className = 'status-badge status-' + s;
}

// Polling fallback (used when WebSocket unavailable)
let lastKnownFiles = new Set();
async function pollResults() {
  try {
    const resp = await fetch('/api/results');
    if (!resp.ok) return;
    const data = await resp.json();

    if (data.state) {
      state.targetScore = data.state.convergence?.target_score || 0.9;
      updateStatus(data.state.status || 'running');
    }

    if (data.iterations) {
      state.iterations = data.iterations;
      state.prompts = data.prompts || {};
      let best = 0, bestVer = null;
      state.iterations.forEach(it => { if (it.overall_score > best) { best = it.overall_score; bestVer = it.version; } });
      state.bestScore = best;
      state.bestVersion = bestVer;
      renderApp();
    }
  } catch (e) { /* silent */ }
}

// WebSocket connection
function connectWS() {
  const wsPort = parseInt(location.port) + 1;
  const ws = new WebSocket(`ws://localhost:${wsPort}`);
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'update') {
      pollResults(); // Full refresh on update notification
    }
  };
  ws.onclose = () => setTimeout(connectWS, 3000);
  ws.onerror = () => {};
}

// Start polling every 2 seconds + try WebSocket
setInterval(pollResults, 2000);
pollResults();
if (location.protocol !== 'file:') connectWS();
</script>
</body>
</html>"""


def find_free_port(start: int = 3117) -> int:
    import socket
    for port in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    return start


class DashboardHandler(SimpleHTTPRequestHandler):
    """Serves the dashboard HTML and a results API endpoint."""

    data_dir: str = ""

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        elif self.path == "/api/results":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(self._gather_results()).encode())
        else:
            self.send_error(404)

    def _gather_results(self) -> dict:
        data_dir = Path(self.__class__.data_dir)
        result = {"iterations": [], "prompts": {}, "state": None}

        # Read state
        state_path = data_dir / "state.json"
        if state_path.exists():
            try:
                result["state"] = json.loads(state_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        # Read results
        results_dir = data_dir / "results"
        if results_dir.exists():
            for f in sorted(results_dir.glob("v*.json")):
                try:
                    result["iterations"].append(json.loads(f.read_text()))
                except (json.JSONDecodeError, OSError):
                    pass

        # Read prompts
        prompts_dir = data_dir / "prompts"
        if prompts_dir.exists():
            for f in sorted(prompts_dir.glob("v*.md")):
                try:
                    result["prompts"][f.stem] = f.read_text()
                except OSError:
                    pass

        return result

    def log_message(self, format, *args):
        pass  # Suppress request logs


def main():
    parser = argparse.ArgumentParser(description="Serve Promptly evaluation dashboard")
    parser.add_argument("data_dir", help="Path to .promptly/ directory")
    parser.add_argument("--port", type=int, default=0, help="Port (0 = auto)")
    args = parser.parse_args()

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Error: {data_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    DashboardHandler.data_dir = data_dir
    port = args.port if args.port > 0 else find_free_port()

    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    url = f"http://localhost:{port}"
    print(f"Dashboard: {url}", flush=True)
    print(f"Watching: {data_dir}", file=sys.stderr)

    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
