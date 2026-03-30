#!/usr/bin/env python3
"""Local Claude evaluation engine for Promptly.

Runs a prompt against a CSV dataset using the Anthropic SDK,
grades each output, and saves results as JSON.

Usage:
    python3 evaluate.py \
        --prompt .promptly/prompts/v1.md \
        --dataset .promptly/datasets/run-xxx.csv \
        --output .promptly/results/v1.json \
        --model claude-sonnet-4-20250514 \
        [--judge-model claude-haiku-4-5-20251001] \
        [--grading-method model_judge|exact|contains|fuzzy|rouge_l]
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Error: anthropic SDK not installed. Run: pip install anthropic", file=sys.stderr)
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


def run_prompt(client: anthropic.Anthropic, model: str, prompt: str, input_text: str) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[
            {"role": "user", "content": f"{prompt}\n\n{input_text}"}
        ],
    )
    return response.content[0].text


def grade_model_judge(
    client: anthropic.Anthropic,
    judge_model: str,
    input_text: str,
    expected: str,
    actual: str,
) -> dict:
    grading_prompt = f"""Grade the following output on a scale of 0.0 to 1.0.

Task Input: {input_text}
Expected Output: {expected}
Actual Output: {actual}

Score based on:
- Correctness: Does it match the expected output semantically?
- Completeness: Does it cover all required information?
- Format: Does it follow the expected format?

Respond with JSON only:
{{"score": <float 0.0-1.0>, "reasoning": "<brief explanation>"}}"""

    response = client.messages.create(
        model=judge_model,
        max_tokens=512,
        messages=[{"role": "user", "content": grading_prompt}],
    )
    text = response.content[0].text.strip()
    # Extract JSON from response
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    return {"score": 0.0, "reasoning": "Failed to parse grading response"}


def grade_exact(expected: str, actual: str) -> dict:
    match = expected.strip().lower() == actual.strip().lower()
    return {"score": 1.0 if match else 0.0, "reasoning": "Exact match" if match else "No match"}


def grade_contains(expected: str, actual: str) -> dict:
    found = expected.strip().lower() in actual.strip().lower()
    return {"score": 1.0 if found else 0.0, "reasoning": "Contains expected" if found else "Missing expected"}


def grade_fuzzy(expected: str, actual: str) -> dict:
    # Simple character-level similarity
    a, b = expected.strip().lower(), actual.strip().lower()
    if not a and not b:
        return {"score": 1.0, "reasoning": "Both empty"}
    max_len = max(len(a), len(b))
    if max_len == 0:
        return {"score": 1.0, "reasoning": "Both empty"}
    # Longest common subsequence ratio
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    lcs_len = dp[m][n]
    score = lcs_len / max_len
    return {"score": round(score, 3), "reasoning": f"LCS similarity: {score:.3f}"}


def main():
    parser = argparse.ArgumentParser(description="Evaluate prompt against dataset using Claude")
    parser.add_argument("--prompt", required=True, help="Path to prompt file")
    parser.add_argument("--dataset", required=True, help="Path to CSV dataset")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Model for running the prompt")
    parser.add_argument("--judge-model", default="claude-haiku-4-5-20251001", help="Model for grading")
    parser.add_argument("--grading-method", default="model_judge",
                        choices=["model_judge", "exact", "contains", "fuzzy"])
    args = parser.parse_args()

    client = anthropic.Anthropic()
    prompt = load_prompt(args.prompt)
    dataset = load_dataset(args.dataset)

    graders = {
        "model_judge": lambda inp, exp, act: grade_model_judge(client, args.judge_model, inp, exp, act),
        "exact": lambda _inp, exp, act: grade_exact(exp, act),
        "contains": lambda _inp, exp, act: grade_contains(exp, act),
        "fuzzy": lambda _inp, exp, act: grade_fuzzy(exp, act),
    }
    grade_fn = graders[args.grading_method]

    results = []
    total_score = 0.0
    scores_by_category: dict[str, list[float]] = {}

    for i, row in enumerate(dataset):
        print(f"Evaluating {i + 1}/{len(dataset)}...", file=sys.stderr)
        actual_output = run_prompt(client, args.model, prompt, row["input"])
        grade = grade_fn(row["input"], row["expected_output"], actual_output)

        result = {
            "input": row["input"],
            "expected_output": row["expected_output"],
            "actual_output": actual_output,
            "score": grade["score"],
            "grader_reasoning": grade["reasoning"],
            "category": row["category"],
        }
        results.append(result)
        total_score += grade["score"]

        cat = row["category"] or "uncategorized"
        scores_by_category.setdefault(cat, []).append(grade["score"])

    overall_score = total_score / len(dataset) if dataset else 0.0
    category_averages = {
        cat: round(sum(scores) / len(scores), 4)
        for cat, scores in scores_by_category.items()
    }

    # Extract version from prompt path
    prompt_name = Path(args.prompt).stem
    output_data = {
        "version": prompt_name,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "overall_score": round(overall_score, 4),
        "scores_by_category": category_averages,
        "total_rows": len(dataset),
        "results": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
    print(f"Evaluation complete. Overall score: {overall_score:.4f}", file=sys.stderr)
    print(json.dumps({"overall_score": overall_score, "scores_by_category": category_averages}))


if __name__ == "__main__":
    main()
