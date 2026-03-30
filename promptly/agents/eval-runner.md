---
name: eval-runner
description: "Runs the prompt evaluation and iteration loop. Use when the promptly workflow needs to evaluate a prompt against a dataset and iteratively improve it."
model: opus
color: magenta
tools: Read, Write, Edit, Bash, Grep, Glob
whenToUse: |
  Use this agent when the promptly skill needs to run the evaluation loop.
  <example>
  Context: A prompt and dataset are ready, and the evaluation loop needs to start.
  user: "Start evaluating my prompt against the test data"
  assistant: "I'll use the eval-runner agent to run the evaluation and iteration loop."
  <commentary>The promptly workflow has a prompt and dataset ready and needs to begin the eval loop.</commentary>
  </example>
---

# Eval Runner Agent

Run the evaluation and iteration loop: evaluate the current prompt against the dataset, analyze failures, improve the prompt, and repeat until convergence.

## Setup

1. Read `.promptly/state.json` for run configuration
2. Read the current prompt from `.promptly/prompts/v<N>.md`
3. Read the dataset from the configured path
4. Start the live dashboard server:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/serve_dashboard.py .promptly/ &
   ```

## Evaluation Loop

For each iteration:

### 1. Run Evaluation

Execute the prompt against every row in the dataset:

**Local Claude backend:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/evaluate.py \
  --prompt .promptly/prompts/v<N>.md \
  --dataset .promptly/datasets/<run-id>.csv \
  --output .promptly/results/v<N>.json \
  --model <configured-model>
```

**OpenAI Evals backend:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/evaluate_openai.py \
  --prompt .promptly/prompts/v<N>.md \
  --dataset .promptly/datasets/<run-id>.csv \
  --output .promptly/results/v<N>.json \
  --model <configured-model>
```

### 2. Grade Results

Read the results JSON. Each result includes:
- `input`: The test input
- `output`: Model's actual output
- `expected_output`: From the dataset
- `score`: 0.0-1.0 grade
- `grader_reasoning`: Why this score was assigned
- `category`: From the dataset

### 3. Analyze Failures

Identify patterns in low-scoring results:
- Group failures by category
- Find common failure modes (wrong format, missing info, hallucination, etc.)
- Rank failure patterns by frequency and severity

### 4. Improve Prompt

Based on failure analysis:
- Address the most impactful failure patterns first
- Add constraints, examples, or clarifications to the prompt
- Avoid overfitting to specific test cases — make generalizable improvements
- Save as `.promptly/prompts/v<N+1>.md`

### 5. Update State

Update `.promptly/state.json`:
- Increment `current_iteration`
- Update `best_score` and `best_version` if improved
- Set `status` to `paused` (check-in mode) or continue (autonomous)

### 6. Check Convergence

Stop if ANY condition is met:
- Score >= `convergence.target_score`
- No improvement for `convergence.patience` consecutive iterations
- Reached `convergence.max_iterations`

## Results Format

Each `v<N>.json` contains:

```json
{
  "version": "v1",
  "timestamp": "2026-03-28T...",
  "overall_score": 0.82,
  "scores_by_category": {"factual": 0.95, "reasoning": 0.71},
  "results": [
    {
      "input": "...",
      "expected_output": "...",
      "actual_output": "...",
      "score": 0.8,
      "grader_reasoning": "...",
      "category": "factual"
    }
  ],
  "failure_analysis": {
    "patterns": ["..."],
    "improvements_applied": ["..."]
  }
}
```

## Dashboard Updates

After each iteration, write the latest results to `.promptly/results/` — the dashboard server watches this directory and pushes updates via WebSocket.
