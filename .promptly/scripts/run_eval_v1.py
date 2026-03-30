#!/usr/bin/env python3
"""Evaluate v1 judge prompt against the judges-verdict dataset."""

import asyncio
import csv
import json
import os
import re
import time
from datetime import datetime, timezone
from statistics import mean

import anthropic

BASE = "/Users/droshima/Documents/code/llms/skills/.promptly"
PROMPT_FILE = f"{BASE}/prompts/v1.md"
DATASET_FILE = f"{BASE}/datasets/judges-verdict.csv"
OUTPUT_FILE = f"{BASE}/results/v1.json"
STATE_FILE = f"{BASE}/state.json"
MODEL = "claude-haiku-4-5-20251001"
CONCURRENCY = 10
MAX_RETRIES = 3

# ── Extract prompts from v1.md ──────────────────────────────────────────

def load_prompts():
    with open(PROMPT_FILE) as f:
        content = f.read()

    # Extract code blocks - first is system prompt, second is user template
    blocks = re.findall(r'```\n(.*?)```', content, re.DOTALL)
    system_prompt = blocks[0].strip()
    user_template = blocks[1].strip()
    return system_prompt, user_template


# ── Load dataset ────────────────────────────────────────────────────────

def load_dataset():
    rows = []
    with open(DATASET_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            rows.append({
                "index": i,
                "input": row["input"],
                "expected_output": row["expected_output"],
                "actual_output": row["actual_output"],
                "expected_score": float(row["expected_score"]),
                "category": row["category"],
            })
    return rows


# ── Call API ────────────────────────────────────────────────────────────

async def grade_row(client, sem, system_prompt, user_template, row):
    user_msg = user_template.replace("{{input}}", row["input"])
    user_msg = user_msg.replace("{{expected_output}}", row["expected_output"])
    user_msg = user_msg.replace("{{actual_output}}", row["actual_output"])

    for attempt in range(MAX_RETRIES):
        try:
            async with sem:
                response = await client.messages.create(
                    model=MODEL,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_msg}],
                )
            text = response.content[0].text.strip()

            # Try to parse JSON
            try:
                # Try to find JSON in the response
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    parsed = json.loads(json_match.group())
                else:
                    raise ValueError("No JSON found")

                score = float(parsed.get("score", -1))
                reasoning = parsed.get("reasoning", "")
                if score < 0 or score > 1:
                    raise ValueError(f"Score out of range: {score}")

                return {
                    "index": row["index"],
                    "input": row["input"][:200],
                    "expected_output": row["expected_output"][:200],
                    "actual_output": row["actual_output"][:200],
                    "expected_score": row["expected_score"],
                    "predicted_score": score,
                    "reasoning": reasoning[:500],
                    "category": row["category"],
                    "error": None,
                }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Try to extract score from text
                score_match = re.search(r'"score"\s*:\s*([\d.]+)', text)
                if score_match:
                    score = float(score_match.group(1))
                    return {
                        "index": row["index"],
                        "input": row["input"][:200],
                        "expected_output": row["expected_output"][:200],
                        "actual_output": row["actual_output"][:200],
                        "expected_score": row["expected_score"],
                        "predicted_score": score,
                        "reasoning": text[:500],
                        "category": row["category"],
                        "error": None,
                    }
                if attempt == MAX_RETRIES - 1:
                    return {
                        "index": row["index"],
                        "input": row["input"][:200],
                        "expected_output": row["expected_output"][:200],
                        "actual_output": row["actual_output"][:200],
                        "expected_score": row["expected_score"],
                        "predicted_score": None,
                        "reasoning": text[:500],
                        "category": row["category"],
                        "error": f"JSON parse error: {e}",
                    }
        except anthropic.RateLimitError:
            wait = 2 ** (attempt + 1)
            print(f"  Rate limited on row {row['index']}, waiting {wait}s...")
            await asyncio.sleep(wait)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                return {
                    "index": row["index"],
                    "input": row["input"][:200],
                    "expected_output": row["expected_output"][:200],
                    "actual_output": row["actual_output"][:200],
                    "expected_score": row["expected_score"],
                    "predicted_score": None,
                    "reasoning": "",
                    "category": row["category"],
                    "error": str(e)[:200],
                }
            await asyncio.sleep(2 ** attempt)

    # Should not reach here
    return None


