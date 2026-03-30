#!/usr/bin/env python3
"""
Evaluate a judge prompt by spawning Claude CLI instances.
Usage: python3 run_eval.py <prompt_version> [--concurrency N] [--model MODEL]
"""

import asyncio
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # .promptly/

DEFAULT_CONCURRENCY = 5
DEFAULT_MODEL = "haiku"


def load_prompt(version: str) -> tuple[str, str]:
    """Load system and user prompt templates from a version file."""
    prompt_file = BASE_DIR / "prompts" / f"{version}.md"
    content = prompt_file.read_text()

    # Extract code blocks - first is system prompt, second is user template
    blocks = []
    in_block = False
    current = []
    for line in content.split("\n"):
        if line.strip().startswith("```") and not in_block:
            in_block = True
            continue
        elif line.strip() == "```" and in_block:
            in_block = False
            blocks.append("\n".join(current))
            current = []
            continue
        if in_block:
            current.append(line)

    if len(blocks) < 2:
        print(f"Error: Expected at least 2 code blocks in {prompt_file}, found {len(blocks)}")
        sys.exit(1)

    return blocks[0], blocks[1]


def load_dataset(path: Path) -> list[dict]:
    """Load CSV dataset."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def build_user_message(template: str, row: dict) -> str:
    """Fill in template variables."""
    msg = template
    msg = msg.replace("{{input}}", row["input"])
    msg = msg.replace("{{expected_output}}", row["expected_output"])
    msg = msg.replace("{{actual_output}}", row["actual_output"])
    return msg


async def evaluate_row(
    sem: asyncio.Semaphore,
    index: int,
    row: dict,
    system_prompt: str,
    user_template: str,
    model: str,
) -> dict:
    """Evaluate a single row by spawning a Claude CLI instance."""
    async with sem:
        user_msg = build_user_message(user_template, row)

        json_schema = json.dumps({
            "type": "object",
            "properties": {
                "rubric_band": {"type": "string", "enum": ["EXACT", "STRONG", "PARTIAL", "WEAK", "MISS"]},
                "band_score": {"type": "number"},
                "adjustment": {"type": "number"},
                "score": {"type": "number"},
                "reasoning": {"type": "string"},
            },
            "required": ["score", "reasoning"],
        })

        cmd = [
            "claude",
            "-p", user_msg,
            "--model", model,
            "--system-prompt", system_prompt,
            "--output-format", "json",
            "--no-session-persistence",
            "--tools", "",
        ]

        result = {
            "index": index,
            "input": row["input"][:200],
            "expected_output": row["expected_output"][:200],
            "actual_output": row["actual_output"][:200],
            "expected_score": float(row["expected_score"]),
            "category": row["category"],
            "predicted_score": None,
            "reasoning": None,
            "rubric_band": None,
            "error": None,
        }

        for attempt in range(3):
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

                if proc.returncode != 0:
                    err = stderr.decode().strip()
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    result["error"] = f"CLI error (exit {proc.returncode}): {err[:200]}"
                    break

                output = stdout.decode().strip()
                # Parse the CLI JSON output - extract the result field
                cli_response = json.loads(output)
                response_text = cli_response.get("result", output)

                # Strip markdown code fences if present
                cleaned = response_text.strip()
                fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', cleaned, re.DOTALL)
                if fence_match:
                    cleaned = fence_match.group(1).strip()

                # Try to parse the judge's JSON response
                try:
                    judge_output = json.loads(cleaned)
                except json.JSONDecodeError:
                    # Try to find JSON object with "score" key
                    json_match = re.search(r'\{[^{}]*"score"\s*:\s*[\d.]+[^{}]*\}', response_text)
                    if json_match:
                        judge_output = json.loads(json_match.group())
                    else:
                        result["error"] = f"Could not parse JSON from response: {response_text[:200]}"
                        break

                result["predicted_score"] = float(judge_output["score"])
                result["reasoning"] = judge_output.get("reasoning", "")
                result["rubric_band"] = judge_output.get("rubric_band", "")

                status = "✓" if abs(result["predicted_score"] - result["expected_score"]) <= 0.15 else "✗"
                print(f"  [{index+1:3d}] {status} expected={result['expected_score']:.2f} predicted={result['predicted_score']:.2f} band={result['rubric_band']} cat={result['category']}")
                break

            except asyncio.TimeoutError:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                result["error"] = "Timeout after 120s"
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                result["error"] = str(e)[:200]

        return result


def compute_metrics(results: list[dict]) -> dict:
    """Compute evaluation metrics."""
    valid = [r for r in results if r["predicted_score"] is not None]
    if not valid:
        return {"error": "No valid results"}

    expected = [r["expected_score"] for r in valid]
    predicted = [r["predicted_score"] for r in valid]

    # MAE
    mae = sum(abs(e - p) for e, p in zip(expected, predicted)) / len(valid)

    # Pearson correlation
    n = len(valid)
    mean_e = sum(expected) / n
    mean_p = sum(predicted) / n
    cov = sum((e - mean_e) * (p - mean_p) for e, p in zip(expected, predicted)) / n
    std_e = (sum((e - mean_e) ** 2 for e in expected) / n) ** 0.5
    std_p = (sum((p - mean_p) ** 2 for p in predicted) / n) ** 0.5
    correlation = cov / (std_e * std_p) if std_e > 0 and std_p > 0 else 0.0

    # Agreement rate (within 0.15)
    agreement = sum(1 for e, p in zip(expected, predicted) if abs(e - p) <= 0.15) / len(valid)

    # Per-category metrics
    categories = set(r["category"] for r in valid)
    by_category = {}
    for cat in sorted(categories):
        cat_rows = [r for r in valid if r["category"] == cat]
        cat_e = [r["expected_score"] for r in cat_rows]
        cat_p = [r["predicted_score"] for r in cat_rows]
        cat_mae = sum(abs(e - p) for e, p in zip(cat_e, cat_p)) / len(cat_rows)

        # Category correlation
        cn = len(cat_rows)
        if cn > 2:
            cm_e = sum(cat_e) / cn
            cm_p = sum(cat_p) / cn
            c_cov = sum((e - cm_e) * (p - cm_p) for e, p in zip(cat_e, cat_p)) / cn
            c_std_e = (sum((e - cm_e) ** 2 for e in cat_e) / cn) ** 0.5
            c_std_p = (sum((p - cm_p) ** 2 for p in cat_p) / cn) ** 0.5
            c_corr = c_cov / (c_std_e * c_std_p) if c_std_e > 0 and c_std_p > 0 else 0.0
        else:
            c_corr = None

        by_category[cat] = {"mae": round(cat_mae, 4), "correlation": round(c_corr, 4) if c_corr is not None else None, "count": cn}

    # Score distribution
    dist = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
    for p in predicted:
        if p < 0.2: dist["0.0-0.2"] += 1
        elif p < 0.4: dist["0.2-0.4"] += 1
        elif p < 0.6: dist["0.4-0.6"] += 1
        elif p < 0.8: dist["0.6-0.8"] += 1
        else: dist["0.8-1.0"] += 1

    # Major disagreements
    disagreements = []
    for r in valid:
        diff = abs(r["predicted_score"] - r["expected_score"])
        if diff >= 0.5:
            disagreements.append({
                "index": r["index"],
                "expected": r["expected_score"],
                "predicted": r["predicted_score"],
                "direction": "over" if r["predicted_score"] > r["expected_score"] else "under",
                "category": r["category"],
                "reasoning": (r["reasoning"] or "")[:300],
            })
    disagreements.sort(key=lambda x: abs(x["expected"] - x["predicted"]), reverse=True)

    return {
        "overall_mae": round(mae, 4),
        "overall_correlation": round(correlation, 4),
        "agreement_rate": round(agreement, 4),
        "total_rows": len(results),
        "valid_rows": len(valid),
        "error_rows": len(results) - len(valid),
        "scores_by_category": by_category,
        "score_distribution": dist,
        "major_disagreements": disagreements[:10],
    }


async def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "v1"
    concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_CONCURRENCY
    model = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_MODEL

    print(f"=== Evaluating {version} with model={model}, concurrency={concurrency} ===")

    system_prompt, user_template = load_prompt(version)
    dataset = load_dataset(BASE_DIR / "datasets" / "judges-verdict.csv")
    print(f"Loaded {len(dataset)} rows")

    sem = asyncio.Semaphore(concurrency)
    start = time.time()

    tasks = [
        evaluate_row(sem, i, row, system_prompt, user_template, model)
        for i, row in enumerate(dataset)
    ]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    print(f"\nCompleted in {elapsed:.1f}s")

    metrics = compute_metrics(results)

    # Save results
    output = {
        "version": version,
        "prompt_file": f".promptly/prompts/{version}.md",
        "dataset_file": ".promptly/datasets/judges-verdict.csv",
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "metrics": metrics,
        "rows": results,
    }

    results_file = BASE_DIR / "results" / f"{version}.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(output, indent=2, default=str))

    # Update state
    state_file = BASE_DIR / "state.json"
    state = json.loads(state_file.read_text())
    iter_num = int(version.replace("v", "")) if version.startswith("v") else 0
    state["current_version"] = iter_num
    state["status"] = "paused"
    if "overall_mae" in metrics:
        score = round(1 - metrics["overall_mae"], 4)
        if score > state.get("best_score", 0):
            state["best_score"] = score
            state["best_version"] = version
    state_file.write_text(json.dumps(state, indent=2))

    # Print summary
    print(f"\n{'='*60}")
    print(f"RESULTS: {version}")
    print(f"{'='*60}")
    print(f"Overall MAE:         {metrics['overall_mae']:.4f}")
    print(f"Overall Correlation: {metrics['overall_correlation']:.4f}")
    print(f"Agreement Rate:      {metrics['agreement_rate']:.1%}")
    print(f"Valid/Total:         {metrics['valid_rows']}/{metrics['total_rows']}")
    print(f"\nPer-Category:")
    for cat, m in metrics["scores_by_category"].items():
        corr_str = f"{m['correlation']:.4f}" if m['correlation'] is not None else "N/A"
        print(f"  {cat:20s} MAE={m['mae']:.4f}  corr={corr_str}  n={m['count']}")
    print(f"\nScore Distribution (predicted):")
    for bucket, count in metrics["score_distribution"].items():
        print(f"  {bucket}: {'█' * count} ({count})")
    if metrics["major_disagreements"]:
        print(f"\nTop Disagreements (|diff| >= 0.5):")
        for d in metrics["major_disagreements"][:5]:
            print(f"  [{d['index']}] expected={d['expected']:.2f} predicted={d['predicted']:.2f} ({d['direction']}) cat={d['category']}")
            print(f"       {d['reasoning'][:100]}")
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
