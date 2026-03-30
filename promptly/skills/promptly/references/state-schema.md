# State Persistence Schema

## state.json

All run state is saved in `.promptly/state.json`:

```json
{
  "id": "run-<timestamp>",
  "description": "User's original prompt description",
  "mode": "autonomous|check-in",
  "eval_backend": "claude|openai",
  "model": "claude-sonnet-4-20250514",
  "grading": {
    "method": "model_judge",
    "judge_model": "claude-haiku-4-5-20251001"
  },
  "convergence": {
    "max_iterations": 10,
    "target_score": 0.9,
    "patience": 3
  },
  "current_iteration": 3,
  "best_score": 0.82,
  "best_version": "v2",
  "baseline_score": 0.65,
  "dataset_path": ".promptly/datasets/run-xxx.csv",
  "status": "running|paused|completed",
  "screening": {
    "sample_size": 8,
    "results": [
      {"variant": "draft-a", "strategy": "Few-shot", "score": 0.85},
      {"variant": "draft-b", "strategy": "Chain-of-thought", "score": 0.72}
    ]
  },
  "hypotheses_log": [
    {
      "iteration": 2,
      "hypotheses": [
        {
          "id": "hyp-a",
          "description": "Add format examples to reduce formatting errors",
          "expected_impact": "Fix ~15 of 25 formatting failures",
          "score": 0.87,
          "status": "accepted"
        },
        {
          "id": "hyp-b",
          "description": "Add constraint for max output length",
          "expected_impact": "Fix 5 verbosity failures",
          "score": 0.79,
          "early_stopped": true,
          "status": "rejected"
        }
      ]
    }
  ]
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique run identifier (run-YYYYMMDD-HHMMSS) |
| `description` | string | User's original prompt description |
| `mode` | string | `autonomous` or `check-in` |
| `eval_backend` | string | `claude` or `openai` |
| `model` | string | Target model for prompt evaluation |
| `grading` | object | Grading configuration (see references/grading.md) |
| `convergence` | object | Stop conditions for the iteration loop |
| `current_iteration` | int | Current iteration number |
| `best_score` | float | Highest score achieved so far (0.0-1.0) |
| `best_version` | string | Version that achieved best score |
| `baseline_score` | float\|null | Score of the original prompt before optimization (null if creating from scratch) |
| `dataset_path` | string | Path to the CSV dataset |
| `status` | string | `running`, `paused`, or `completed` |
| `screening` | object\|null | Results from the lightweight strategy screening round |
| `hypotheses_log` | array | Log of hypotheses tested per iteration, with outcomes |

### Screening Object

Recorded after the draft & screen phase (Step 4):

| Field | Type | Description |
|-------|------|-------------|
| `screening.sample_size` | int | Number of rows used for screening |
| `screening.results[]` | array | Per-variant screening scores |
| `screening.results[].variant` | string | Draft filename stem (e.g., "draft-a") |
| `screening.results[].strategy` | string | Strategy name (e.g., "Few-shot") |
| `screening.results[].score` | float | Screening score (0.0-1.0) |

### Hypotheses Log

Recorded per iteration during the eval loop (Step 6):

| Field | Type | Description |
|-------|------|-------------|
| `hypotheses_log[].iteration` | int | Which iteration these hypotheses were tested in |
| `hypotheses_log[].hypotheses[]` | array | Individual hypotheses tested |
| `hypotheses_log[].hypotheses[].id` | string | Hypothesis ID (e.g., "hyp-a") |
| `hypotheses_log[].hypotheses[].description` | string | What was changed and why |
| `hypotheses_log[].hypotheses[].expected_impact` | string | Predicted improvement |
| `hypotheses_log[].hypotheses[].score` | float | Actual score achieved |
| `hypotheses_log[].hypotheses[].early_stopped` | bool | Whether evaluation was stopped early |
| `hypotheses_log[].hypotheses[].status` | string | `accepted`, `rejected`, or `merged` |

## Directory Structure

```
.promptly/
├── state.json              # Run state (for resume)
├── prompts/
│   ├── baseline.md         # Original prompt (if modifying existing)
│   ├── draft-a.md          # Strategy variants from screening
│   ├── draft-b.md
│   ├── ...
│   ├── v1.md               # Selected starting version
│   ├── v2.md               # Improved version
│   ├── v2-hyp-a.md         # Hypothesis variant (temporary)
│   ├── v2-hyp-b.md         # Hypothesis variant (temporary)
│   ├── ...
│   └── best.md             # Copy of highest-scoring version
├── datasets/
│   └── run-20260328.csv    # Validation dataset (CSV)
├── results/
│   ├── baseline.json       # Baseline evaluation results
│   ├── screening.json      # Strategy screening results
│   ├── screen-a.json       # Per-variant screening detail
│   ├── screen-b.json
│   ├── v1.json             # Full eval results for v1
│   ├── v2.json             # Full eval results for v2
│   ├── v2-hyp-a.json       # Hypothesis eval results
│   ├── v2-hyp-b.json
│   └── ...
└── reports/
    └── index.html          # Static snapshot of dashboard
```
