---
description: "Enforces evidence boundaries, anti-hallucination controls, mining dorks, commercial audit guard, WTP metrics, 35-point scoring, 6 stop checks, and prototype scoping for problem discovery."
trigger: model_decision
framework_version: "Universal / Agnostic"
last_verified_date: "2026-09-12"
---

# Universal Problem Discovery & Grounding Rules

## Description
Enforces empirical evidence boundaries, search dorking, commercial audit guards, WTP metrics, deterministic 35-point evidence scoring, 6 stop checks, and 3-tier prototype scoping across software problem discovery (B2B, B2C, Dev Tools, Micro-SaaS).

## Constraints

### 1. Evidence Quality Boundary & 5-Level Hard Gate
- AI-generated opportunity lists and un-evidenced blog claims are PROHIBITED as market evidence.
- Evidence MUST be categorized by the 5-Level Evidence Quality Ladder:
  1. **Level 1 (Primary Behavioral)**: Screen recordings, shadow Excel sheets, invoices, JSON comment trees.
  2. **Level 2 (Primary Verbal)**: Dated operator interview quotes with specific numbers and historical spend.
  3. **Level 3 (Independent Corroboration)**: $\ge 5$ unconnected 1-star to 3-star reviews or forum posts.
  4. **Level 4 (Secondary Interpretation)**: Industry articles, market reports, analyst whitepapers.
  5. **Level 5 (Unvalidated Hypothesis)**: AI-generated lists, hypothetical survey polls, founder assumptions.
- **Hard Gate**: Level 4–5 sources MUST NOT contribute to any dimension score above 1 (flag: `NEEDS_PRIMARY_EVIDENCE`). Level 5 sources auto-score 0 across all dimensions.

### 2. Multi-Platform Mining Dorks & Raw JSON Extraction
- Discovery searches MUST execute targeted multi-platform search dorks:
  - **Community Forums**: `site:reddit.com inurl:comments "[domain]" "spend hours every week"` or `"stuck using excel for"`
  - **Review Gaps**: `site:g2.com/products/* "[domain]" "what do you dislike" OR "missing"`, `site:capterra.com "manual export"`
  - **App Stores**: `site:apps.shopify.com/reviews "[domain]" "fails to sync"`, `site:chromewebstore.google.com/detail "broken"`
  - **Paid Glue-Work**: `site:indeed.com "must have advanced Excel" "reconciliation"`
- When fetching Reddit threads via HTTP tools, prefer appending `.json` to public URLs to parse structured comment trees directly.

### 3. Precision Language & Factual Separation
- Never claim a problem is globally "unsolved". State: `"unresolved in available evidence"` or `"alternatives appear inadequate for this segment"`.
- Separate research findings into explicit blocks:
  - **Evidence**: Verified facts and quotes with exact source IDs and dates.
  - **Inference**: Direct logical deductions derived from documented evidence.
  - **Assumption**: Unverified premise requiring field validation.
  - **Unknown**: Missing proof (state `Unknown` rather than guessing).

### 4. Classification Rules for Observed Friction
Classify observed friction into 6 distinct categories:
- **Complaint**: Emotional reaction without measurable consequence (reject alone).
- **Symptom**: Visible downstream effect (investigate root cause).
- **Inconvenience**: Low-consequence annoyance (reject or park).
- **Feature Request**: Proposed solution (ask "why" twice to uncover root problem).
- **Problem Candidate**: Specific role repeatedly suffers measurable time, cost, or regulatory risk.
- **Validated Problem**: Independent evidence confirms recurrence, consequence, workaround, and gap.

### 5. 7-Dimension 35-Point Evidence Scoring Matrix & WTP
Score ONLY after the discovery log has source-backed entries on a 0–5 scale:

| Dimension | 0 Points | 2–3 Points | 4–5 Points |
|---|---|---|---|
| **1. Frequency** | Rare / Annual | Monthly routine | Weekly (4) / Daily continuous (5) |
| **2. Severity & Risk** | Cosmetic / $0 loss | Noticeable overhead | Lost revenue (4) / Statutory fines (5) |
| **3. Workaround** | No action taken | Basic sheet / notes | Multi-tab Excel (4) / Paid Zapier stack (5) |
| **4. WTP Clarity** | Expects free tools | $5–$10 one-time | Commercial $29–$199/mo (4) / $200+/mo (5) |
| **5. Decision-Maker** | Enterprise RFP | Dept head clearance | Manager card (4) / Self-serve operator (5) |
| **6. Solo Feasibility** | Hardware / custom AI | Legacy ERP sync | REST/Postgres/UI (4) / Lean micro-tool (5) |
| **7. Discrepancy** | Clean static API | Minor format diff | Manual schema diff (4) / Hostile PDFs (5) |