async def main():
    print("Loading prompts and dataset...")
    system_prompt, user_template = load_prompts()
    dataset = load_dataset()
    print(f"Loaded {len(dataset)} rows")

    client = anthropic.AsyncAnthropic()
    sem = asyncio.Semaphore(CONCURRENCY)

    print(f"Running evaluation with concurrency={CONCURRENCY}...")
    start = time.time()

    tasks = [grade_row(client, sem, system_prompt, user_template, row) for row in dataset]
    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start
    print(f"Evaluation complete in {elapsed:.1f}s")

    # ── Compute metrics ─────────────────────────────────────────────────

    valid = [r for r in results if r["predicted_score"] is not None]
    errors = [r for r in results if r["predicted_score"] is None]
    print(f"Valid: {len(valid)}, Errors: {len(errors)}")

    if not valid:
        print("No valid results!")
        return

    # Overall MAE
    abs_errors = [abs(r["predicted_score"] - r["expected_score"]) for r in valid]
    overall_mae = mean(abs_errors)

    # Pearson correlation
    pred = [r["predicted_score"] for r in valid]
    exp = [r["expected_score"] for r in valid]
    n = len(valid)
    mean_pred = mean(pred)
    mean_exp = mean(exp)
    cov = sum((p - mean_pred) * (e - mean_exp) for p, e in zip(pred, exp)) / n
    std_pred = (sum((p - mean_pred) ** 2 for p in pred) / n) ** 0.5
    std_exp = (sum((e - mean_exp) ** 2 for e in exp) / n) ** 0.5
    correlation = cov / (std_pred * std_exp) if std_pred * std_exp > 0 else 0.0

    # Agreement rate (within 0.15)
    agreement = sum(1 for r in valid if abs(r["predicted_score"] - r["expected_score"]) <= 0.15) / len(valid)

    # Per-category metrics
    categories = {}
    for r in valid:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"pred": [], "exp": []}
        categories[cat]["pred"].append(r["predicted_score"])
        categories[cat]["exp"].append(r["expected_score"])

    scores_by_category = {}
    for cat, data in categories.items():
        cat_errors = [abs(p - e) for p, e in zip(data["pred"], data["exp"])]
        cat_mae = mean(cat_errors)
        # Correlation
        n_c = len(data["pred"])
        if n_c > 1:
            mp = mean(data["pred"])
            me = mean(data["exp"])
            cov_c = sum((p - mp) * (e - me) for p, e in zip(data["pred"], data["exp"])) / n_c
            sp = (sum((p - mp) ** 2 for p in data["pred"]) / n_c) ** 0.5
            se = (sum((e - me) ** 2 for e in data["exp"]) / n_c) ** 0.5
            corr_c = cov_c / (sp * se) if sp * se > 0 else 0.0
        else:
            corr_c = 0.0
        scores_by_category[cat] = {"mae": round(cat_mae, 4), "correlation": round(corr_c, 4), "count": n_c}

    # Score distribution
    dist = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
    for r in valid:
        s = r["predicted_score"]
        if s < 0.2:
            dist["0.0-0.2"] += 1
        elif s < 0.4:
            dist["0.2-0.4"] += 1
        elif s < 0.6:
            dist["0.4-0.6"] += 1
        elif s < 0.8:
            dist["0.6-0.8"] += 1
        else:
            dist["0.8-1.0"] += 1

    # Major disagreements
    major_disagreements = []
    for r in valid:
        p, e = r["predicted_score"], r["expected_score"]
        if p >= 0.75 and e <= 0.25:
            major_disagreements.append({
                "index": r["index"], "expected": e, "predicted": p,
                "direction": "over", "reasoning": r["reasoning"]
            })
        elif p <= 0.25 and e >= 0.75:
            major_disagreements.append({
                "index": r["index"], "expected": e, "predicted": p,
                "direction": "under", "reasoning": r["reasoning"]
            })

    # Sort by severity
    major_disagreements.sort(key=lambda x: abs(x["predicted"] - x["expected"]), reverse=True)

    # ── Save results ────────────────────────────────────────────────────

    output = {
        "version": "v1",
        "prompt_file": ".promptly/prompts/v1.md",
        "dataset_file": ".promptly/datasets/judges-verdict.csv",
        "model": MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "metrics": {
            "overall_mae": round(overall_mae, 4),
            "overall_correlation": round(correlation, 4),
            "agreement_rate": round(agreement, 4),
            "scores_by_category": scores_by_category,
            "score_distribution": dist,
        },
        "rows": results,
        "major_disagreements": major_disagreements,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved to {OUTPUT_FILE}")

    # ── Update state ────────────────────────────────────────────────────

    # Use agreement_rate as the "score" for tracking best version
    best_score = agreement
    with open(STATE_FILE) as f:
        state = json.load(f)
    state["current_iteration"] = 1
    state["current_version"] = 1
    state["status"] = "paused"
    state["best_score"] = round(best_score, 4)
    state["best_version"] = "v1"
    state["iterations"] = [{
        "version": "v1",
        "mae": round(overall_mae, 4),
        "correlation": round(correlation, 4),
        "agreement_rate": round(agreement, 4),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }]
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    print(f"State updated")

    # ── Print summary ───────────────────────────────────────────────────

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY - v1")
    print("=" * 60)
    print(f"Overall MAE:         {overall_mae:.4f}")
    print(f"Overall Correlation: {correlation:.4f}")
    print(f"Agreement Rate:      {agreement:.2%} (within 0.15)")
    print(f"Valid/Total:         {len(valid)}/{len(results)}")
    print(f"Errors:              {len(errors)}")
    print()
    print("Score Distribution (predicted):")
    for bucket, count in dist.items():
        bar = "#" * (count // 2)
        print(f"  {bucket}: {count:3d} {bar}")
    print()
    print("Per-Category Breakdown:")
    print(f"  {'Category':<16} {'MAE':>6} {'Corr':>6} {'Count':>6}")
    print(f"  {'-'*16} {'-'*6} {'-'*6} {'-'*6}")
    for cat, m in sorted(scores_by_category.items()):
        print(f"  {cat:<16} {m['mae']:>6.4f} {m['correlation']:>6.4f} {m['count']:>6}")
    print()
    print(f"Major Disagreements: {len(major_disagreements)}")
    for d in major_disagreements[:5]:
        print(f"  Row {d['index']:3d}: expected={d['expected']:.2f} predicted={d['predicted']:.2f} ({d['direction']})")
        print(f"          {d['reasoning'][:120]}...")
    print()


if __name__ == "__main__":
    asyncio.run(main())
