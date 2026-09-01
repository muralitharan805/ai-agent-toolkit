---
description: "Workflow to execute end-to-end FOCUS problem discovery, high-intent mining dorks, commercial pre-scoring audit guard, WTP economic metrics, 14-node mapping, 35-point evidence scoring, Obsidian logging, and 3-tier production tech stack prototype code generation."
trigger: manual
---

# Global Problem Discovery, Validation & Building Workflow

Follow this step-by-step pipeline when executing an evidence-driven problem discovery, validation, and prototyping request:

````
┌───────────────────────────────────────────────────────────────────────────┐
│           GLOBAL PROBLEM DISCOVERY & BUILDING WORKFLOW                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  STEP 1: FIELD IMMERSION & HIGH-INTENT MINING (STAGE F)                   │
│  ├── Search via Reddit, G2, Capterra, Trustpilot friction dorks.          │
│  └── Extract raw comment trees via Reddit `.json` endpoints.              │
│                                                                           │
│  STEP 2: 14-NODE WORKFLOW MAP & GLUE-WORK ANALYSIS (STAGE O)             │
│  ├── Map Actor, Trigger, Input, Steps, Handoffs, Delays, Cost, Risk.      │
│  └── Detect Human Glue-Work (System A -> Excel -> WhatsApp -> System B).  │
│                                                                           │
│  STEP 3: CAUSE DIGGING, WTP & EVIDENCE SEPARATION (STAGES C & U)          │
│  ├── Classify friction (Complaint, Symptom, Feature Request, Problem).    │
│  ├── Audit WTP Signals (Zapier spend, VAs hired, dev hours on scripts).   │
│  └── Separate facts into Evidence, Inference, Assumption, Unknown.        │
│                                                                           │
│  STEP 4: COMMERCIAL AUDIT, STOP CHECKS & 35-POINT SCORING (STAGE S)       │
│  ├── Commercial Pre-Scoring Audit: Check if >= 3 SaaS under $50/mo exist. │
│  ├── Evaluate 6 Mandatory Stop Checks & 35-Point Score.                   │
│  └── If Score < 15 -> Output "Could not find a valid problem".            │
│                                                                           │
│  STEP 5: OBSIDIAN DISCOVERY LOGGING                                       │
│  └── Save structured log note in `01_Inbox/discovery_logs/`.              │
│                                                                           │
│  STEP 6: 3-TIER PRODUCTION TECH STACK PROTOTYPING                         │
│  └── Scaffold Tier 1 (Angular client tool), Tier 2, or Tier 3 NestJS app. │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
````

## Execution Steps:

### Step 1: Field Immersion & High-Intent Data Mining (Stage F)
Define the research boundary (user segment, geography/industry, workflow examined, date, source IDs). Use `search_web` to discover high-intent friction, glue-work, and migration signals:
- **Reddit Dorks**: `site:reddit.com/r/[subreddit] "why is there no tool to" OR "hate that [tool] doesn't"`, `site:reddit.com/r/[subreddit] "spending hours manually" OR "our team is stuck using excel for"`, `site:reddit.com/r/[subreddit] "looking for a simple alternative to" OR "is there an API or script to"`.
- **Review & Complaint Dorks**: `site:g2.com/products/*/reviews "what do you dislike" OR "missing feature" OR "workaround"`, `site:capterra.com "cons" OR "manual export" OR "lack of integration"`, `site:trustpilot.com/review/* "terrible experience" OR "pricing increase" OR "broken sync"`.
- **Raw JSON Comment Extraction**: When fetching Reddit threads via `read_url_content`, prefer appending `.json` to public thread URLs (or using search `.json` endpoints) to pull raw structured comment trees rather than shallow HTML.

### Step 2: 14-Node Workflow Deconstruction & Glue-Work Check (Stage O)
Map all 14 execution nodes: Actor, Trigger, Input, Steps, Tools, Decisions, Handoffs, Waiting, Rework, Errors, Output, Cost, Risk, Audit. Detect whether the process relies on unversioned spreadsheets, manual copy-pasting, or messaging apps.

### Step 3: Cause Digging, WTP Audit & Evidence Discipline (Stages C & U)
Classify observed friction into Complaint, Symptom, Inconvenience, Feature Request, Problem Candidate, or Validated Problem. Audit Willingness to Pay (WTP) signals (paying Zapier/Make \$50–\$200/mo, hiring VAs/freelancers, spending $\ge 5$ dev hours/mo on internal scripts, or paying for multiple disconnected SaaS tools). Separate findings strictly into **Evidence**, **Inference**, **Assumption**, and **Unknown**. Categorize sources using the 5-Level Evidence Quality Ladder.

### Step 4: Commercial "Already Solved" Audit Guard, Stop Checks & 35-Point Scoring (Stage S)
1. **Commercial Pre-Scoring Audit**: Before scoring candidate $\ge 23$ points, execute a direct commercial scan (`best software for [workflow]` / `alternative to [workaround tool]`).
   - If $\ge 3$ dedicated modern SaaS products exist under \$50/mo with positive reviews solving this exact workflow $\rightarrow$ Trigger Stop Check #3 (*Alternative fits well*) and **PARK/ARCHIVE**.
   - Mark "Underserved / Validated" ONLY if existing tools are: (1) enterprise suite locked behind \$500+/mo sales calls, (2) deprecated/unmaintained tools with broken APIs, or (3) missing critical niche localization/compliance.
2. **Evaluate 6 Mandatory Stop Checks**:
   - Infrequent/no consequence?
   - Users have no workaround?
   - Affordable commercial alternative fits well (< \$50/mo)?
   - Single source evidence?
   - Training/policy issue?
   - Unreachable target user?
3. **Calculate 35-Point 7-Dimension Score**:
   - Frequency (1-3-5)
   - Consequence & WTP (1-3-5)
   - Workaround Strength & Economic Friction (1-3-5)
   - Evidence Quality (1-3-5)
   - Segment Reach (1-3-5)
   - Alternative Gap (1-3-5)
   - Access to Validation (1-3-5)
4. **Threshold Check**:
   - If Score < 15: Output `"Could not find a valid, evidence-backed problem in the supplied input."` and stop.
   - If Score >= 23: Proceed to Steps 5 & 6.

### Step 5: Obsidian Discovery Logging
Format and write a structured Markdown log note `PROB-[DATE]-[SCORE]PTS-[ID].md` (e.g. `PROB-20260830-31PTS-CAM-RECONCILIATION.md`) into the dedicated discovery logs sub-directory `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/`.

### Step 6: 3-Tier Production Tech Stack Prototyping
Scaffold production-grade code for:
- **Tier 1**: Free Client-Side Utility Tool (Standalone Angular / TypeScript component for `seyalicraft.com`, SEO-ready, zero-backend cost, Google AdSense container ready).
- **Tier 2**: Micro-Utility / Automation (Chrome Extension Manifest v3 or Node.js / Python CLI automation script, \$5–\$29 one-time purchase).
- **Tier 3**: B2B Micro-SaaS Product (NestJS backend + PostgreSQL/pgvector Prisma schema + Angular frontend + Stripe/Paddle billing model, \$29–\$199/month recurring subscription).

