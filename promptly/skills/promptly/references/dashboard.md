# Live Dashboard Architecture

The dashboard is a locally-served single-page HTML application that displays evaluation progress in real time.

## Architecture

```
serve_dashboard.py (Python HTTP + WebSocket server)
├── Serves index.html at http://localhost:3117
├── Watches .promptly/results/ for new files
└── Pushes updates via WebSocket to connected clients
```

## Features

### Score Progression Chart
- Line chart showing overall score across iterations
- Per-category score lines (togglable)
- Target threshold displayed as horizontal dashed line

### Prompt Version Comparison
- Side-by-side diff view of any two prompt versions
- Dropdown selectors for v1..vN
- Syntax-highlighted diff with additions/removals

### Results Table
- Sortable table of all evaluation results for a given iteration
- Columns: input, expected output, actual output, score, category
- Color-coded scores (red < 0.5, yellow 0.5-0.8, green > 0.8)
- Click to expand full text for long inputs/outputs

### Run Summary
- Current iteration number
- Best score and which version achieved it
- Convergence status (running, plateau, target reached, max iterations)
- Time elapsed

## WebSocket Protocol

The server sends JSON messages when results change:

```json
{
  "type": "update",
  "iteration": 3,
  "overall_score": 0.85,
  "scores_by_category": {"factual": 0.92, "reasoning": 0.78},
  "best_score": 0.85,
  "best_version": "v3",
  "status": "running"
}
```

The client automatically re-renders charts and tables on each update.

## File Watching

The server uses `os.scandir()` polling (1-second interval) on `.promptly/results/` to detect new result files. When a new `v<N>.json` appears, it reads the file, extracts summary metrics, and broadcasts to all connected WebSocket clients.

## Port Selection

Default port: 3117. If unavailable, increment until a free port is found. Print the URL to stdout so Claude can relay it to the user.
