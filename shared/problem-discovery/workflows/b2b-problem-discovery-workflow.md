---
description: "Workflow to execute end-to-end FOCUS problem discovery, 14-node mapping, 35-point evidence scoring, Obsidian logging, and 3-tier prototype code generation."
trigger: manual
---

# Global Problem Discovery, Validation & Building Workflow

Follow this step-by-step pipeline when executing an evidence-driven problem discovery, validation, and prototyping request:

````
┌───────────────────────────────────────────────────────────────────────────┐
│           GLOBAL PROBLEM DISCOVERY & BUILDING WORKFLOW                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  STEP 1: FIELD IMMERSION & WEB MINING (STAGE F)                           │
│  ├── Search target subreddits, G2 2-star reviews, or job postings.        │
│  └── Fetch live content using `search_web` & `read_url_content`.          │
│                                                                           │
│  STEP 2: 14-NODE WORKFLOW MAP & GLUE-WORK ANALYSIS (STAGE O)             │
│  ├── Map Actor, Trigger, Input, Steps, Handoffs, Delays, Cost, Risk.      │
│  └── Detect Human Glue-Work (System A -> Excel -> WhatsApp -> System B).  │
│                                                                           │
│  STEP 3: CAUSE DIGGING, EVIDENCE SEPARATION & AUDIT (STAGES C & U)        │
│  ├── Classify friction (Complaint, Symptom, Feature Request, Problem).    │
│  ├── Separate facts into Evidence, Inference, Assumption, Unknown.        │
│  └── Apply 5-Level Evidence Quality Ladder.                               │
│                                                                           │
│  STEP 4: 6 MANDATORY STOP CHECKS & 35-POINT SCORING (STAGE S)             │
│  ├── Evaluate 6 Stop Checks (infrequent, no workaround, etc.).            │
│  ├── Compute 35-Point 7-Dimension Evidence Score.                         │
│  └── If Score < 15 -> Output "Could not find a valid problem".            │
│                                                                           │
│  STEP 5: OBSIDIAN DISCOVERY LOGGING                                       │
│  └── Save structured log note in `01_Inbox/discovery_logs/`.              │
│                                                                           │
│  STEP 6: 3-TIER SOLUTION PROTOTYPING                                      │
│  └── Scaffold Tier 1 (seyalicraft.com free tool), Tier 2, or Tier 3 code. │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
````

## Execution Steps:

### Step 1: Field Immersion & Web Data Mining (Stage F)
Define the research boundary (user segment, geography/industry, workflow examined, date, source IDs). Use `search_web` to discover real user discussions (e.g. `site:reddit.com/r/accounting "spreadsheet workaround"` or `site:g2.com "property management reviews"`). Fetch thread contents via `read_url_content`.

### Step 2: 14-Node Workflow Deconstruction & Glue-Work Check (Stage O)
Map all 14 execution nodes: Actor, Trigger, Input, Steps, Tools, Decisions, Handoffs, Waiting, Rework, Errors, Output, Cost, Risk, Audit. Detect whether the process relies on unversioned spreadsheets, manual copy-pasting, or messaging apps.

### Step 3: Cause Digging, Classification & Evidence Discipline (Stages C & U)
Classify observed friction into Complaint, Symptom, Inconvenience, Feature Request, Problem Candidate, or Validated Problem. Separate findings strictly into **Evidence**, **Inference**, **Assumption**, and **Unknown**. Categorize sources using the 5-Level Evidence Quality Ladder.

### Step 4: Mandatory Stop Checks & 35-Point Scoring (Stage S)
1. **Evaluate 6 Mandatory Stop Checks**:
   - Infrequent/no consequence?
   - Users have no workaround?
   - Affordable alternative fits well?
   - Single source evidence?
   - Training/policy issue?
   - Unreachable target user?
2. **Calculate 35-Point 7-Dimension Score**:
   - Frequency (1-3-5)
   - Consequence (1-3-5)
   - Workaround Strength (1-3-5)
   - Evidence Quality (1-3-5)
   - Segment Reach (1-3-5)
   - Alternative Gap (1-3-5)
   - Access to Validation (1-3-5)
3. **Threshold Check**:
   - If Score < 15: Output `"Could not find a valid, evidence-backed problem in the supplied input."` and stop.
   - If Score >= 23: Proceed to Steps 5 & 6.

### Step 5: Obsidian Discovery Logging
Format and write a structured Markdown log note `PROB-[DATE]-[SCORE]PTS-[ID].md` (e.g. `PROB-20260830-31PTS-CAM-RECONCILIATION.md`) into the dedicated discovery logs sub-directory `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/`.

### Step 6: 3-Tier Solution Prototyping
Scaffold production-grade code for:
- **Tier 1**: Free Client-Side Utility Tool (HTML/JS/Angular for `seyalicraft.com`).
- **Tier 2**: Micro-Utility / Chrome Extension (Manifest v3 or CLI tool).
- **Tier 3**: B2B Micro-SaaS Product (NestJS backend + Angular frontend + Postgres schema).
