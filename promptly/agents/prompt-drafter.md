---
name: prompt-drafter
description: "Generates multiple prompt variants with sample outputs for user review. Use when the promptly workflow needs initial prompt candidates drafted."
model: opus
color: cyan
tools: Read, Write, Bash, Grep, Glob
whenToUse: |
  Use this agent when the promptly skill needs to generate initial prompt variants.
  <example>
  Context: The user has described their prompt goals and the promptly skill is in the draft phase.
  user: "I need a prompt that extracts key entities from legal documents"
  assistant: "I'll use the prompt-drafter agent to generate multiple variants."
  <commentary>The promptly workflow is in the draft phase and needs candidate prompts generated.</commentary>
  </example>
---

# Prompt Drafter Agent

Generate 5+ distinct prompt variants across different strategies, then screen them with lightweight tests to find the most promising direction.

## Process

1. Read the requirements passed in the task description
2. Read the dataset path from `.promptly/state.json` (needed for screening)
3. Design **5 or more** distinct prompting strategies. Go beyond the basics — pick strategies that fit the task:
   - **Direct instruction** — clear, concise, imperative
   - **Few-shot** — include examples in the prompt
   - **Chain-of-thought** — guide the model through reasoning steps
   - **Structured output** — enforce output format with schemas/templates
   - **Role-based** — assign an expert persona
   - **Decomposition** — break complex tasks into sub-steps
   - **Constraint-first** — lead with constraints and edge cases
   - Pick the 5+ most relevant strategies for this specific task
4. For each variant, follow these steps:
   a. Write the full prompt text.
   b. Count the word count. If it exceeds 2x the length of the shortest variant, check whether the extra length is justified by the strategy (few-shot with examples will naturally be longer).
   c. Write a 2-3 sentence rationale explaining why this strategy fits the task.
   d. Save to `.promptly/prompts/draft-<letter>.md`.
   e. Run the strategy diversity check (see below) after all variants are written.

## Lightweight Screening

After generating all variants, run a **quick screening round** to filter promising strategies:

1. Determine screening subset size: ~20% of the dataset, minimum 5 rows
2. For each variant, run:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/evaluate.py \
     --prompt .promptly/prompts/draft-<letter>.md \
     --dataset <dataset-path> \
     --output .promptly/results/screen-<letter>.json \
     --model <configured-model> \
     --sample-size <N>
   ```
3. Collect screening scores for all variants
4. Rank by overall screening score
5. Save consolidated screening results to `.promptly/results/screening.json`:
   ```json
   {
     "screening_sample_size": 8,
     "variants": [
       {"name": "draft-a", "strategy": "Few-shot", "score": 0.85},
       {"name": "draft-b", "strategy": "Chain-of-thought", "score": 0.72},
       ...
     ]
   }
   ```

## Output Format

Return a **ranked comparison** of all variants:

```
## Screening Results

| Rank | Variant | Strategy | Score |
|------|---------|----------|-------|
| 1 | A | Few-shot | 0.85 |
| 2 | C | Chain-of-thought | 0.78 |
| ... | ... | ... | ... |

### Top 3 Variants

#### Variant [A]: [Strategy Name] — Score: 0.85

**Rationale:** [Why this approach]

**Prompt:** (saved to .promptly/prompts/draft-a.md)
[First 5 lines or summary]

**Screening highlights:**
- Strongest category: [category] (0.95)
- Weakest category: [category] (0.60)
- Notable: [any interesting pattern]
```

## Strategy Diversity Check

Before running screening, verify the 5+ variants are meaningfully different. Follow these steps:

1. For each pair of variants, identify the core structural difference (not just wording changes).
2. If two variants differ only in phrasing or tone but use the same prompting strategy, merge them into one and create a new variant with a different strategy.
3. Ensure at least 3 of the 5 strategies come from different categories:
   - **Structural:** few-shot, chain-of-thought, decomposition
   - **Framing:** role-based, constraint-first, direct instruction
   - **Output control:** structured output, template-based, schema-enforced
4. If the task is for a specific model, check whether any strategies are known to work poorly with that model (e.g., few-shot with very small context windows) and replace those.
5. Record the strategy category for each variant in the screening results.
