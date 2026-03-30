# Grading Methods

Promptly supports multiple grading methods that can be combined for comprehensive evaluation.

## Model-as-Judge (Default)

Uses an LLM to grade the output against the expected output.

**How it works:**
1. Send the input, expected output, and actual output to a grading model
2. The grading model returns a score (0.0-1.0) and reasoning
3. Uses a different model than the one being evaluated to avoid bias

**Grading prompt template:**
```
You are an expert evaluator. Grade the following output on a scale of 0.0 to 1.0.

Task Input: {{input}}
Expected Output: {{expected_output}}
Actual Output: {{actual_output}}

Score the output based on:
- Correctness: Does it match the expected output semantically?
- Completeness: Does it cover all required information?
- Format: Does it follow the expected format?

Respond with JSON:
{"score": 0.0-1.0, "reasoning": "brief explanation"}
```

## String Matching

Exact or fuzzy comparison between actual and expected output.

**Methods:**
- `exact`: Case-sensitive exact match (score: 0 or 1)
- `case_insensitive`: Case-insensitive exact match
- `contains`: Expected output is contained in actual output
- `fuzzy`: Levenshtein distance-based similarity (0.0-1.0)

## Similarity Metrics

Statistical text similarity measures.

**Methods:**
- `cosine`: Cosine similarity of TF-IDF vectors
- `bleu`: BLEU score (common for translation tasks)
- `rouge_l`: ROUGE-L score (longest common subsequence)

## Custom Python Grader

User-provided Python function for domain-specific grading.

**Interface:**
```python
def grade(input_text: str, expected: str, actual: str) -> dict:
    """
    Returns: {"score": float, "reasoning": str}
    """
    # Custom grading logic
    return {"score": 0.85, "reasoning": "Matched 17/20 entities"}
```

Save custom graders to `.promptly/graders/custom.py`.

## Composite Grading

Combine multiple graders with weights:

```json
{
  "graders": [
    {"type": "model_judge", "weight": 0.6},
    {"type": "rouge_l", "weight": 0.2},
    {"type": "contains", "weight": 0.2}
  ]
}
```

Final score = weighted average of all grader scores.

## Configuration

Set the grading method in `.promptly/state.json`:

```json
{
  "grading": {
    "method": "model_judge",
    "judge_model": "claude-haiku-4-5-20251001",
    "fallback": "rouge_l"
  }
}
```
