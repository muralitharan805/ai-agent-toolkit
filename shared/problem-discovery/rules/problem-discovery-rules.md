---
description: "Enforces evidence boundaries, anti-hallucination controls, mining dorks, commercial audit guard, WTP metrics, 35-point scoring, 6 stop checks, and prototype scoping for problem discovery."
trigger: model_decision
---

# Problem Discovery & Grounding Rules

## Description
Enforces evidence boundaries, high-intent search dorks, commercial pre-scoring audit guards, Willingness to Pay (WTP) economic friction metrics, 35-point 7-dimension evidence scoring, 6 mandatory stop checks, and 3-tier tech stack scoping across problem discovery tasks.

## Constraints

### 1. Evidence Quality Boundary & 5-Level Ladder
- AI-generated opportunity lists and un-evidenced blog claims are PROHIBITED as market evidence.
- Claims MUST be categorized by the 5-Level Evidence Quality Ladder:
  1. **Level 1 (Primary Behavioral)**: Raw screenshots, SOP spreadsheets, error logs, invoices, JSON comment trees.
  2. **Level 2 (Primary Verbal)**: Dated user interview quotes with specific contextual background.
  3. **Level 3 (Independent Corroboration)**: Multiple independent 2-3 star G2/Capterra reviews or forum posts.
  4. **Level 4 (Secondary Interpretation)**: Industry articles, market reports, analyst summaries.
  5. **Level 5 (Hypothesis)**: Unverified plausible explanations.
- Never present a lower evidence level as a higher one.

### 2. High-Intent Mining Dorks & Raw JSON Extraction
- Discovery searches MUST execute targeted search dorks:
  - **Reddit**: `site:reddit.com/r/[sub] "why is there no tool to" OR "spending hours manually" OR "stuck using excel for"`
  - **Reviews**: `site:g2.com/products/*/reviews "what do you dislike" OR "missing feature" OR "workaround"`
  - **Complaints**: `site:capterra.com "cons" OR "manual export"`, `site:trustpilot.com/review/* "broken sync"`
- When fetching Reddit threads, prefer appending `.json` to public URLs to extract structured comment trees.

### 3. Precision Language & Strict Factual Separation
- Never state that a problem is globally "unsolved". Use: `"unresolved in available evidence"` or `"alternatives appear inadequate for this segment"`.
- Separate conclusions into explicit blocks:
  - **Evidence**: Verified facts and quotes with exact source IDs/dates.
  - **Inference**: Direct logical deductions based on evidence.
  - **Assumption**: Unverified premise requiring validation.
  - **Unknown**: Missing proof (state `Unknown` rather than guessing).

### 4. Classification Rules for Observed Friction
Classify observed friction into 6 distinct categories:
- **Complaint**: Emotional reaction without measurable consequence (reject alone).
- **Symptom**: Visible downstream effect (investigate root cause).
- **Inconvenience**: Low-consequence annoyance (reject or park).
- **Feature Request**: Proposed solution (ask "why" twice to uncover root problem).
- **Problem Candidate**: Specific role repeatedly suffers measurable time/cost/risk.
- **Validated Problem**: Independent evidence confirms recurrence, consequence, workaround, and gap.

### 5. 7-Dimension 35-Point Evidence Scoring Matrix & WTP
Score ONLY after the discovery log has source-backed entries. Score on a 1–3–5 scale:

| Dimension | 1 Point | 3 Points | 5 Points |
|---|---|---|---|
| **1. Frequency** | Rare / Ad-hoc | Monthly | Daily / Weekly |
| **2. Consequence & WTP** | Minor annoyance; $0 budget | Noticeable cost | Severe loss, churn; **Active WTP** (\$50-\$200/mo Zapier, VAs, $\ge 5$ dev hrs/mo) |
| **3. Workaround** | None | Basic manual steps | Maintained spreadsheet, custom script, or multi-SaaS bridging |
| **4. Evidence Quality** | Anecdote / Level 4-5 | Level 2-3 corroboration | Level 1-2 primary behavioral/verbal sources |
| **5. Segment Reach** | Single individual | Several users | Clear recurring role / segment pattern |
| **6. Alternative Gap** | Alternatives fit well | Partial fit | Alternatives are costly, complex, or bypassed |
| **7. Access to Validation** | No reliable access | Some access | Direct access to several independent users |

