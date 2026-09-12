# 35-Point Evidence Scoring Matrix & Willingness to Pay (WTP) Guide

## Overview

The 35-Point Evidence Scoring Matrix provides a rigorous, mathematical boundary to qualify problem candidates before writing code. Scoring must be calculated strictly from documented, source-backed discovery logs—never from ungrounded assumptions or AI-generated idea lists.

---

## 1. The 35-Point Evidence Scoring Matrix

Every discovered problem candidate is evaluated across **7 core dimensions** scored from 0 to 5:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                  35-POINT EVIDENCE SCORING RUBRIC                      │
├─────────────────────────────────────┬───────┬──────────────────────────┤
│ Criterion                           │ Range │ Threshold Target         │
├─────────────────────────────────────┼───────┼──────────────────────────┤
│ 1. Problem Frequency                │ 0 – 5 │ ≥ 4 (Daily or Weekly)    │
│ 2. Financial Severity & Legal Risk  │ 0 – 5 │ ≥ 4 (Direct fines/loss)  │
│ 3. Existing Workaround Investment   │ 0 – 5 │ ≥ 3 (Hours in Excel/WA)  │
│ 4. Willingness to Pay (WTP) Clarity │ 0 – 5 │ ≥ 4 ($29–$199/mo easily) │
│ 5. Single Decision-Maker Workflow   │ 0 – 5 │ ≥ 4 (No committee veto)  │
│ 6. Technical Solo-Feasibility       │ 0 – 5 │ ≥ 4 (Node/Postgres/UI)   │
│ 7. Discrepancy & Data Fragility     │ 0 – 5 │ ≥ 3 (Mismatch occurs)    │
├─────────────────────────────────────┼───────┼──────────────────────────┤
│ TOTAL SCORE                         │ 0–35  │ Pass Threshold: ≥ 23     │
└─────────────────────────────────────┴───────┴──────────────────────────┘
```

---

## 2. Granular Dimension Scoring Rubric

### 1. Problem Frequency (0–5)
- **0 Points**: Once a year or never; unpredictable anomaly.
- **2 Points**: Quarterly task (tolerated as minor periodic overhead).
- **4 Points**: Weekly recurring operational requirement.
- **5 Points**: Daily continuous bottleneck (occurs multiple times per work shift).

### 2. Financial Severity & Legal Risk (0–5)
- **0 Points**: Aesthetic preference or minor cosmetic complaint.
- **2 Points**: Causes mild employee annoyance with no measurable cash or regulatory impact.
- **4 Points**: Causes lost revenue, customer disputes, delayed billing, or developer downtime.
- **5 Points**: Direct statutory penalties, license suspension, tax credit forfeiture, or data loss liabilities.

### 3. Existing Workaround Investment (0–5)
- **0 Points**: Users take no corrective action; problem is ignored.
- **2 Points**: Casual mental tracking, unorganized notes, or browser bookmarks.
- **4 Points**: Maintained multi-tab Excel formulas, custom color-coded tabs, or dedicated communication groups.
- **5 Points**: Dedicated full-time employee, agency retainer, or multi-step paid automation (e.g., $100+/mo Zapier/Make accounts).

### 4. Willingness to Pay (WTP) Clarity (0–5)
- **0 Points**: Target users expect free consumer web/mobile apps; zero commercial software budget.
- **2 Points**: Willing to pay $5–$10 one-time for a utility app or script.
- **4 Points**: Natural commercial expense ($29–$199/month); costs substantially less than 2 hours of operator labor.
- **5 Points**: High ROI ($200–$1,000+/month); prevents recurring audit penalties or saves dozens of staff hours monthly.

### 5. Single Decision-Maker Workflow (0–5)
- **0 Points**: Enterprise procurement requiring RFP, multi-department security audits, and board signoff.
- **2 Points**: Requires department head approval + IT infrastructure clearance.
- **4 Points**: Team lead, project manager, or branch head can swipe credit card under corporate expense limits.
- **5 Points**: Solo operator, freelancer, small business owner, or developer can purchase instantly on a self-serve landing page.

### 6. Technical Solo-Feasibility (0–5)
- **0 Points**: Demands frontier AI research, custom computer vision models, specialized hardware, or proprietary enterprise certifications.
- **2 Points**: Requires complex distributed consensus, heavy legacy mainframe integration, or extensive multi-year compliance testing.
- **4 Points**: Clean full-stack architecture (REST/GraphQL API, PostgreSQL/SQLite, Angular/React UI, background worker jobs).
- **5 Points**: Lean micro-tool (single serverless worker, client-side data parser, webhook receiver, or Chrome Extension).

### 7. Discrepancy & Data Fragility (0–5)
- **0 Points**: Data is homogeneous, versioned, and accessed through a single reliable API.
- **2 Points**: Minor formatting variations between two standard screens or exports.
- **4 Points**: Manual cross-referencing between two distinct data schemas with missing primary identifiers.
- **5 Points**: Hostile schemas, unstandardized PDFs, fuzzy invoice matching, frequent breaking changes, and high human error rate.

---

## 3. The 5-Level Evidence Quality Ladder (Hard Gate)

Before computing dimension scores, classify data sources using the **Evidence Quality Ladder**:

| Level | Evidence Category | Source Artifact | Trust Weight |
| :---: | :--- | :--- | :---: |
| **Level 1** | **Primary Behavioral Evidence** | Direct screen recordings, sanitized shadow Excel sheets, actual invoices, JSON comment trees. | **100% (Gold Standard)** |
| **Level 2** | **Primary Verbal Evidence** | Verifiable, dated interview quotes with specific numbers, roles, and historical spend. | **80%** |
| **Level 3** | **Independent Corroboration** | 5+ unconnected 1-star to 3-star reviews or forum posts reporting the identical failure pattern. | **60%** |
| **Level 4** | **Secondary Interpretation** | Industry blogs, generic analyst reports, consultant whitepapers. | **20% (Treat as clue only)** |
| **Level 5** | **Unvalidated Hypothesis** | AI-generated idea lists, hypothetical survey polls, founder assumptions. | **0% (Never score this)** |

### Hard Gate Enforcement Rules:
1. **Level 4–5 sources MUST NOT contribute to any dimension score above 1**, regardless of how many Level 4 sources exist. Flag: `NEEDS_PRIMARY_EVIDENCE`.
2. **Level 5 (AI-generated or speculative) sources automatically score 0** across all dimensions—no exceptions.
3. Two independent analysts evaluating the identical evidence must arrive at consistent scores (repeatability test).

---

## 4. Decision Thresholds & Triage

```text
┌────────────────────────────────────────────────────────────────────────┐
│                    DECISION THRESHOLDS & TRIAGE                        │
├──────────────┬───────────────────────────────┬─────────────────────────┤
│ Score Range  │ Classification                │ Mandatory Action        │
├──────────────┼───────────────────────────────┼─────────────────────────┤
│ 0 – 14 PTS   │ HALT / NO-PROBLEM FALLBACK    │ Stop pipeline. Output   │
│              │                               │ anti-hallucination msg. │
├──────────────┼───────────────────────────────┼─────────────────────────┤
│ 15 – 22 PTS  │ REJECT / KILL                 │ Insufficient commercial │
│              │                               │ urgency. Archive data.  │
├──────────────┼───────────────────────────────┼─────────────────────────┤
│ 23 – 27 PTS  │ QUALIFIED OPPORTUNITY         │ Conduct 2–3 field user  │
│              │                               │ interviews or shadowing.│
├──────────────┼───────────────────────────────┼─────────────────────────┤
│ 28 – 35 PTS  │ TIER-1 GOLD PROBLEM           │ High pain, clear WTP.   │
│              │                               │ Scope 3-tier prototype. │
└──────────────┴───────────────────────────────┴─────────────────────────┘
```

---

## 5. Commercial Pre-Scoring Guard & 6 Mandatory Stop Checks

Before confirming any candidate $\ge 23$ points, execute a direct commercial scan (`best software for [workflow]` and `alternative to [workaround tool]`).

Trigger an immediate **PARK / ARCHIVE** if ANY of the 6 Stop Checks are true:
1. **Infrequent & Low Impact**: Problem occurs rarely with negligible operational or financial downside.
2. **No Meaningful Workaround**: Operators tolerate the issue without maintaining spreadsheets, scripts, or manual habits.
3. **Commercial Alternative Fits Well**: $\ge 3$ dedicated, affordable SaaS products ($<\$50/\text{month}$) already solve this exact workflow.
4. **Single-Source Bias**: Evidence originates from a single vocal user or re-posted anecdote without independent confirmation.
5. **Internal Policy / Training Issue**: Breakdown is caused by poor employee onboarding or internal policy non-compliance rather than a software tooling gap.
6. **Unreachable Audience**: Target buyers cannot be reached through accessible communities, directories, or direct outreach channels.

---

## 6. Anti-Hallucination No-Problem Fallback Protocol

If the evidence does not prove documented operational friction, financial loss, or active workarounds:

$$\text{Total Score} < 15 \implies \textbf{HALT PIPELINE}$$

The engine **MUST NOT** invent a problem or brainstorm a startup concept. It must return:
> *"Could not find an evidence-backed operational problem in the supplied domain input. Failure reason: Existing workarounds are sufficient, or search signals represent cosmetic complaints without financial bleed."*
