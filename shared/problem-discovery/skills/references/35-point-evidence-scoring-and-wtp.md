# 35-Point Evidence Scoring Matrix & Dual-Track Prioritization Guide

## Overview

The 35-Point Evidence Scoring Matrix provides a disciplined mathematical framework to prioritize problem candidates before writing code. **Crucially, the 35-point score measures Research Prioritization—NOT final market validation.** High scores indicate that a candidate deserves rapid empirical experimentation, not that customer demand is already proven. 

Scoring must be calculated strictly from documented, source-backed discovery logs across two dedicated evaluation tracks.

---

## 1. Dual Evaluation Tracks

Problem candidates must be routed into the appropriate track to prevent bias against valuable non-commercial tools:

- **Track A (Commercial / Micro-SaaS)**: Evaluates problems intended for paid products, subscription software, or paid extensions. Focuses on direct willingness to pay (WTP), economic loss, and single-buyer purchasing power.
- **Track B (Free Utility / Public Benefit / Community)**: Evaluates high-utility free tools, local offline workflows, developer open-source utilities, civic tools, or static web helpers. Replaces Dollar WTP with **Adoption Urgency & Time Saved**, focusing on distribution reach, accessibility, and zero-maintenance architecture.

---

## 2. The 35-Point Evidence Scoring Matrix

