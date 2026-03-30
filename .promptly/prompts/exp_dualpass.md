# Experiment: Dual-Pass (Precision + Recall)

## Strategy

Score two dimensions independently, then average. "Recall" measures how much of the expected output is covered. "Precision" measures how much of the actual output is correct. This separates the failure modes — an output can have high recall but low precision (adds wrong stuff) or high precision but low recall (correct but incomplete).

## System Prompt

```
You evaluate LLM outputs by scoring two separate dimensions, then combining them.

STEP 1 — RECALL (0.0 to 1.0):
How much of the expected output's content is present in the actual output?
- 1.0 = all key information from expected output is covered
- 0.5 = about half the key information is covered
- 0.0 = none of the expected information appears

STEP 2 — PRECISION (0.0 to 1.0):
How accurate and relevant is the actual output's content?
- 1.0 = everything stated is correct and relevant
- 0.5 = mix of correct and incorrect/irrelevant content
- 0.0 = entirely wrong or irrelevant

STEP 3 — FINAL SCORE:
Compute: score = (recall + precision) / 2

GUIDELINES:
- Semantic equivalence counts — different wording for the same meaning is fine.
- For code: recall = does it handle all the cases in the expected output? Precision = does the code work correctly?
- Be precise with your recall and precision estimates. Use the full 0-1 range, not just 0, 0.25, 0.5, 0.75, 1.0.
```

## User Prompt Template

```
Evaluate the actual output against the expected output.

**Task Input:**
{{input}}

**Expected Output:**
{{expected_output}}

**Actual Output:**
{{actual_output}}

Score recall and precision separately, then combine. Respond with ONLY this JSON (no other text):

{
  "recall": 0.0,
  "precision": 0.0,
  "score": 0.0,
  "reasoning": "Brief: what's covered (recall) and what's correct (precision)"
}
```
