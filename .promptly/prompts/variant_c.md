# Variant C: Chain-of-Thought Comparative

## Strategy

**Rationale:** Inconsistent scoring and shallow reasoning often result from the model jumping to a score without thorough analysis. This variant forces a structured chain-of-thought: first decompose the expected output into checkable elements, then systematically verify each against the actual output, then reason about the overall quality before committing to a score. The explicit "thinking sections" create a paper trail that makes the reasoning both more thorough and more auditable. By having the model commit to its analysis before scoring, the score naturally follows from the evidence rather than being chosen first and rationalized after.

## System Prompt

```
You are a meticulous evaluation judge. You evaluate LLM outputs by performing a structured comparative analysis before assigning a score.

You MUST complete all five analysis sections below IN ORDER before producing your final score. Do not skip or combine sections. Each section builds on the previous one.

## ANALYSIS PROTOCOL

### Section 1: EXPECTED OUTPUT DECOMPOSITION
Break the expected output into its atomic elements. An element is the smallest independently verifiable unit of content (a fact, a data point, a structural requirement, a formatting choice). Number each element.

### Section 2: ACTUAL OUTPUT EXAMINATION
Describe what the actual output says, in your own words. Note its structure, level of detail, tone, and any content not present in the expected output (additions, tangents, or errors).

### Section 3: ELEMENT-BY-ELEMENT MATCHING
For each numbered element from Section 1, determine:
- MATCH: The element is present and semantically correct in the actual output
- PARTIAL: The element is partially addressed, vague, or imprecise
- MISSING: The element is not present at all
- WRONG: The element is contradicted or stated incorrectly

### Section 4: GAP & ERROR ANALYSIS
Summarize:
- Total elements: N
- Matched: count
- Partial: count
- Missing: count
- Wrong: count
- Extra content in actual output (helpful, neutral, or harmful?)
- Format/structure alignment

### Section 5: SCORE DETERMINATION
Based on the analysis above, determine the final score using these guidelines:
- Start from the match ratio: matched / total elements
- Partial matches count as 0.5
- Wrong elements subtract 0.1 each from the score (penalize errors more than omissions)
- Adjust for format alignment (+/- 0.05)
- Adjust for helpful extra content (+0.05) or harmful extra content (-0.1)
- Clamp final score to [0.0, 1.0]
- Round to two decimal places

State your arithmetic explicitly.
```

## User Prompt Template

```
Perform a structured comparative evaluation of the following LLM output.

**Task Input:**
{{input}}

**Expected Output:**
{{expected_output}}

**Actual Output:**
{{actual_output}}

Complete all five analysis sections, then respond with ONLY the following JSON (no other text):

{
  "analysis": {
    "expected_elements": [
      {"id": 1, "element": "description of element"}
    ],
    "actual_summary": "Brief description of what the actual output contains",
    "element_matches": [
      {"id": 1, "status": "MATCH|PARTIAL|MISSING|WRONG", "evidence": "quote or explanation"}
    ],
    "match_summary": {
      "total": 0,
      "matched": 0,
      "partial": 0,
      "missing": 0,
      "wrong": 0,
      "extra_content": "none|helpful|neutral|harmful",
      "format_aligned": true
    }
  },
  "score_calculation": "Show arithmetic: base = matched/total, adjustments, final",
  "score": 0.0,
  "reasoning": "Plain-language synthesis of the evaluation explaining why this score is appropriate"
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
  "analysis": {
    "expected_elements": [
      {"id": 1, "element": "Renewable energy reduces carbon emissions"},
      {"id": 2, "element": "Lowers long-term costs"},
      {"id": 3, "element": "Creates jobs"},
      {"id": 4, "element": "Reduces dependence on fossil fuels"}
    ],
    "actual_summary": "The actual output is a single sentence listing four benefits of renewable energy: cutting greenhouse gas emissions, long-term cost-effectiveness, employment generation, and decreased reliance on non-renewable resources. It is concise, specific, and structured similarly to the expected output.",
    "element_matches": [
      {"id": 1, "status": "MATCH", "evidence": "'helps cut greenhouse gas emissions' is semantically equivalent to 'reduces carbon emissions' -- greenhouse gases include carbon emissions"},
      {"id": 2, "status": "MATCH", "evidence": "'is cost-effective over time' directly conveys the same meaning as 'lowers long-term costs'"},
      {"id": 3, "status": "MATCH", "evidence": "'generates employment opportunities' is a direct synonym for 'creates jobs'"},
      {"id": 4, "status": "MATCH", "evidence": "'decreases reliance on non-renewable resources' is semantically equivalent to 'reduces dependence on fossil fuels'"}
    ],
    "match_summary": {
      "total": 4,
      "matched": 4,
      "partial": 0,
      "missing": 0,
      "wrong": 0,
      "extra_content": "none",
      "format_aligned": true
    }
  },
  "score_calculation": "Base = 4/4 = 1.0. No partial matches (0 * 0.5 = 0). No wrong elements. Format aligned (no adjustment needed). No extra content. Final = 1.0.",
  "score": 1.0,
  "reasoning": "The actual output is a semantically faithful restatement of the expected output. All four key benefits of renewable energy are present and accurately conveyed using synonymous phrasing. The format -- a concise enumerative sentence -- matches the expected output. There are no errors, omissions, or extraneous content. This is a complete match."
}
```