#### Thresholds:
- **0–14 PTS**: **REJECT / PARK**. Do not build or research further without new primary evidence.
- **15–22 PTS**: **INVESTIGATE**. Collect stronger primary evidence; do NOT design a solution.
- **23–28 PTS**: **EVIDENCE-BACKED HYPOTHESIS**. Run focused interviews and alternative audits.
- **29–35 PTS**: **STRONG VALIDATION CANDIDATE**. Confirm with users and alternatives.

### 6. Commercial "Already Solved" Guard & Stop Checks
Before scoring $\ge 23$ PTS, scan: `best software for [workflow]` and `alternative to [workaround tool]`.
- **Stop Check**: If $\ge 3$ dedicated SaaS exist under \$50/mo solving this workflow, trigger Stop Check #3 (*Alternative fits well*) and park/archive.
- **Underserved Qualification**: A candidate is "Underserved" ONLY if existing tools are: (1) enterprise suites locked behind \$500+/mo sales calls, (2) deprecated tools, or (3) missing critical compliance.

Park or reject a candidate immediately if ANY condition is true:
1. Pain is infrequent with no material operational or financial consequence.
2. Target users have no meaningful workaround and spend no time or money.
3. **Commercial Guard**: Affordable tool (< \$50/mo) fits the segment well.
4. Evidence originates from a single person or copied source.
5. Issue is internal training, policy, or adoption rather than a product gap.
6. Target users cannot realistically be reached for direct validation.

### 7. No-Problem Fallback Mandate
- If input lacks evidence of an acute problem (or scores < 15 PTS):
  - Output: `"Could not find a valid, evidence-backed problem in the supplied input."`
  - Fabricating fake friction is STRICTLY FORBIDDEN.

### 8. Dedicated Discovery Log Storage & Archiving
- Validated discovery logs MUST include score in filename: `PROB-[DATE]-[SCORE]PTS-[ID].md`.
- Save active logs under `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/`.
- If an audit reveals a problem is already solved, move it to `discovery_logs/archive/`.

### 9. Production Tech Stack 3-Tier Build Output Scoping
Scope validated opportunities ($\ge 23$ PTS) into 3 production tiers:
- **Tier 1 (Free Utility Tool)**: Standalone Angular component (SEO-ready, zero-backend, AdSense ready).
- **Tier 2 (Micro-Utility)**: Chrome Extension (MV3) or Node/Python CLI tool (\$5–\$29 one-time).
- **Tier 3 (B2B Micro-SaaS)**: NestJS backend + PostgreSQL Prisma + Angular frontend + Stripe (\$29–\$199/mo).

## Examples

### 1. Validated B2B Candidate (31 Points)
- **Candidate**: Commercial Lease CAM reconciliation.
- **Evidence**: Level 1 (5 property managers maintaining 40-tab spreadsheets, paying \$150/mo Zapier).
- **Score**: Freq(5) + Consequence(5) + Workaround(5) + Evidence(5) + Reach(3) + Gap(5) + Access(3) = 31 PTS (STRONG VALIDATION CANDIDATE).
- **Action**: Scaffold Tier 1 Angular CAM calculator and Tier 3 NestJS ingestion service.

### 2. Commercial Stop Check Triggered (Parked)
- **Candidate**: Freelance PDF invoice generator.
- **Commercial Scan**: Discovered Invoice Ninja, Wave, and Harvest offering free or \$12/mo tiers.
- **Verdict**: Stop Check #3 triggered (Commercial alternative fits well under \$50/mo). Marked ALREADY SOLVED and archived.

### 3. No-Problem Fallback
- **Input**: "Users dislike the blue button on our landing page."
- **Classification**: Complaint / Inconvenience (Score: 7 PTS).
- **Verdict**: Output: `"Could not find a valid, evidence-backed problem in the supplied input."`
