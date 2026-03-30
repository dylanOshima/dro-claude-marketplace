# OpenAI Evals API Integration

Details for using the OpenAI Evals API as the evaluation backend.

## Prerequisites

- `openai` Python SDK installed (`pip install openai`)
- `OPENAI_API_KEY` environment variable set

## API Workflow

### 1. Create an Eval

```python
from openai import OpenAI
client = OpenAI()

eval_obj = client.evals.create(
    name="promptly-eval-<run-id>",
    data_source_config={
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {
                "input": {"type": "string"},
                "expected_output": {"type": "string"},
                "category": {"type": "string"}
            }
        },
        "include_sample_schema": True
    },
    testing_criteria=[
        {
            "type": "score_model",
            "name": "quality_grader",
            "model": "o3",
            "input": [
                {"role": "system", "content": "Grade the response quality from 1-7. Consider correctness, completeness, and format compliance."},
                {"role": "user", "content": "Task: {{item.input}}\nExpected: {{item.expected_output}}\nActual: {{sample.output_text}}"}
            ],
            "range": [1, 7],
            "pass_threshold": 5.0
        }
    ]
)
```

### 2. Run the Eval

```python
run = client.evals.runs.create(
    eval_id=eval_obj.id,
    name=f"v{iteration}",
    data_source={
        "type": "completions",
        "source": {
            "type": "file_content",
            "content": [{"item": row} for row in dataset]
        },
        "input_messages": {
            "type": "template",
            "template": [
                {"type": "message", "role": "system",
                 "content": {"type": "input_text", "text": prompt_text}},
                {"type": "message", "role": "user",
                 "content": {"type": "input_text", "text": "{{item.input}}"}}
            ]
        },
        "model": model_name,
        "sampling_params": {"seed": 42, "temperature": 0.7}
    }
)
```

### 3. Retrieve Results

```python
# Poll for completion
import time
while True:
    run_status = client.evals.runs.retrieve(eval_id=eval_obj.id, run_id=run.id)
    if run_status.status in ("completed", "failed", "canceled"):
        break
    time.sleep(5)

# Get results
results = client.evals.runs.output_items.list(eval_id=eval_obj.id, run_id=run.id)
```

## Grader Types Available

| Type | Use Case |
|------|----------|
| `StringCheckGrader` | Exact/fuzzy string match (`eq`, `ne`, `like`, `ilike`) |
| `TextSimilarityGrader` | Similarity metrics: `cosine`, `bleu`, `rouge_l`, `meteor` |
| `ScoreModelGrader` | LLM assigns numeric score (1-7, 1-10, etc.) |
| `LabelModelGrader` | LLM assigns categorical labels |
| `PythonGrader` | Custom Python `grade(input, output)` function |
| `MultiGrader` | Combines multiple graders |

## Score Normalization

OpenAI scores use different ranges depending on grader type. Normalize all scores to 0.0-1.0 for consistency with local Claude evaluation:

```python
def normalize_score(score, grader_range):
    min_val, max_val = grader_range
    return (score - min_val) / (max_val - min_val)
```

## External Model Support

OpenAI Evals can evaluate non-OpenAI models (including Claude) by configuring custom endpoints. However, for simplicity, the `evaluate_openai.py` script pre-generates Claude responses locally and feeds them to the OpenAI grading system.