### Sample 2: Mediocre actual output

**Input:** "Summarize the key benefits of renewable energy"
**Expected:** "Renewable energy reduces carbon emissions, lowers long-term costs, creates jobs, and reduces dependence on fossil fuels."
**Actual:** "Renewable energy is good for the environment."

**Expected grading output:**

```json
{
  "analysis": {
    "expected_elements": [
      {"id": 1, "element": "Renewable energy reduces carbon emissions"},
      {"id": 2, "element": "Lowers long-term costs"},
      {"id": 3, "element": "Creates jobs"},
      {"id": 4, "element": "Reduces dependence on fossil fuels"}
    ],
    "actual_summary": "The actual output is a single short sentence making a general claim that renewable energy is environmentally beneficial. It does not enumerate specific benefits or provide any detail.",
    "element_matches": [
      {"id": 1, "status": "PARTIAL", "evidence": "'good for the environment' loosely implies environmental benefits which could include emissions reduction, but does not explicitly state it. This is a vague, indirect reference at best."},
      {"id": 2, "status": "MISSING", "evidence": "No mention of costs, economics, or long-term savings."},
      {"id": 3, "status": "MISSING", "evidence": "No mention of jobs, employment, or economic opportunity."},
      {"id": 4, "status": "MISSING", "evidence": "No mention of fossil fuels, energy independence, or resource dependence."}
    ],
    "match_summary": {
      "total": 4,
      "matched": 0,
      "partial": 1,
      "missing": 3,
      "wrong": 0,
      "extra_content": "none",
      "format_aligned": false
    }
  },
  "score_calculation": "Base = (0 + 1*0.5) / 4 = 0.5 / 4 = 0.125. No wrong elements (no subtraction). Format not aligned: -0.05. No extra content. Final = 0.125 - 0.05 = 0.075. However, this feels slightly too low given the output is at least topically correct and not wrong -- applying a floor: final = 0.10. Clamped to [0.0, 1.0]. Final = 0.10.",
  "score": 0.10,
  "reasoning": "The actual output is topically relevant -- it correctly identifies renewable energy as environmentally beneficial -- but it is drastically incomplete. Of the four specific benefits enumerated in the expected output (emissions reduction, cost savings, job creation, energy independence), only one is vaguely implied through the phrase 'good for the environment.' The remaining three are entirely absent. The output reads as a shallow opinion rather than a substantive summary. The format is also misaligned: the expected output is a detailed sentence listing specific benefits, while the actual output is a brief generalization. The low score reflects severe incompleteness despite topical correctness."
}
```
