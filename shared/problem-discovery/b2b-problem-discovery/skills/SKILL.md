---
name: b2b-problem-discovery
description: "Discovers and validates grounded B2B problem candidates using forensic 14-node workflow mapping, high-intent mining dorks, 35-point evidence scoring, and WTP metrics."
---

# Grounded B2B Problem Discovery & Validation

Systematically discovers, qualifies, and scopes B2B software opportunities grounded in traceable operational evidence. Replaces opinion surveys and premature brainstorming with 14-node forensic workflow mapping, Willingness to Pay (WTP) economic friction audits, 35-point evidence scoring, and commercial pre-scoring audit guards.

---

## 5-Pillar Architecture Directory Layout

```text
shared/problem-discovery/skills/b2b-problem-discovery/
├── SKILL.md                                           # Core procedural guidance (< 500 lines)
├── references/                                        # Authoritative deep-dive runbooks
│   ├── 14-node-workflow-and-glue-work.md             # Forensic workflow mapping and glue-work analysis
│   └── 35-point-evidence-scoring-and-wtp.md          # 7-dimension scoring rubric and stop checks
├── scripts/                                           # Standalone automation tools
│   └── score_problem_candidate.py                     # CLI candidate scoring and decision engine
├── assets/                                            # Reusable templates and schemas
│   ├── discovery-log-template.md                      # Standardized 9-section Obsidian log note
│   └── scoring-matrix-schema.json                     # JSON schema for evaluation payloads
└── evals/                                             # Verifiable test cases and grading
    ├── evals.json
    └── grading.json
```

---

## 6-Step Procedural Discovery Pipeline

Follow this disciplined pipeline to discover, validate, and qualify problem candidates:

### Step 1: Field Immersion & High-Intent Web Data Mining (Stage F)
Define the research boundary (user segment, geography/industry, workflow examined, date, source IDs). Execute targeted high-intent search dorks:
- **Reddit Dorks**:
  * `site:reddit.com/r/[subreddit] "why is there no tool to" OR "hate that [tool] doesn't"`
  * `site:reddit.com/r/[subreddit] "spending hours manually" OR "our team is stuck using excel for"`
  * `site:reddit.com/r/[subreddit] "looking for a simple alternative to" OR "is there an API or script to"`
- **Review & Complaint Dorks**:
  * `site:g2.com/products/*/reviews "what do you dislike" OR "missing feature" OR "workaround"`
  * `site:capterra.com "cons" OR "manual export" OR "lack of integration"`
  * `site:trustpilot.com/review/* "terrible experience" OR "pricing increase" OR "broken sync"`
- **Raw JSON Comment Extraction**: When fetching Reddit threads via `read_url_content`, prefer appending `.json` to public URLs to extract raw structured comment trees rather than shallow HTML snippets.

### Step 2: 14-Node Workflow Deconstruction & Glue-Work Analysis (Stage O)
Map all 14 operational nodes (see `references/14-node-workflow-and-glue-work.md`): Actor, Trigger, Input, Steps, Tools, Decisions, Handoffs, Waiting, Rework, Errors, Output, Cost, Risk, Audit.
- Uncover **Human Glue-Work**: `System A -> Human -> Unversioned Spreadsheet -> WhatsApp/Email -> System B`.

### Step 3: Cause Digging & Evidence Discipline (Stages C & U)
1. Classify observed friction:
   - *Complaint* (Emotional only; reject alone).
   - *Symptom* (Downstream effect; dig deeper).
   - *Inconvenience* (Low-consequence annoyance; park/reject).
   - *Feature Request* (Proposed solution; ask "why" twice to uncover root problem).
   - *Problem Candidate* (Specific user + repeated friction + measurable consequence).
   - *Validated Problem* (Independent evidence of recurrence + consequence + workaround + gap).
2. Separate findings strictly into **Evidence**, **Inference**, **Assumption**, and **Unknown**. Categorize sources using the 5-Level Evidence Quality Ladder.
3. Audit active **Willingness to Pay (WTP)** signals (paying \$50–\$200/mo for Zapier, hiring VAs/freelancers, or spending $\ge 5$ dev hours/mo on internal scripts).

### Step 4: Commercial "Already Solved" Audit Guard, Stop Checks & 35-Point Scoring (Stage S)
1. **Commercial Pre-Scoring Audit**: Before scoring candidate $\ge 23$ points, execute direct commercial scan (`best software for [workflow]` and `alternative to [workaround tool]`).
   - If $\ge 3$ dedicated modern SaaS products exist under \$50/mo solving this exact workflow $\rightarrow$ Trigger Stop Check #3 (*Alternative fits well*) and **PARK/ARCHIVE**.
2. **Evaluate 6 Mandatory Stop Checks** (infrequent/low-consequence, no workaround, commercial alternative fits well, single source, training issue, unreachable user).
3. **Run Automated Scoring Tool**:
   ```bash
   python3 scripts/score_problem_candidate.py \
     --freq 5 --consequence 5 --workaround 5 --evidence 5 --reach 3 --gap 5 --access 3
   ```
4. **Evaluate Decision Threshold**:
   - **Score < 15**: Output `"Could not find a valid, evidence-backed problem in the supplied input."` and stop.
   - **Score 15–22**: Keep investigating.
   - **Score $\ge 23$**: Proceed to Steps 5 and 6.

### Step 5: Obsidian Discovery Logging
Format and write a structured Markdown log note `PROB-[DATE]-[SCORE]PTS-[ID].md` into `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/` using `assets/discovery-log-template.md`.

### Step 6: 3-Tier Production Tech Stack Prototyping
Scope validated opportunities across 3 production build tiers:
- **Tier 1 (Free Utility Tool)**: Client-side Standalone Angular component (SEO-ready, zero-backend cost, AdSense ready).
- **Tier 2 (Micro-Utility / Automation)**: Chrome Extension (Manifest v3) or Node.js / Python CLI automation script (\$5–\$29 one-time).
- **Tier 3 (B2B Micro-SaaS Product)**: NestJS backend + PostgreSQL Prisma schema + Angular frontend + Stripe billing (\$29–\$199/month).

---

## Gotchas & Market Validation Pitfalls

| Naive / Flawed Approach | Disciplined Evidence-Based Replacement | Why It Matters |
|---|---|---|
| Asking "Would you buy this software if I built it?" | "Can you share your screen and walk me through the last time you did this?" | Hypothetical purchase intent yields 80%+ false positive validation; past behavior predicts actual WTP. |
| Counting complaints on social media as validation | Auditing economic workarounds (SOP spreadsheets, Zapier bills, VA invoices) | Free complaints indicate emotional annoyance, not commercial willingness to pay. |
| Assuming a market is wide open without commercial search | Executing pre-scoring commercial scan for SaaS $<\$50$/mo | Proposing solutions for workflows already solved by commoditized tools wastes engineering time. |
| Pitching solutions when discovery input lacks evidence | Outputting `"Could not find a valid, evidence-backed problem in the supplied input."` | Fabricating fake friction leads to building products nobody buys or needs. |
| Treating feature requests as customer problems | Asking "Why" at least twice to uncover the underlying operational bottleneck | Customers request local solutions to visible symptoms, not the fundamental root cause. |
