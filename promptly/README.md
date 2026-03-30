# Promptly

A prompt engineering workbench for Claude Code. Generate, evaluate, and iterate on prompts against validation datasets.

## Usage

```
/promptly <description of what the prompt should do>
/promptly --resume    # Resume a previous evaluation run
```

## Workflow

1. **Understand** - Collaborative dialogue to understand prompt goals
2. **Draft** - Generate multiple prompt variants with sample outputs
3. **Dataset** - Source existing CSV data or generate synthetic validation sets
4. **Evaluate** - Run prompts against the dataset (local Claude or OpenAI Evals API)
5. **Iterate** - Improve prompts in a loop until convergence
6. **Report** - Live HTML dashboard showing progression and results

## Evaluation Backends

- **Local Claude** - Uses Anthropic SDK to evaluate prompts locally
- **OpenAI Evals API** - Submits evaluations to OpenAI's platform

## Data Storage

All data is saved in `.promptly/` in your project directory:

```
.promptly/
├── state.json        # Run state (for resume)
├── prompts/          # Prompt versions (v1.md, v2.md, ...)
├── datasets/         # CSV validation sets
├── results/          # Eval results per iteration
└── reports/          # Generated HTML dashboard
```

## Dataset Format

CSV with columns: `input,expected_output,category`

- `input` (required) - The input to the prompt
- `expected_output` (required) - Expected output for grading
- `category` (optional) - For segmented scoring

## Requirements

- Python 3.10+
- `anthropic` SDK (for local Claude eval)
- `openai` SDK (for OpenAI Evals eval)

Install dependencies:
```bash
pip install anthropic openai
```
