#!/usr/bin/env python3
"""OpenAI Evals API evaluation engine for Promptly.

Submits a prompt evaluation to OpenAI's Evals API, waits for completion,
and saves normalized results as JSON.

Usage:
    python3 evaluate_openai.py \
        --prompt .promptly/prompts/v1.md \
        --dataset .promptly/datasets/run-xxx.csv \
        --output .promptly/results/v1.json \
        --model gpt-4.1 \
        [--grader-model o3] \
        [--score-range 1,7] \
        [--pass-threshold 5.0]
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai SDK not installed. Run: pip install openai", file=sys.stderr)
    sys.exit(1)


def load_prompt(prompt_path: str) -> str:
    return Path(prompt_path).read_text().strip()


def load_dataset(dataset_path: str) -> list[dict]:
    rows = []
    with open(dataset_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "input": row["input"],
                "expected_output": row["expected_output"],
                "category": row.get("category", ""),
            })
    return rows


def normalize_score(score: float, score_range: tuple[float, float]) -> float:
    min_val, max_val = score_range
    if max_val == min_val:
        return 1.0 if score >= max_val else 0.0
    return round((score - min_val) / (max_val - min_val), 4)


def main():
    parser = argparse.ArgumentParser(description="Evaluate prompt using OpenAI Evals API")
    parser.add_argument("--prompt", required=True, help="Path to prompt file")
    parser.add_argument("--dataset", required=True, help="Path to CSV dataset")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    parser.add_argument("--model", default="gpt-4.1", help="Model to evaluate")
    parser.add_argument("--grader-model", default="o3", help="Model for grading")
    parser.add_argument("--score-range", default="1,7", help="Score range min,max")
    parser.add_argument("--pass-threshold", type=float, default=5.0, help="Pass threshold")
    args = parser.parse_args()

    score_range = tuple(float(x) for x in args.score_range.split(","))
    client = OpenAI()
    prompt_text = load_prompt(args.prompt)
    dataset = load_dataset(args.dataset)

    # Step 1: Create the eval
    print("Creating eval...", file=sys.stderr)
    eval_obj = client.evals.create(
        name=f"promptly-{Path(args.prompt).stem}",
        data_source_config={
            "type": "custom",
            "item_schema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                    "expected_output": {"type": "string"},
                    "category": {"type": "string"},
                },
            },
            "include_sample_schema": True,
        },
        testing_criteria=[
            {
                "type": "score_model",
                "name": "quality_grader",
                "model": args.grader_model,
                "input": [
                    {
                        "role": "system",
                        "content": (
                            "Grade the response quality. Consider correctness against the expected output, "
                            "completeness, and format compliance."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Task Input: {{item.input}}\n"
                            "Expected Output: {{item.expected_output}}\n"
                            "Actual Output: {{sample.output_text}}"
                        ),
                    },
                ],
                "range": list(score_range),
                "pass_threshold": args.pass_threshold,
            }
        ],
    )

    # Step 2: Run the eval
    print("Starting eval run...", file=sys.stderr)
    run = client.evals.runs.create(
        eval_id=eval_obj.id,
        name=Path(args.prompt).stem,
        data_source={
            "type": "completions",
            "source": {
                "type": "file_content",
                "content": [{"item": item} for item in dataset],
            },
            "input_messages": {
                "type": "template",
                "template": [
                    {
                        "type": "message",
                        "role": "system",
                        "content": {"type": "input_text", "text": prompt_text},
                    },
                    {
                        "type": "message",
                        "role": "user",
                        "content": {"type": "input_text", "text": "{{item.input}}"},
                    },
                ],
            },
            "model": args.model,
            "sampling_params": {"seed": 42, "temperature": 0.7},
        },
    )

    # Step 3: Poll for completion
    print("Waiting for eval to complete...", file=sys.stderr)
    while True:
        run_status = client.evals.runs.retrieve(eval_id=eval_obj.id, run_id=run.id)
        status = run_status.status
        print(f"  Status: {status}", file=sys.stderr)
        if status in ("completed", "failed", "canceled"):
            break
        time.sleep(5)

    if status != "completed":
        print(f"Eval run {status}.", file=sys.stderr)
        sys.exit(1)

    # Step 4: Retrieve results
    print("Retrieving results...", file=sys.stderr)
    output_items = client.evals.runs.output_items.list(eval_id=eval_obj.id, run_id=run.id)

    results = []
    total_score = 0.0
    scores_by_category: dict[str, list[float]] = {}

    for item in output_items.data:
        # Map back to dataset row using the item data
        item_data = item.datasource_item
        raw_score = item.results[0].score if item.results else score_range[0]
        normalized = normalize_score(raw_score, score_range)

        actual_output = ""
        if hasattr(item, "sample") and item.sample:
            actual_output = item.sample.output_text or ""

        reasoning = ""
        if item.results and hasattr(item.results[0], "reasoning"):
            reasoning = item.results[0].reasoning or ""

        result = {
            "input": item_data.get("input", ""),
            "expected_output": item_data.get("expected_output", ""),
            "actual_output": actual_output,
            "score": normalized,
            "raw_score": raw_score,
            "grader_reasoning": reasoning,
            "category": item_data.get("category", ""),
        }
        results.append(result)
        total_score += normalized

        cat = item_data.get("category", "") or "uncategorized"
        scores_by_category.setdefault(cat, []).append(normalized)

    overall_score = total_score / len(results) if results else 0.0
    category_averages = {
        cat: round(sum(scores) / len(scores), 4)
        for cat, scores in scores_by_category.items()
    }

    version = Path(args.prompt).stem
    output_data = {
        "version": version,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "overall_score": round(overall_score, 4),
        "scores_by_category": category_averages,
        "total_rows": len(results),
        "eval_id": eval_obj.id,
        "run_id": run.id,
        "report_url": getattr(run_status, "report_url", None),
        "results": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
    print(f"Evaluation complete. Overall score: {overall_score:.4f}", file=sys.stderr)
    print(json.dumps({"overall_score": overall_score, "scores_by_category": category_averages}))


if __name__ == "__main__":
    main()
