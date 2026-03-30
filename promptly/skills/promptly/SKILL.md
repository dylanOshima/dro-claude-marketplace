---
name: promptly
description: "This skill should be used when the user invokes /promptly, asks to 'create a prompt', 'optimize a prompt', 'evaluate a prompt against data', 'iterate on a prompt', 'test my prompt', 'benchmark prompt performance', 'improve my prompt', or wants to build and test prompts against validation datasets. Orchestrates the full prompt engineering workflow: understand goals, draft variants, build datasets, evaluate, and iterate."
argument-hint: "<description of the prompt to create> or --resume to continue a previous run"
allowed-tools: "Read, Write, Edit, Bash, Agent, Glob, Grep, WebFetch, WebSearch"
---

# Promptly - Prompt Engineering Workbench

Orchestrate a complete prompt engineering workflow: understand goals, draft multiple variants, build or source validation datasets, evaluate against them, and iterate until convergence.

## Workflow Overview

```
Understand → Draft Variants → Build Dataset → Evaluate & Iterate → Report
```

All data persists in `.promptly/` within the current project directory.

## Resume Support

When invoked with `--resume`, check for `.promptly/state.json`. If found, read the state and resume from the last checkpoint. Present the current status to the user and ask how to proceed.

## Step 1: Understand

Goal: Deeply understand what the prompt needs to accomplish before writing anything.

1. Read the user's description from the command arguments
2. Ask clarifying questions **one at a time** to understand:
   - What task the prompt performs (classification, generation, extraction, transformation, etc.)
   - What model will run this prompt in production
   - What "good output" looks like — ask for 1-2 concrete examples
   - What failure modes to watch for
   - Any constraints (token budget, format requirements, tone)
3. Summarize understanding and confirm with the user before proceeding

## Step 2: Configuration

Ask the user these configuration questions:

1. **Autonomy mode**: "Would you like me to run autonomously, or check in with you periodically?"
   - **Autonomous**: Run the full eval loop, stop on convergence criteria
   - **Check-in**: Pause after each iteration for user review

2. **Evaluation backend**: "Should I evaluate locally with Claude, or use the OpenAI Evals API?"
   - **Local Claude**: Uses Anthropic SDK — requires `ANTHROPIC_API_KEY`
   - **OpenAI Evals**: Uses OpenAI Evals API — requires `OPENAI_API_KEY`

3. **Convergence settings** (for autonomous mode):
   - Max iterations (default: 10)
   - Target score threshold (default: 0.9)
   - Plateau patience — stop if no improvement for N iterations (default: 3)

Save configuration to `.promptly/state.json`.

## Step 3: Draft Prompt Variants

Use the `prompt-drafter` agent to generate 3 prompt variants.

1. Dispatch the `prompt-drafter` agent with the understood requirements
2. The agent returns 3 variants, each with:
   - The full prompt text
   - A brief rationale for the approach
   - Sample output from 2-3 example inputs
3. Present all variants to the user with sample outputs
4. Ask the user to pick one as the starting point (or request modifications)
5. Save the selected prompt as `.promptly/prompts/v1.md`

## Step 4: Build or Source Dataset

Use the `dataset-builder` agent to create or import a validation dataset.

1. Ask the user: "Do you have existing validation data, or should I generate a synthetic dataset?"
   - **Existing data**: Ask for the file path or directory. Also ask if there is a specific location or convention for datasets in this project.
   - **Generate**: Instruct the agent to create synthetic test cases using a **different model** than the evaluation target to avoid overfitting
2. Dataset format is CSV with columns: `input,expected_output,category`
   - `category` is optional, used for segmented scoring
3. Save to `.promptly/datasets/<run-id>.csv`
4. Present dataset summary: row count, categories, sample rows

## Step 5: Evaluate & Iterate

Use the `eval-runner` agent to run the evaluation loop.

1. Initialize the `.promptly/state.json` with run metadata
2. Launch the live HTML dashboard: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/serve_dashboard.py .promptly/` and open in browser
3. For each iteration:
   a. Run the current prompt against all dataset rows using the configured backend
   b. Grade outputs using the configured grading method (see `references/grading.md`)
   c. Save results to `.promptly/results/v<N>.json`
   d. Update the dashboard with new results
   e. Analyze failures and identify patterns
   f. Generate an improved prompt based on failure analysis
   g. Save as `.promptly/prompts/v<N+1>.md`
   h. Check convergence:
      - Score >= target threshold? Stop.
      - No improvement for `patience` iterations? Stop.
      - Reached max iterations? Stop.
   i. In check-in mode: pause and present results to user
4. Update `.promptly/state.json` after each iteration

## Step 6: Final Report

When the iteration loop completes:

1. Present a summary: best prompt version, final score, iterations run
2. Show score progression across iterations
3. Highlight the dashboard URL for detailed exploration
4. Save the best prompt prominently as `.promptly/prompts/best.md`
5. Ask the user if they want to continue iterating or finalize

## State & Data

All run data persists in `.promptly/` — see `references/state-schema.md` for the full `state.json` schema and directory layout.

## Additional Resources

### Reference Files

- **`references/grading.md`** — Grading methods: model-as-judge, string matching, similarity metrics, custom Python
- **`references/openai-evals.md`** — OpenAI Evals API integration details and grader types
- **`references/dashboard.md`** — Live dashboard architecture and update protocol
- **`references/state-schema.md`** — State persistence schema and directory structure