Every discovered problem candidate is evaluated across **7 core dimensions** scored from 0 to 5:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                  35-POINT EVIDENCE SCORING RUBRIC                      │
├─────────────────────────────────────┬───────┬──────────────────────────┤
│ Criterion                           │ Range │ Threshold Target         │
├─────────────────────────────────────┼───────┼──────────────────────────┤
│ 1. Problem Frequency                │ 0 – 5 │ ≥ 4 (Daily or Weekly)    │
│ 2. Severity, Consequence & Risk     │ 0 – 5 │ ≥ 4 (Direct loss/penalty)│
│ 3. Existing Workaround Investment   │ 0 – 5 │ ≥ 3 (Hours in Excel/WA)  │
│ 4. Track Evaluation:                │ 0 – 5 │ ≥ 4                      │
│    Track A: Willingness to Pay (WTP)│       │ ($29–$199/mo easily)     │
│    Track B: Utility & Adoption Push │       │ (High repeat retention)  │
│ 5. Single Decision-Maker Workflow   │ 0 – 5 │ ≥ 4 (No committee veto)  │
│ 6. Technical Solo-Feasibility       │ 0 – 5 │ ≥ 4 (Node/Postgres/UI)   │
│ 7. Process Discrepancy & Friction   │ 0 – 5 │ ≥ 3 (Workflow breaks)    │
├─────────────────────────────────────┼───────┼──────────────────────────┤
│ TOTAL RESEARCH PRIORITY SCORE       │ 0–35  │ Priority Threshold: ≥ 23 │
└─────────────────────────────────────┴───────┴──────────────────────────┘
```

---

## 3. Granular Dimension Scoring Rubric

### 1. Problem Frequency (0–5)
- **0 Points**: Once a year or never; unpredictable anomaly.
- **2 Points**: Quarterly task (tolerated as minor periodic overhead).
- **4 Points**: Weekly recurring operational requirement.
- **5 Points**: Daily continuous bottleneck (occurs multiple times per work shift).

### 2. Severity, Consequence & Risk (0–5)
- **0 Points**: Cosmetic preference or minor convenience complaint without operational consequence.
- **2 Points**: Mild employee annoyance with no measurable time, cash, or regulatory impact.
- **4 Points**: Causes direct lost revenue, customer disputes, delayed billing, or developer downtime (> 4 hours/week).
- **5 Points**: Statutory penalties, license suspension, tax credit forfeiture, catastrophic data loss, or legal liability.

### 3. Existing Workaround Investment & Inaction Analysis (0–5)
- **0 Points**: Users take no corrective action because the consequence is negligible.
- **2 Points**: Casual mental tracking, unorganized bookmarks, or ad-hoc messaging.
- **4 Points**: Maintained multi-tab Excel formulas, physical notebooks, WhatsApp coordination, or custom SOPs.
- **5 Points**: Dedicated staff hire, agency retainer, or multi-step paid automation (e.g., $100+/mo Zapier/Make stack).
- *Inaction Caveat*: If no workaround exists because users lack technical literacy, tools are non-existent, or the task was abandoned under extreme friction, document this under Inaction Analysis rather than penalizing if consequence is severe.

### 4. Track Evaluation (0–5)

#### Track A: Commercial Willingness to Pay (WTP) Clarity
- **0 Points**: Target users expect free tools; zero commercial software budget or mandate.
- **2 Points**: Willing to pay $5–$10 one-time for a utility app or script.
- **4 Points**: Natural commercial expense ($29–$199/month); costs substantially less than 2 hours of operator labor.
- **5 Points**: High ROI ($200–$1,000+/month); prevents recurring audit penalties or saves dozens of staff hours monthly.

#### Track B: Utility, Repeat Adoption & Time Saved (Free / Public Tool)
- **0 Points**: One-time curiosity visit; zero return incentive or measurable time saved.
- **2 Points**: Occasional lookup utility (< 10 minutes saved per month).
- **4 Points**: Saves 1–3 hours weekly for an operator, citizen, or small business owner; clear organic search demand.
- **5 Points**: Essential daily workflow enabler; zero-overhead static distribution with high organic sharing.

### 5. Single Decision-Maker Workflow (0–5)
- **0 Points**: Enterprise procurement requiring RFP, multi-department security audits, and board signoff.
- **2 Points**: Requires department head approval + IT infrastructure clearance.
- **4 Points**: Team lead, project manager, or branch head can swipe credit card or approve immediate trial.
- **5 Points**: Solo operator, freelancer, small shopkeeper, or developer can adopt immediately on a self-serve page.

### 6. Technical Solo-Feasibility (0–5)
- **0 Points**: Demands frontier AI research, custom computer vision models, specialized hardware, or proprietary enterprise certifications.
- **2 Points**: Requires complex distributed consensus, heavy legacy mainframe integration, or multi-year compliance certification.
- **4 Points**: Clean full-stack architecture (REST API, PostgreSQL/SQLite, Angular OnPush UI, background jobs).
- **5 Points**: Lean micro-tool (standalone static client-side parser, CLI binary, webhook receiver, or browser extension).

### 7. Process Discrepancy & Operational Friction (0–5)
*Important*: Evaluate user pain and workflow breakdown, NOT implementation difficulty. Hostile schemas or messy PDFs represent technical implementation risk, not customer demand!
- **0 Points**: Clean, single-system workflow without data transposition or handoff friction.
- **2 Points**: Minor formatting variations between two standard screens or exports.
- **4 Points**: Manual cross-referencing between two distinct disconnected tools (e.g. ERP to logistics spreadsheet).
- **5 Points**: Acute multi-party discrepancy where handoffs repeatedly fail, requiring manual forensic reconciliation.

---

## 4. The 5-Level Evidence Quality Ladder (Hard Gate)

Before computing dimension scores, classify data sources using the **Evidence Quality Ladder**:

| Level | Evidence Category | Source Artifact | Evidentiary Confidence |
| :---: | :--- | :--- | :--- |
| **Level 1** | **Primary Behavioral Evidence** | Direct screen recordings, sanitized shadow Excel sheets, actual production error logs, verified receipts. | **High (Direct Observation)** |
| **Level 2** | **Primary Verbal Evidence** | Verifiable, dated interview quotes with specific numbers, roles, and historical spend. | **Substantial (Primary Testimony)** |
| **Level 3** | **Independent Corroboration** | 5+ unconnected reviews, Reddit/forum threads, or JSON comment trees reporting the identical failure pattern. | **Moderate (Reported Sentiment)** |
| **Level 4** | **Secondary Interpretation** | Industry blogs, generic analyst reports, consultant whitepapers. | **Low (Treat as clue only)** |
| **Level 5** | **Unvalidated Hypothesis** | AI-generated idea lists, hypothetical survey polls, founder assumptions. | **Zero (Never score this)** |

> [!IMPORTANT]
> **Data Format != Evidence Quality**
> Extracting Reddit comments as a raw JSON tree (`.json` URL) does NOT convert reported sentiment into behavioral proof. A JSON comment tree remains **Level 3 Corroborated Sentiment**, because it documents someone *reporting* an experience, not direct operational observation.

### Hard Gate Enforcement Rules:
1. **Level 4–5 sources MUST NOT contribute to any dimension score above 1**, regardless of volume. Flag: `NEEDS_PRIMARY_EVIDENCE`.
2. **Level 5 (AI-generated or speculative) sources automatically score 0** across all dimensions—no exceptions.
3. Scoring without attached primary artifacts or source references results in `UNVERIFIED_INPUT / RESEARCH_PRIORITY`, never `VALIDATED`.

---

## 5. Research Prioritization Thresholds & Triage

Scores govern **research and experimentation priority**, not build guarantees:

```text
┌────────────────────────────────────────────────────────────────────────┐
│               RESEARCH PRIORITIZATION & NEXT ACTIONS                   │
├──────────────┬───────────────────────────────┬─────────────────────────┤
│ Score Range  │ Prioritization Tier           │ Mandatory Next Step     │
├──────────────┼───────────────────────────────┼─────────────────────────┤
│ 0 – 14 PTS   │ HALT / NO-PROBLEM FALLBACK    │ Stop research. Output   │
│              │                               │ anti-hallucination msg. │
├──────────────┼───────────────────────────────┼─────────────────────────┤
│ 15 – 22 PTS  │ LOW RESEARCH PRIORITY         │ Archive finding; do NOT │
│              │                               │ design solutions.       │
├──────────────┼───────────────────────────────┼─────────────────────────┤
│ 23 – 27 PTS  │ QUALIFIED RESEARCH CANDIDATE  │ Conduct 2–3 field user  │
│              │                               │ interviews or shadowing.│
├──────────────┼───────────────────────────────┼─────────────────────────┤
│ 28 – 35 PTS  │ HIGH RESEARCH PRIORITY        │ Design smallest trial   │
│              │                               │ experiment to test fit. │
└──────────────┴───────────────────────────────┴─────────────────────────┘
```

---

## 6. Multi-Dimensional Alternative Audit & 6 Stop Checks

Before advancing any candidate $\ge 23$ points, execute a direct alternative scan. Do not simply count competitors or look at pricing alone. Evaluate:
1. **Exact Workflow Fit**: Does the competitor solve the specific micro-bottleneck, or is it bloated generic software?
2. **Geography & Language**: Does the tool support local compliance, vernacular language, and regional payment methods?
3. **Accessibility & Device Constraints**: Can operators use it on basic mobile devices / low bandwidth, or does it require desktop Chrome?
4. **Switching Friction**: Is migration so costly or complex that operators stay with manual workarounds?
5. **Non-Software Alternatives**: Can a pre-formatted Excel template, a WhatsApp checklist, or a simple operational SOP solve this without building custom software?

### Trigger an immediate PARK / ARCHIVE if ANY of the 6 Stop Checks are confirmed:
1. **Infrequent & Low Consequence**: Problem occurs rarely with negligible operational or financial downside.
2. **No Consequence Inaction**: Operators take no action, and abandoning the task causes no meaningful harm.
3. **Alternative Fits Well Across All Dimensions**: Accessible, modern tools or non-software templates already solve this workflow for the target user's context without high switching friction.
4. **Single-Source Bias**: Evidence originates from a single vocal user or re-posted anecdote without independent confirmation.
5. **Internal Policy / Training Issue**: Breakdown is caused by poor employee onboarding or internal policy non-compliance rather than a software tooling gap.
6. **Unreachable Audience**: Target operators cannot be reached through accessible communities, local physical visits, or direct channels.

---

## 7. Anti-Hallucination No-Problem Fallback Protocol

If the evidence does not prove documented operational friction, measurable time loss, or active workarounds:

$$\text{Total Score} < 15 \implies \textbf{HALT PIPELINE}$$

The engine **MUST NOT** invent a problem or brainstorm a startup concept. It must return:
> *"Could not find an evidence-backed operational problem in the supplied domain input. Failure reason: Existing workarounds or alternatives are sufficient, or search signals represent cosmetic complaints without operational consequence."*
