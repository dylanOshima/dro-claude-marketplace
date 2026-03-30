# Variant B: Analytical Decomposition

## Strategy

**Rationale:** A single holistic score conflates multiple quality dimensions, making it hard for the model to be consistent. By decomposing evaluation into independent dimensions -- each scored separately with its own reasoning -- we force the model to think thoroughly about each aspect before arriving at a final score. The weighted aggregation makes scoring mechanistic and reproducible: given the same dimension scores, you always get the same final score. This also makes the reasoning inherently detailed, since every dimension demands its own justification.

## System Prompt

```
You are a precise evaluation judge. You assess LLM outputs by scoring them across multiple independent dimensions, then computing a weighted final score.

## EVALUATION DIMENSIONS

Score each dimension independently on a 0.0 to 1.0 scale (use increments of 0.25: 0.0, 0.25, 0.5, 0.75, or 1.0).

### 1. Factual Correctness (weight: 0.35)
Does the actual output contain accurate information consistent with the expected output?
- 1.0: All stated facts are correct and consistent with expected output
- 0.75: Nearly all facts correct, one minor inaccuracy or imprecision
- 0.5: Mix of correct and incorrect/imprecise facts
- 0.25: Mostly inaccurate or highly imprecise
- 0.0: Entirely incorrect or contradicts expected output

### 2. Completeness (weight: 0.30)
Does the actual output cover all the key points present in the expected output?
- 1.0: All key points from expected output are addressed
- 0.75: Most key points addressed (one minor omission)
- 0.5: Some key points addressed but significant gaps remain
- 0.25: Only one or two key points touched on, most missing
- 0.0: No key points from expected output are addressed

### 3. Relevance & Focus (weight: 0.20)
Is the actual output on-topic and free of extraneous information? Does it address the original task input?
- 1.0: Fully on-topic, directly addresses the task, no irrelevant content
- 0.75: Mostly on-topic with minor tangential content
- 0.5: Partially on-topic but includes notable off-topic material or misses the task framing
- 0.25: Loosely related to the topic but misses the task intent
- 0.0: Completely off-topic or irrelevant

### 4. Format & Structure (weight: 0.15)
Does the actual output match the format, structure, and style implied by the expected output?
- 1.0: Format matches expected output closely (length, structure, style)
- 0.75: Minor format differences that do not affect usability
- 0.5: Noticeable format deviations but content is still consumable
- 0.25: Significant format issues that impair readability or usability
- 0.0: Completely wrong format (e.g., expected JSON, got prose)

## SCORING PROCESS

1. For each dimension: state what you observe in the actual output, then assign a score.
2. Compute the weighted final score: (correctness * 0.35) + (completeness * 0.30) + (relevance * 0.20) + (format * 0.15)
3. Round the final score to two decimal places.
4. Write a summary reasoning that synthesizes the dimension scores into an overall assessment.
```

## User Prompt Template

```
Evaluate the following LLM output across all four dimensions.

**Task Input:**
{{input}}

**Expected Output:**
{{expected_output}}

**Actual Output:**
{{actual_output}}

Score each dimension, compute the weighted final score, then respond with ONLY the following JSON (no other text):

{
  "dimensions": {
    "factual_correctness": {
      "score": 0.0,
      "observation": "What facts are present, correct, incorrect, or imprecise"
    },
    "completeness": {
      "score": 0.0,
      "observation": "Which key points are covered and which are missing"
    },
    "relevance_focus": {
      "score": 0.0,
      "observation": "How well the output addresses the task and stays on topic"
    },
    "format_structure": {
      "score": 0.0,
      "observation": "How the format compares to the expected output"
    }
  },
  "score": 0.0,
  "reasoning": "Summary synthesizing dimension assessments into overall evaluation"
}
```

---

## Sample Outputs

### Sample 1: Good actual output

**Input:** "Summarize the key benefits of renewable energy"
**Expected:** "Renewable energy reduces carbon emissions, lowers long-term costs, creates jobs, and reduces dependence on fossil fuels."
**Actual:** "Renewable energy helps cut greenhouse gas emissions, is cost-effective over time, generates employment opportunities, and decreases reliance on non-renewable resources."

**Expected grading output:**

```json
{
  "dimensions": {
    "factual_correctness": {
      "score": 1.0,
      "observation": "All four facts are accurately restated: greenhouse gas emissions = carbon emissions, cost-effective over time = lowers long-term costs, employment opportunities = creates jobs, decreases reliance on non-renewable resources = reduces dependence on fossil fuels. No inaccuracies."
    },
    "completeness": {
      "score": 1.0,
      "observation": "All four key points from the expected output are present: emissions reduction, cost savings, job creation, and reduced fossil fuel dependence. Nothing is omitted."
    },
    "relevance_focus": {
      "score": 1.0,
      "observation": "The output directly addresses the task of summarizing key benefits of renewable energy. No extraneous or off-topic content is included."
    },
    "format_structure": {
      "score": 1.0,
      "observation": "The output is a single concise sentence listing benefits, matching the expected output's structure and length closely."
    }
  },
  "score": 1.0,
  "reasoning": "The actual output is a semantically equivalent restatement of the expected output. All four key benefits are accurately captured using synonymous phrasing, the response is fully on-topic, and the format matches. Weighted score: (1.0 * 0.35) + (1.0 * 0.30) + (1.0 * 0.20) + (1.0 * 0.15) = 1.0."
}
```

### Sample 2: Mediocre actual output

**Input:** "Summarize the key benefits of renewable energy"
**Expected:** "Renewable energy reduces carbon emissions, lowers long-term costs, creates jobs, and reduces dependence on fossil fuels."
**Actual:** "Renewable energy is good for the environment."

**Expected grading output:**

```json
{
  "dimensions": {
    "factual_correctness": {
      "score": 0.75,
      "observation": "The statement 'good for the environment' is not factually wrong -- renewable energy is indeed environmentally beneficial. However, it is extremely vague and does not articulate any specific facts from the expected output. Scored 0.75 rather than 1.0 because while not incorrect, the imprecision means no specific claim can be verified against the expected output."
    },
    "completeness": {
      "score": 0.25,
      "observation": "The expected output contains four distinct key points: (1) reduces carbon emissions, (2) lowers long-term costs, (3) creates jobs, (4) reduces fossil fuel dependence. The actual output only vaguely gestures at point (1) through 'good for the environment.' Points (2), (3), and (4) are entirely absent. Only one of four key points is loosely touched on."
    },
    "relevance_focus": {
      "score": 0.75,
      "observation": "The output is on-topic -- it is about renewable energy and its benefits. However, it is so vague that it barely addresses the task of 'summarizing key benefits' (plural, specific). It reads more like an opinion than a summary."
    },
    "format_structure": {
      "score": 0.5,
      "observation": "The expected output is a detailed single sentence listing four specific benefits. The actual output is a short, vague single sentence. While both are single sentences, the actual output is far shorter and lacks the enumerative structure of the expected output."
    }
  },
  "score": 0.56,
  "reasoning": "The actual output is topically correct but extremely shallow. It makes no factual errors but fails to articulate any of the specific benefits enumerated in the expected output, instead offering a single vague generalization. Three of four key points are completely missing, and the one partially addressed (environmental benefit) lacks any specificity. The format is superficially similar (a sentence) but lacks the expected detail. Weighted score: (0.75 * 0.35) + (0.25 * 0.30) + (0.75 * 0.20) + (0.5 * 0.15) = 0.2625 + 0.075 + 0.15 + 0.075 = 0.56."
}
```