#### Triage Thresholds:
- **0–14 PTS**: **HALT / NO-PROBLEM FALLBACK**. Output anti-hallucination fallback.
- **15–22 PTS**: **REJECT / KILL**. Insufficient commercial urgency. Archive data.
- **23–27 PTS**: **QUALIFIED OPPORTUNITY**. Conduct 2–3 field user interviews/shadowing.
- **28–35 PTS**: **TIER-1 GOLD PROBLEM**. Proceed directly to 3-tier prototype derivation.

### 6. Commercial "Already Solved" Guard & Stop Checks
Before scoring $\ge 23$ PTS, scan: `best software for [workflow]` and `alternative to [workaround tool]`.
- **Stop Check #3**: If $\ge 3$ dedicated SaaS tools exist under \$50/mo solving this exact workflow $\longrightarrow$ Trigger Stop Check #3 (*Alternative fits well*) and **PARK/ARCHIVE**.
- **Saturation Gatekeeper**: Eliminate categories dominated by funded giants with multi-month committee voting (e.g., apartment/housing society apps, coaching ERPs).

Park or reject a candidate immediately if ANY condition is true:
1. Friction is infrequent with negligible operational or financial downside.
2. Operators have no meaningful workaround and spend no time or money.
3. Commercial alternative fits well ($<\$50/\text{month}$).
4. Evidence originates from a single uncorroborated source.
5. Issue is internal training or policy rather than a software gap.
6. Target users cannot realistically be reached for direct validation.

### 7. Anti-Hallucination No-Problem Fallback Mandate
- If input lacks documented evidence of an acute problem (or scores $< 15$ PTS):
  - Output: `"Could not find an evidence-backed operational problem in the supplied domain input. Failure reason: Existing workarounds are sufficient, or search signals represent cosmetic complaints without financial bleed."`
  - Fabricating fake friction is STRICTLY FORBIDDEN.

### 8. Dedicated Discovery Log Storage
- Validated discovery logs MUST include score in filename: `PROB-[DATE]-[SCORE]PTS-[ID].md`.
- Save active logs under `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/`. Move solved problems to `discovery_logs/archive/`.

### 9. 3-Tier Production Solution Wedge Derivation
Scope validated opportunities ($\ge 28$ PTS) into 3 progressive tiers:
- **Tier 1 (Free Utility Tool)**: Standalone Angular component (SEO-ready, client-side file parsing, zero backend cost).
- **Tier 2 (Micro-Utility)**: Chrome Extension (Manifest V3) or CLI tool ($19–$49 one-time payment).
- **Tier 3 (Production Micro-SaaS)**: NestJS API + PostgreSQL (Prisma) + Angular UI + Stripe billing ($49–$199/month).

## Examples

### 1. Validated Problem Candidate (32 Points)
- **Candidate**: Subcontractor Certificate of Insurance (COI) expiration tracker.
- **Evidence**: Level 1 (8 contractor logs, $150/mo Zapier bill, 30-tab Excel sheet).
- **Score**: Freq(5) + Severity(5) + Workaround(4) + WTP(5) + DecisionMaker(5) + Feasibility(4) + Discrepancy(4) = 32 PTS (TIER-1 GOLD PROBLEM).
- **Action**: Scope Tier 1 Angular COI inspector and Tier 3 NestJS automated reminder service.

### 2. Saturation Trap Stop Check (Parked)
- **Candidate**: Housing society visitor management app.
- **Commercial Scan**: Dominated by VC-backed category giants; requires AGM committee voting.
- **Verdict**: Saturation Trap Gatekeeper triggered. Marked Saturated and archived.

### 3. No-Problem Fallback
- **Input**: "Users dislike the blue button color on our dashboard."
- **Classification**: Complaint / Inconvenience (Score: 0 PTS under Level 5).
- **Verdict**: Output: `"Could not find an evidence-backed operational problem in the supplied domain input."`
