---
tags: [discovery-log, candidate, unvalidated]
created: YYYY-MM-DD
candidate_id: PROB-YYYYMMDD-ID
domain: [Industry / Domain / Vertical]
target_role: [Exact Job Title / Operator Role]
evidence_level: [Level 1 | Level 2 | Level 3 | Level 4 | Level 5]
total_score: [0–35]
status: [exploring | qualified | validated | discarded | parked]
---

# 📋 Problem Discovery Log: [Candidate Name]

## 1. Problem Statement & Operational Context
- **What is broken?**: [Single concise sentence describing the core operational friction]
- **Who experiences this?**: [Target role, company size, volume, geography]
- **Trigger Event**: [What operational event starts this friction?]
- **Current Workaround**: [Spreadsheet / WhatsApp / Physical paperwork / Copy-paste]

---

## 2. 14-Node Forensic Workflow Deconstruction

| Node | Name | Observation Details |
| :---: | :--- | :--- |
| **1** | **Actor** | [Job title, technical literacy, who gets blamed if it breaks] |
| **2** | **Trigger** | [Exact event initiating the task: email, invoice, webhook, calendar date] |
| **3** | **Input** | [Raw data format: PDF, unformatted CSV, API payload, physical scan] |
| **4** | **Steps** | [Click-by-click actions taken across screens] |
| **5** | **Tools** | [All software, spreadsheets, and communication apps touched] |
| **6** | **Decisions** | [Threshold logic determining branches: variance %, approvals] |
| **7** | **Handoffs** | [Points where data/work passes between people or systems] |
| **8** | **Delays** | [Idle wait times between steps: waiting for vendor or signoff] |
| **9** | **Rework** | [Frequency of re-entry due to validation errors or schema mismatch] |
| **10** | **Errors** | [Common failure points: typos, broken formats, duplicate records] |
| **11** | **Output** | [Final deliverable produced: reconciliation report, tax filing, clean DB] |
| **12** | **Cost** | [Calculated weekly labor hours × loaded hourly wage] |
| **13** | **Risk** | [Statutory penalty, financial loss, churn, or legal exposure] |
| **14** | **Audit** | [Who signs off and how chain-of-custody proof is preserved] |

---

## 3. Evidence Signals & Source Traceability

- **Signal 1 (Community / Forum)**: [Link / quote from Reddit, Hacker News, or specialized forum]
- **Signal 2 (Software Reviews)**: [Link / quote from G2, Capterra, or Trustpilot 1-star/2-star reviews]
- **Signal 3 (Direct Operator / Job Posting)**: [Direct quote, screen recording summary, or job description]

---

## 4. Evidence Quality Ladder Hard-Gate Check

- **Assigned Evidence Level**: `[Level 1 | Level 2 | Level 3 | Level 4 | Level 5]`
- **Source Verification**:
  - [ ] Level 1 (Primary Behavioral: direct screen recording, sanitized shadow Excel, invoice logs)
  - [ ] Level 2 (Primary Verbal: dated operator interview quotes with exact numbers)
  - [ ] Level 3 (Independent Corroboration: ≥ 5 unconnected review complaints)
  - [ ] Level 4 (Secondary Interpretation: industry reports; max dimension score = 1)
  - [ ] Level 5 (Unvalidated Hypothesis: AI-generated lists; auto-scores 0)

---

## 5. Existing Workaround & Economic Audit

- **Active Labor Cost**: [e.g., 6 hours/week × $35/hour = $210/week wasted]
- **Workaround Software Spend**: [e.g., $100/mo Zapier plan + $200/mo freelance data entry]
- **Cost of Inaction / Error**: [e.g., $5,000 regulatory penalty or lost client invoice dispute]

---

## 6. 35-Point Evidence Scoring Matrix

| Dimension | Points (0–5) | Justification & Source Grounding |
| :--- | :---: | :--- |
| **1. Frequency** | [0–5] | [Daily continuous = 5, Weekly = 4, Monthly = 2, Ad-hoc = 0] |
| **2. Financial Severity & Risk** | [0–5] | [Statutory fines / lost cash = 5, lost hours = 4, cosmetic = 0] |
| **3. Workaround Investment** | [0–5] | [Dedicated staff / complex macro = 5, custom sheet = 4, none = 0] |
| **4. Willingness to Pay (WTP)** | [0–5] | [High ROI $200+/mo = 5, $29–$199/mo = 4, expect free = 0] |
| **5. Single Decision-Maker** | [0–5] | [Self-serve operator / owner = 5, manager card = 4, RFP = 0] |
| **6. Solo Feasibility** | [0–5] | [Micro-tool / extension = 5, clean full-stack = 4, deep AI/hardware = 0] |
| **7. Discrepancy & Fragility** | [0–5] | [Hostile PDFs / mismatch = 5, manual diff = 4, static API = 0] |
| **TOTAL SCORE** | **[0–35]** | **Pass Threshold: ≥ 23 PTS** |

### Decision Triage:
- [ ] **Score < 15 PTS**: Halt discovery. Output anti-hallucination no-problem fallback.
- [ ] **Score 15–22 PTS**: Reject / Kill. Insufficient commercial urgency.
- [ ] **Score 23–27 PTS**: Qualified Opportunity. Conduct 2–3 field user shadow sessions.
- [ ] **Score 28–35 PTS**: Tier-1 Gold Problem. Proceed to 3-tier prototype derivation.

---

## 7. Commercial "Already Solved" Audit & Stop Checks

- **Pre-Scoring Commercial Scan**: Checked Google (`best software for [workflow]` and `alternatives to [tool]`).
  - Existing Competitors: [List tools found and pricing models]
- **Stop Checks Evaluation**:
  - [ ] 1. Infrequent & Low Impact?
  - [ ] 2. No Meaningful Workaround?
  - [ ] 3. Commercial Alternative Fits Well (< $50/mo)?
  - [ ] 4. Single Source Bias?
  - [ ] 5. Internal Training / Policy Issue?
  - [ ] 6. Unreachable Target Audience?
  - [ ] 7. Saturation Trap (brutally competitive category)?

---

## 8. 3-Tier Solution Wedge Derivation

*(Triggered only if Total Score ≥ 28 PTS)*

- **Tier 1 (Free Client-Side Utility)**:
  - Tool Name: [Name] Quick Inspector
  - Input: [Drag-and-drop CSV / PDF]
  - Instant Value: [Clean highlight table of variances / missing items]
  - Delivery: Client-side Standalone Angular / Static Web Utility (SEO / Lead Magnet)
- **Tier 2 (Micro-Utility / Extension)**:
  - Tool Name: [Name] Workflow Extension
  - Format: Chrome Extension (Manifest V3) or CLI binary
  - Pricing: $19–$49 one-time payment
- **Tier 3 (Recurring B2B / Pro Micro-SaaS)**:
  - Product Name: [Name] Cloud Platform
  - Architecture: NestJS API + PostgreSQL (Prisma) + Angular UI + Stripe Billing
  - Recurring Feature: Scheduled automated synchronization, webhooks, multi-user audit trail
  - Pricing: $49–$199 / month

---

## 9. Verification & Next Steps

1. [Next field interview or screen share scheduled]
2. [Specific raw sample files requested for testing: e.g., 2 sanitized sample CSVs]
3. [Prototype milestone date]
