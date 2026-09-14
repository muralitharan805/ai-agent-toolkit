---
tags: [discovery-log, candidate, unvalidated]
created: YYYY-MM-DD
candidate_id: PROB-YYYYMMDD-ID
track: [commercial | free_utility]
validation_status: [unverified | research_priority | corroborated | experiment_validated | parked | rejected]
priority_score: [0–35]
target_role: [Exact Job Title / Operator / Citizen Role]
evidence_level: [Level 1 | Level 2 | Level 3 | Level 4 | Level 5]
---

# 📋 Problem Discovery Log: [Candidate Name]

## 1. Problem Statement & PAIN Extraction
- **Source URL & Date**: [Exact URL or physical encounter date: YYYY-MM-DD]
- **Person (Actor & Geography)**: [Exact job title/role, company/fleet size, geography, language, and device constraints]
- **Activity (Goal)**: [What specific operational outcome are they attempting to complete?]
- **Incident (Where It Breaks)**: [Where precisely does the breakdown occur: handoff, format mismatch, or cutoff?]
- **Number (Frequency & Loss)**: [Verifiable recurrence and measurable hours wasted, money lost, or penalty rate]
- **Current Workaround**: [Spreadsheet / WhatsApp / Physical notebook / Manual copy-paste]
- **Existing Solutions Tried**: [Specific software, plugins, or workarounds tested and where they failed]
- **Inaction Analysis**: [If no workaround exists, did users abandon it due to lack of accessible tools or low consequence?]

---

## 2. 14-Node Forensic Workflow Deconstruction

| Node | Name | Observation Details |
| :---: | :--- | :--- |
| **1** | **Actor** | [Job title, technical/vernacular literacy, device used] |
| **2** | **Trigger** | [Exact event initiating the task: email, invoice, closing time, webhook] |
| **3** | **Input** | [Raw data format: paper register, physical scan, PDF, CSV, WhatsApp photo] |
| **4** | **Steps** | [Action-by-action steps taken across tools, screens, or counters] |
| **5** | **Tools** | [All physical registers, software, spreadsheets, and messaging apps used] |
| **6** | **Decisions** | [Threshold logic determining branches: variance %, approvals] |
| **7** | **Handoffs** | [Points where data/work passes between people, shifts, or systems] |
| **8** | **Delays** | [Idle wait times: waiting for vendor, accountant, or network signal] |
| **9** | **Rework** | [Frequency of re-entry due to calculation mistakes or schema drift] |
| **10** | **Errors** | [Common failure points: calculation errors, typos, missing pages] |
| **11** | **Output** | [Final deliverable produced: closing tally, tax filing, clean DB] |
| **12** | **Cost / Time** | [Calculated weekly clerical hours wasted × hourly loaded cost] |
| **13** | **Risk** | [Statutory penalty, financial loss, stock shortage, or churn] |
| **14** | **Audit** | [Who signs off and how chain-of-custody proof is preserved] |

---

## 3. Per-Claim Evidence Matrix & Source Grounding

*Document source proof separately for each operational claim. Evidence for frequency does NOT prove willingness to pay or workaround investment.*

| Dimension Claim | Asserted Value | Source Artifact / URL / Quote | Evidence Level (1–5) | Confidence |
| :--- | :--- | :--- | :---: | :--- |
| **Frequency Claim** | [e.g. Daily closing] | [Quote / screen recording / counter log] | [1–5] | [High/Med/Low] |
| **Severity / Risk** | [e.g. $500 penalty] | [Regulatory rule / historical fine receipt] | [1–5] | [High/Med/Low] |
| **Workaround / Inaction**| [e.g. 5-hr Excel/WA] | [Screenshot of notebook or spreadsheet] | [1–5] | [High/Med/Low] |
| **WTP / Utility Push** | [e.g. $49/mo or high] | [Actual invoice paid / organic search vol] | [1–5] | [High/Med/Low] |

---

## 4. Alternatives & Non-Software Audit

