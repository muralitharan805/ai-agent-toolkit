---
description: "Enforces strict evidence boundaries, anti-hallucination controls, high-intent mining dorks, commercial pre-scoring audit guard, WTP economic metrics, 35-point 7-dimension evidence scoring, 6 mandatory stop checks, and production tech stack prototype scoping for problem discovery."
trigger: always_on
---

# Problem Discovery & Grounding Rules

## Description
Enforces mandatory evidence boundaries, anti-hallucination controls, high-intent mining search dorks, commercial pre-scoring audit guards, Willingness to Pay (WTP) economic friction metrics, 35-point 7-dimension evidence scoring, competitor audit rules, 6 mandatory stop checks, and production tech stack prototype scoping across all problem discovery tasks.

## Constraints

### 1. Evidence Quality Boundary & 5-Level Quality Ladder
- AI-generated opportunity lists, un-evidenced blog claims, or previous LLM answers are STRICTLY PROHIBITED as market evidence.
- Claims MUST be grounded in traceable evidence categorized by the 5-Level Evidence Quality Ladder:
  1. **Level 1 (Primary Behavioral Evidence)**: Direct observation, raw screenshots, SOP spreadsheets, recorded workflows, error counts, paid invoices, JSON structured comment trees.
  2. **Level 2 (Primary Verbal Evidence)**: Dated user interview quotes with specific contextual background.
  3. **Level 3 (Independent Corroboration)**: Multiple unconnected 2-3 star G2/Capterra/Trustpilot reviews, forum posts, or public discussions.
  4. **Level 4 (Secondary Interpretation)**: Industry articles, market reports, analyst summaries.
  5. **Level 5 (Hypothesis)**: Unverified plausible explanations.
- Never present a lower evidence level as a higher one.

### 2. High-Intent Mining Dorks & Raw JSON Extraction Rule
- Discovery searches MUST NOT rely solely on generic keywords. Agents MUST execute targeted search dorks:
  - **Reddit Dorks**: `site:reddit.com/r/[subreddit] "why is there no tool to" OR "hate that [tool] doesn't"`, `site:reddit.com/r/[subreddit] "spending hours manually" OR "our team is stuck using excel for"`, `site:reddit.com/r/[subreddit] "looking for a simple alternative to" OR "is there an API or script to"`.
  - **Review & Complaint Dorks**: `site:g2.com/products/*/reviews "what do you dislike" OR "missing feature" OR "workaround"`, `site:capterra.com "cons" OR "manual export" OR "lack of integration"`, `site:trustpilot.com/review/* "terrible experience" OR "pricing increase" OR "broken sync"`.
- When fetching Reddit threads, prefer appending `.json` to public thread URLs (or using search `.json` endpoints) to pull raw structured comment trees rather than shallow HTML snippets.

### 3. Precision Language & Strict Factual Separation Rule
- Agents MUST NEVER state or imply that a problem is globally "unsolved". Use precise language: `"unresolved in the available evidence"` or `"current alternatives appear inadequate for this segment"`.
- Every finding MUST separate conclusions into explicit blocks:
  - **Evidence**: Verified facts and quotes with exact source IDs/dates.
  - **Inference**: Logical deductions based directly on evidence.
  - **Assumption**: Unverified premise requiring validation.
  - **Unknown**: Missing proof (MUST explicitly state `Unknown` rather than guessing).

### 4. Classification Rules for Observed Friction
Observed friction MUST be classified into one of 6 distinct categories:
- **Complaint**: Emotional reaction without measurable consequence (insufficient on its own).
- **Symptom**: Visible downstream effect (investigate root cause).
- **Inconvenience**: Low-consequence annoyance (reject or park).
- **Feature Request**: Proposed solution (ask "why" at least twice to uncover underlying problem).
- **Problem Candidate**: Specific user role repeatedly experiences unwanted outcome with measurable time/cost/risk.
- **Validated Problem**: Independent evidence confirms recurrence, consequence, real workaround, and alternative gap.

### 5. 7-Dimension 35-Point Evidence Scoring Matrix & WTP Integration
Score ONLY after the discovery log has source-backed entries. Score each dimension on a 1–3–5 scale:

| Dimension | 1 Point | 3 Points | 5 Points |
|---|---|---|---|
| **1. Frequency** | Rare / Ad-hoc | Monthly | Daily / Weekly |
| **2. Consequence & WTP** | Minor annoyance; zero budget allocation | Noticeable time / cost; minor ad-hoc spending | Severe financial loss, compliance penalty, customer churn; **Active WTP signals** (paying Zapier \$50–\$200/mo, hiring VAs/freelancers, spending $\ge 5$ dev hours/mo on internal scripts) |
| **3. Workaround Strength & Economic Friction** | None | Basic manual workaround | Maintained spreadsheet / custom script / paying for multiple disconnected SaaS tools to bridge a single gap |
| **4. Evidence Quality** | Anecdote / Level 4-5 | Level 2-3 corroboration | Level 1-2 primary behavioral/verbal sources (SOPs, JSON comment trees, invoices) |
| **5. Segment Reach** | Single individual | Several similar users | Clear recurring role / segment pattern |
| **6. Alternative Gap** | Strong alternatives fit well | Partial fit | Alternatives are costly, complex, or bypassed |
| **7. Access to Validation** | No reliable access | Some access | Direct access to several independent users |

#### Decision Thresholds:
- **0–14 Points**: **REJECT / PARK**. Do not build or research further unless new primary evidence appears.
- **15–22 Points**: **INVESTIGATE**. Collect stronger primary evidence; DO NOT design a solution.
- **23–28 Points**: **EVIDENCE-BACKED HYPOTHESIS**. Run focused interviews and alternative audits.
- **29–35 Points**: **STRONG VALIDATION CANDIDATE**. Confirm with independent users and current alternatives.

### 6. Commercial "Already Solved" Audit Guard & Mandatory Stop Checks
Before scoring any candidate $\ge 23$ points, agents MUST execute a direct commercial scan: `best software for [extracted friction workflow]` and `alternative to [workaround tool] for [niche]`.
- **Mandatory Stop Check Trigger**: If $\ge 3$ dedicated modern SaaS products exist under \$50/mo with positive reviews that solve this exact workflow, the agent MUST automatically trigger Stop Check #3 (*Alternative fits well*) and park/archive the finding.
- **Underserved Qualification**: A problem candidate is marked "Underserved / Validated" ONLY if existing tools are:
  1. Bloated enterprise suites locked behind \$500+/mo sales calls.
  2. Deprecated or unmaintained tools with broken APIs.
  3. Missing critical niche-specific localization or compliance requirements.

Agents MUST immediately park or reject a candidate problem if ANY of the following 6 conditions are true:
1. The pain is infrequent and carries no material financial, compliance, or operational consequence.
2. Target users have no meaningful workaround and do not modify behavior or spend money to solve it.
3. **Commercial "Already Solved" Guard**: A current affordable alternative tool (< \$50/mo) already fits the target user segment well.
4. Evidence originates from only a single person or a single copied source.
5. The issue is primarily an internal training, policy, or adoption issue rather than a product/workflow gap.
6. Target users or decision-makers cannot realistically be reached for direct validation.

### 7. No-Problem Fallback Mandate
- If the supplied input or domain scan does NOT contain sufficient evidence of an acute, recurring problem (or scores < 15 points):
  - The agent MUST explicitly output: `"Could not find a valid, evidence-backed problem in the supplied input."`
  - Fabricating fake friction or pitching premature solution ideas is STRICTLY FORBIDDEN.

### 8. Dedicated Discovery Log Storage & Archiving Protocol
- All validated problem discovery log notes MUST incorporate their 35-point score into the filename (`PROB-[DATE]-[SCORE]PTS-[ID].md`, e.g., `PROB-20260830-31PTS-CAM-RECONCILIATION.md`).
- Active validated logs MUST be saved in Obsidian under `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/`.
- If an audit reveals that a problem is ALREADY SOLVED in the real-world market by existing SaaS platforms (e.g. Avalara, Vanta, Getida), it MUST be moved to `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/archive/`.

### 9. Production Tech Stack 3-Tier Build Output Scoping
Validated opportunities ($\ge 23$ Points) MUST be scoped strictly across our 3 production build tiers:
- **Tier 1 (Free Utility Tool for `seyalicraft.com`)**: Client-side Standalone Angular / TypeScript component (SEO-ready, zero-backend cost, Google AdSense container ready).
- **Tier 2 (Micro-Utility / Automation)**: Chrome Extension (Manifest v3) or Node.js / Python CLI automation script (\$5–\$29 one-time purchase).
- **Tier 3 (B2B Micro-SaaS Product)**: NestJS backend + PostgreSQL/pgvector Prisma schema + Angular frontend + Stripe/Paddle billing model (\$29–\$199/month recurring subscription).

