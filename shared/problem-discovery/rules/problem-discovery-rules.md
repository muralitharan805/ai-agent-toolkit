---
description: "Enforces strict evidence boundaries, anti-hallucination controls, 35-point 7-dimension evidence scoring, 6 mandatory stop checks, and no-solution-design mandate for problem discovery."
trigger: always_on
---

# Problem Discovery & Grounding Rules

## Description
Enforces mandatory evidence boundaries, anti-hallucination controls, 35-point 7-dimension evidence scoring, competitor audit rules, 6 mandatory stop checks, and no-problem fallback protocols across all problem discovery and validation tasks.

## Constraints

### 1. Evidence Quality Boundary & 5-Level Quality Ladder
- AI-generated opportunity lists, un-evidenced blog claims, or previous LLM answers are STRICTLY PROHIBITED as market evidence.
- Claims MUST be grounded in traceable evidence categorized by the 5-Level Evidence Quality Ladder:
  1. **Level 1 (Primary Behavioral Evidence)**: Direct observation, raw screenshots, SOP spreadsheets, recorded workflows, error counts, paid invoices.
  2. **Level 2 (Primary Verbal Evidence)**: Dated user interview quotes with specific contextual background.
  3. **Level 3 (Independent Corroboration)**: Multiple unconnected 2-3 star G2/Capterra reviews, forum posts, or public discussions.
  4. **Level 4 (Secondary Interpretation)**: Industry articles, market reports, analyst summaries.
  5. **Level 5 (Hypothesis)**: Unverified plausible explanations.
- Never present a lower evidence level as a higher one.

### 2. Precision Language & Strict Factual Separation Rule
- Agents MUST NEVER state or imply that a problem is globally "unsolved". Use precise language: `"unresolved in the available evidence"` or `"current alternatives appear inadequate for this segment"`.
- Every finding MUST separate conclusions into explicit blocks:
  - **Evidence**: Verified facts and quotes with exact source IDs/dates.
  - **Inference**: Logical deductions based directly on evidence.
  - **Assumption**: Unverified premise requiring validation.
  - **Unknown**: Missing proof (MUST explicitly state `Unknown` rather than guessing).

### 3. Classification Rules for Observed Friction
Observed friction MUST be classified into one of 6 distinct categories:
- **Complaint**: Emotional reaction without measurable consequence (insufficient on its own).
- **Symptom**: Visible downstream effect (investigate root cause).
- **Inconvenience**: Low-consequence annoyance (reject or park).
- **Feature Request**: Proposed solution (ask "why" at least twice to uncover underlying problem).
- **Problem Candidate**: Specific user role repeatedly experiences unwanted outcome with measurable time/cost/risk.
- **Validated Problem**: Independent evidence confirms recurrence, consequence, real workaround, and alternative gap.

### 4. 7-Dimension 35-Point Evidence Scoring Matrix
Score ONLY after the discovery log has source-backed entries. Score each dimension on a 1–3–5 scale:

| Dimension | 1 Point | 3 Points | 5 Points |
|---|---|---|---|
| **1. Frequency** | Rare / Ad-hoc | Monthly | Daily / Weekly |
| **2. Consequence** | Minor annoyance | Noticeable time / cost | Financial loss, compliance penalty, customer churn |
| **3. Workaround Strength** | None | Basic manual workaround | Maintained spreadsheet / script / service process |
| **4. Evidence Quality** | Anecdote / Level 4-5 | Level 2-3 corroboration | Level 1-2 primary behavioral/verbal sources |
| **5. Segment Reach** | Single individual | Several similar users | Clear recurring role / segment pattern |
| **6. Alternative Gap** | Strong alternatives fit well | Partial fit | Alternatives are costly, complex, or bypassed |
| **7. Access to Validation** | No reliable access | Some access | Direct access to several independent users |

#### Decision Thresholds:
- **0–14 Points**: **REJECT / PARK**. Do not build or research further unless new primary evidence appears.
- **15–22 Points**: **INVESTIGATE**. Collect stronger primary evidence; DO NOT design a solution.
- **23–28 Points**: **EVIDENCE-BACKED HYPOTHESIS**. Run focused interviews and alternative audits.
- **29–35 Points**: **STRONG VALIDATION CANDIDATE**. Confirm with independent users and current alternatives.

### 5. Mandatory Stop Checks (6 Triggers to Park or Reject)
Agents MUST immediately park or reject a candidate problem if ANY of the following 6 conditions are true:
1. The pain is infrequent and carries no material financial, compliance, or operational consequence.
2. Target users have no meaningful workaround and do not modify behavior or spend money to solve it.
3. A current affordable alternative tool already fits the target user segment well.
4. Evidence originates from only a single person or a single copied source.
5. The issue is primarily an internal training, policy, or adoption issue rather than a product/workflow gap.
6. Target users or decision-makers cannot realistically be reached for direct validation.

### 6. No-Problem Fallback Mandate
- If the supplied input or domain scan does NOT contain sufficient evidence of an acute, recurring problem (or scores < 15 points):
  - The agent MUST explicitly output: `"Could not find a valid, evidence-backed problem in the supplied input."`
  - Fabricating fake friction or pitching premature solution ideas is STRICTLY FORBIDDEN.

### 7. Dedicated Discovery Log Storage & Archiving Protocol
- All validated problem discovery log notes MUST incorporate their 35-point score into the filename (`PROB-[DATE]-[SCORE]PTS-[ID].md`, e.g., `PROB-20260830-31PTS-CAM-RECONCILIATION.md`).
- Active validated logs MUST be saved in Obsidian under `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/`.
- If an audit reveals that a problem is ALREADY SOLVED in the real-world market by existing SaaS platforms (e.g. Avalara, Vanta, Getida), it MUST be moved to `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/archive/`.

### 8. 3-Tier Build Output Scoping
Validated opportunities ($\ge 23$ Points) MUST be scoped across 3 build tiers:
- **Tier 1**: Free Portfolio Utility Tool (for `seyalicraft.com`, developer brand, SEO, AdSense).
- **Tier 2**: Micro-Utility / Chrome Extension / CLI ($5–$29 one-time purchase).
- **Tier 3**: B2B Micro-SaaS Product ($29–$199/month recurring subscription).
