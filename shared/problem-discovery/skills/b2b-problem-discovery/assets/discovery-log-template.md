# Discovery Log: PROB-[YYYYMMDD]-[SCORE]PTS-[SLUG]

## 1. Research Boundary
- **Candidate ID**: `PROB-[YYYYMMDD]-[SCORE]PTS-[SLUG]`
- **Target User Segment**: `[e.g. Mid-market Commercial Property Managers]`
- **Target Geography & Industry**: `[e.g. US / Commercial Real Estate]`
- **Specific Workflow Examined**: `[e.g. Annual Common Area Maintenance (CAM) Reconciliation]`
- **Investigation Date**: `[YYYY-MM-DD]`
- **Primary Source IDs / Thread URLs**:
  - `[SRC-01] reddit.com/r/commercialrealestate/comments/...`
  - `[SRC-02] G2 Review for Yardi Voyager: ...`

---

## 2. 14-Node Forensic Workflow Map

| Node | Finding | Operational Evidence |
|---|---|---|
| **1. Actor** | `[Role]` | `[Who sits in the chair]` |
| **2. Trigger** | `[Event]` | `[Email, invoice, calendar date]` |
| **3. Input** | `[Data/Format]` | `[Unstructured PDF, portal export]` |
| **4. Steps** | `[Manual Actions]` | `[Step-by-step click path]` |
| **5. Tools** | `[Software/Spreadsheets]` | `[Applications open simultaneously]` |
| **6. Decisions** | `[Business Rules]` | `[Threshold logic, pass/fail review]` |
| **7. Handoffs** | `[Transfers]` | `[Handoff across departments/parties]` |
| **8. Waiting** | `[Delays]` | `[Idle time waiting for approvals]` |
| **9. Rework** | `[Re-keying]` | `[Re-typing data between systems]` |
| **10. Errors** | `[Failure Modes]` | `[Discrepancy rates, formula errors]` |
| **11. Output** | `[Deliverable]` | `[Final tenant letter, ERP entry]` |
| **12. Cost** | `[Labor/Spend]` | `[Hours per week / monthly software fee]` |
| **13. Risk** | `[Penalties/Loss]` | `[Tenant dispute, audit penalty]` |
| **14. Audit** | `[Verification]` | `[CFO review, external auditor]` |

**Human Glue-Work Identified**:
`[System A] -> [Manual CSV Export] -> [40-Tab Excel Spreadsheet] -> [System B]`

---

## 3. Observed Friction & Classification

- **Category**: `[Complaint | Symptom | Inconvenience | Feature Request | Problem Candidate | Validated Problem]`
- **Description**: `[Clear explanation of the acute operational friction]`

---

## 4. Candidate Problem Statement

> When **[specific user]** is **[context/trigger]**, they must **[current workaround]**, which causes **[unwanted outcome]** resulting in **[measurable financial/operational consequence]**.

---

## 5. Evidence Table & Quality Ladder

| Source ID | Evidence Level | Verbatim Quote / Artifact | Key Fact Extracted |
|---|---|---|---|
| `[SRC-01]` | `Level 1 (Behavioral)` | `"[Quote]"` | `[Fact]` |
| `[SRC-02]` | `Level 3 (Corroboration)` | `"[Quote]"` | `[Fact]` |

### Factual Separation:
- **Evidence**: `[Verified facts from sources]`
- **Inference**: `[Direct logical deduction]`
- **Assumption**: `[Premise requiring testing]`
- **Unknown**: `[Explicitly missing data - never guessed]`

---

## 6. Existing Alternatives & Commercial Pre-Scoring Audit

| Tool / Alternative | Monthly Pricing | Gap / Missing Capability |
|---|---|---|
| `[Enterprise ERP]` | `>$500/mo` | `[Requires custom developer consultants]` |
| `[Manual Spreadsheet]` | `$0 (Internal Labor)` | `[Prone to formula breakage, 15 hrs/mo]` |

**Commercial "Already Solved" Audit Guard Check**:
- Dedicated SaaS under \$50/mo found? `[YES / NO]`
- If YES ($\ge 3$ SaaS): **Trigger Stop Check #3 and ARCHIVE.**

---

## 7. Disconfirming Evidence & 6 Mandatory Stop Checks

1. Infrequent & low consequence? `[NO]`
2. No real workaround? `[NO]`
3. Commercial alternative fits well (< \$50/mo)? `[NO]`
4. Single-source bias? `[NO]`
5. Internal training/adoption issue? `[NO]`
6. Unreachable target audience? `[NO]`

---

## 8. 35-Point 7-Dimension Score & Status

| Dimension | Points (1, 3, 5) | Evidence Rationale |
|---|---|---|
| **1. Frequency** | `[5]` | `[Daily / Weekly execution]` |
| **2. Consequence & WTP** | `[5]` | `[Active WTP: $150/mo Zapier spend, 10 hrs overtime]` |
| **3. Workaround Strength** | `[5]` | `[Maintained 40-tab Excel model with VLOOKUPs]` |
| **4. Evidence Quality** | `[5]` | `[Level 1 SOP spreadsheets and real invoices]` |
| **5. Segment Reach** | `[3]` | `[Observed across 8 commercial property firms]` |
| **6. Alternative Gap** | `[5]` | `[Only $500+/mo enterprise suites exist]` |
| **7. Access to Validation** | `[3]` | `[Direct connection to 4 property managers]` |
| **TOTAL SCORE** | **`[31 / 35 PTS]`** | **`STRONG VALIDATION CANDIDATE`** |

**Status**: `[Observed | Investigating | Evidence-backed hypothesis | Validated | Parked | Rejected]`

---

## 9. Next Validation Actions & 3-Tier Production Prototype Scoping

- **Tier 1 (Free SEO Utility Tool)**: Standalone Angular component (e.g. CAM Lease Percentage Calculator for `yourdomain.com`).
- **Tier 2 (Micro-Utility)**: Chrome Extension (e.g. Automated PDF invoice lease extractor).
- **Tier 3 (B2B Micro-SaaS Product)**: NestJS backend + PostgreSQL Prisma schema + Angular frontend + Stripe billing (\$49–\$149/mo).
