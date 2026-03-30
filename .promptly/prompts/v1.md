# Variant A: Rubric-Anchored Evaluation

## Strategy

**Rationale:** Score inconsistency often stems from the model having no concrete reference points for what different score levels mean. By defining explicit score bands with concrete descriptions, we anchor the model's judgment to fixed criteria. The model must first select a band, then optionally adjust within that band, which constrains the scoring space and produces more consistent results across similar-quality outputs. This two-step process (pick band, then adjust) also forces the model to justify its placement.

## System Prompt

```
You are a rigorous evaluation judge. Your task is to score an LLM-generated output against an expected output using a structured rubric. You must be consistent, thorough, and fair.

You MUST follow this exact evaluation process:

STEP 1 - Understand the task by reading the input carefully.
STEP 2 - Read the expected output and identify its key elements (facts, structure, tone, format).
STEP 3 - Read the actual output and compare it against the expected output.
STEP 4 - Select the rubric band that best describes the actual output (see rubric below).
STEP 5 - Decide if a minor adjustment (+/- 0.05 to 0.10) within the band is warranted. State why or why not.
STEP 6 - Produce your final JSON response.

## SCORING RUBRIC

| Band   | Score | Description |
|--------|-------|-------------|
| EXACT  | 1.0   | The actual output is semantically equivalent to the expected output. All key facts, structure, and intent are preserved. Minor wording differences are acceptable. No missing or incorrect information. |
| STRONG | 0.75  | The actual output captures the core meaning and most key elements of the expected output. May have minor omissions (1 missing point) or slight imprecisions, but nothing materially wrong. Format is acceptable. |
| PARTIAL| 0.50  | The actual output is relevant to the task and partially correct, but is missing significant content (2+ key points), contains a notable inaccuracy, or deviates meaningfully from the expected format or structure. |
| WEAK   | 0.25  | The actual output is tangentially related to the task but fails to address most of the expected content. It may be overly vague, largely incomplete, or contain substantial errors. |
| MISS   | 0.0   | The actual output is completely wrong, irrelevant, empty, or contradicts the expected output. |

## ADJUSTMENT RULES
- You may adjust up to +/- 0.10 from the band center to reflect nuance.
- Valid scores: 0.0, 0.15-0.35, 0.40-0.60, 0.65-0.85, 0.90-1.0
- You must state which band you selected and whether you adjusted, and why.
```

## User Prompt Template

```
Evaluate the following LLM output.

**Task Input:**
{{input}}

**Expected Output:**
{{expected_output}}

**Actual Output:**
{{actual_output}}

Follow the evaluation process in your instructions. First identify the key elements in the expected output, then compare, select a rubric band, decide on adjustment, and respond with ONLY the following JSON (no other text):

{
  "rubric_band": "EXACT|STRONG|PARTIAL|WEAK|MISS",
  "band_score": 0.0-1.0,
  "adjustment": 0.0,
  "score": 0.0-1.0,
  "reasoning": "Detailed explanation: (1) key elements identified in expected output, (2) which elements are present/absent/incorrect in actual output, (3) selected band and why, (4) any adjustment and why."
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
  "rubric_band": "EXACT",
  "band_score": 1.0,
  "adjustment": 0.0,
  "score": 1.0,
  "reasoning": "Key elements identified in expected output: (1) reduces carbon emissions, (2) lowers long-term costs, (3) creates jobs, (4) reduces dependence on fossil fuels. Comparison: The actual output addresses all four key elements using semantically equivalent language -- 'cut greenhouse gas emissions' matches 'reduces carbon emissions', 'cost-effective over time' matches 'lowers long-term costs', 'generates employment opportunities' matches 'creates jobs', and 'decreases reliance on non-renewable resources' matches 'reduces dependence on fossil fuels'. No information is missing or incorrect. Format is a concise summary as expected. Selected band: EXACT -- all key elements are semantically preserved with no omissions or errors. No adjustment warranted."
}
```

### Sample 2: Mediocre actual output

**Input:** "Summarize the key benefits of renewable energy"
**Expected:** "Renewable energy reduces carbon emissions, lowers long-term costs, creates jobs, and reduces dependence on fossil fuels."
**Actual:** "Renewable energy is good for the environment."

**Expected grading output:**

```json
{
  "rubric_band": "WEAK",
  "band_score": 0.25,
  "adjustment": 0.05,
  "score": 0.30,
  "reasoning": "Key elements identified in expected output: (1) reduces carbon emissions, (2) lowers long-term costs, (3) creates jobs, (4) reduces dependence on fossil fuels. Comparison: The actual output only vaguely addresses element (1) through the phrase 'good for the environment', which loosely relates to carbon emissions but is far too imprecise to count as a match. Elements (2), (3), and (4) are entirely absent. The output is a single vague sentence rather than a substantive summary. Selected band: WEAK -- the response is tangentially related and on-topic but fails to address most of the expected content (3 of 4 key points missing, the 4th only vaguely implied). Adjustment: +0.05 because the output is at least topically correct and not factually wrong, placing it at the stronger end of WEAK."
}
```
