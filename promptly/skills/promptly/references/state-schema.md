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
  "dataset_path": ".promptly/datasets/run-xxx.csv",
  "status": "running|paused|completed"
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
| `dataset_path` | string | Path to the CSV dataset |
| `status` | string | `running`, `paused`, or `completed` |

## Directory Structure

```
.promptly/
├── state.json              # Run state (for resume)
├── prompts/
│   ├── v1.md               # First prompt version
│   ├── v2.md               # Improved version
│   ├── ...
│   └── best.md             # Copy of highest-scoring version
├── datasets/
│   └── run-20260328.csv    # Validation dataset (CSV)
├── results/
│   ├── v1.json             # Eval results for v1
│   ├── v2.json             # Eval results for v2
│   └── ...
└── reports/
    └── index.html          # Static snapshot of dashboard
```