- **Commercial & Free Competitors**:
  - Existing Tools: [List existing products and evaluate exact fit]
  - Workflow Fit: [Does it solve this exact micro-bottleneck, or is it bloated generic software?]
  - Local / Vernacular Fit: [Does it support local language, currency, and local compliance?]
  - Device / Connectivity Fit: [Does it work offline / on entry-level mobile, or requires desktop Chrome?]
  - Switching Friction: [Why haven't operators migrated to this tool?]
- **Non-Software Alternative**:
  - Could an Excel template, printed checklist, or WhatsApp group SOP solve 80% of this? [Yes/No - Rationale]

---

## 5. 35-Point Research Prioritization Matrix

| Dimension | Points (0–5) | Justification & Grounding |
| :--- | :---: | :--- |
| **1. Frequency** | [0–5] | [Daily = 5, Weekly = 4, Monthly = 2, Ad-hoc = 0] |
| **2. Severity & Risk** | [0–5] | [Statutory fines / lost cash = 5, lost hours = 4, cosmetic = 0] |
| **3. Workaround Investment** | [0–5] | [Dedicated staff / macro = 5, custom notebook/sheet = 4, none = 0] |
| **4. Track Dimension:** | [0–5] | |
| - *Track A: WTP Clarity* | | [High ROI $200+/mo = 5, $29–$199/mo = 4, expect free = 0] |
| - *Track B: Utility & Adoption* | | [Daily essential = 5, 1–3 hrs/wk saved = 4, one-time curiosity = 0] |
| **5. Single Decision-Maker** | [0–5] | [Self-serve operator / owner = 5, manager card = 4, RFP = 0] |
| **6. Solo Feasibility** | [0–5] | [Micro-tool / extension = 5, clean full-stack = 4, deep AI/hardware = 0] |
| **7. Process Discrepancy** | [0–5] | [Acute handoff failure = 5, manual diff = 4, unified tool = 0] |
| **TOTAL RESEARCH PRIORITY** | **[0–35]** | **Priority Threshold: ≥ 23 PTS** |

### Status Classification:
- [ ] **UNVERIFIED_INPUT**: Raw numbers entered without attached evidence artifacts. High score marks research priority, not validated demand.
- [ ] **REJECT / PARK**: Score < 23 PTS or Stop Check triggered.
- [ ] **QUALIFIED_RESEARCH_PRIORITY**: Score ≥ 23 PTS with corroborated multi-source evidence. Proceed to experiment design.
- [ ] **EXPERIMENT_VALIDATED**: Observed repeat usage or payment commitment achieved during small experiment.

---

## 6. Experiment Design & Validation Contract

*(Required before writing production software)*
- **Core Hypothesis**: [If we provide X, target operators will achieve Y within Z days]
- **Target Participants**: [Exact 3–5 operators or 20 community members testing]
- **Test Mechanism**: [Concierge MVP / Static Web Utility / Paper Prototype / Interactive Walk]
- **Time Window**: [e.g. 7 calendar days]
- **Objective Success Metric**: [e.g. ≥ 3 operators use it consistently for 5 consecutive days]
- **Observed Experiment Outcome**: [Document what actually happened during the trial]
- **Decision**: [Advance to build Smallest Suitable Solution / Revise / Park]

---

## 7. Smallest Suitable Solution Scoping

*(Select the leanest technical format that solves the bottleneck; SaaS is NOT compulsory)*

- **Chosen Solution Format**:
  - [ ] Non-Software Template / SOP (Stop here)
  - [ ] Static Client-Side Web Utility (Standalone Angular / Vanilla JS, zero backend, client-side only)
  - [ ] CLI Automation Tool (Standalone script / binary)
  - [ ] Browser Extension (Manifest V3 DOM injection / export)
  - [ ] Full-Stack Micro-SaaS (NestJS + Postgres + Stripe - only if background sync / multi-user strictly required)
- **Tool Name**: [Proposed Name]
- **Delivery & Distribution**: [How the operator accesses it: URL, Web Store, WhatsApp, GitHub Pages]

---

## 8. Verification & Next Steps
- **What do we know?**: [Confirmed operational facts and quotes with exact source links]
- **What remains Unknown?**: *(State "Unknown" explicitly. DO NOT allow AI or assistants to fill plausible values or guess unverified numbers)*
- **Next Concrete Validation Action**: [Exact field test, conversation, or experiment scheduled]
