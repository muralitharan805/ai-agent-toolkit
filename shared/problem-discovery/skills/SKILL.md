---
name: problem-discovery
description: "Discovers, qualifies, and empirically validates software and automation problem candidates across B2B, developer tools, local retail, and civic utilities using dual-track prioritization, search refinement, multi-dimensional alternative audits, and small experiment validation gates."
metadata:
  framework_version: "Universal / Agnostic"
  last_verified_date: "2026-09-14"
---

# Universal Problem Discovery & Empirical Validation

Systematically discovers, qualifies, and tests software and automation opportunities grounded in traceable operational evidence. Replaces opinion surveys, premature brainstorming, and rigid SaaS calculators with the 7-stage evidence-and-experiment pipeline: 14-node forensic workflow mapping, dual-track prioritization (Commercial vs Free Utility), multi-platform search refinement, multi-dimensional competitor and non-software audits, inaction root cause analysis, small experiment validation gates, and smallest suitable solution scoping.

---

## 5-Pillar Modular Directory Architecture

```text
shared/problem-discovery/skills/
├── SKILL.md                                           # Tier 2 Core Pipeline Guidance (< 500 lines)
├── references/                                        # Tier 3 Authoritative Technical Manuals
│   ├── 14-node-workflow-and-glue-work.md             # Forensic workflow mapping & 4 friction archetypes
│   ├── 35-point-evidence-scoring-and-wtp.md          # Dual-track rubric & research prioritization thresholds
│   ├── discovery-frameworks-and-interviewing.md      # TRACE, FOCUS, The Mom Test & inaction root causes
│   ├── complaint-mining-and-dorking.md               # Search refinement heuristics & signal hygiene
│   ├── anti-opportunities-and-saturation-traps.md    # Multi-dimensional competitor fit & non-software checks
│   ├── solo-builder-micro-saas-strategy.md           # Smallest Suitable Solution architecture
│   ├── local-and-offline-discovery.md                # Retail counter shadowing & offline-first constraints
│   └── experiment-design-and-validation.md           # Low-cost prototypes & habit change friction
├── scripts/                                           # Standalone Automation Tools (PEP 723)
│   ├── score_problem_candidate.py                     # CLI candidate scoring & evidence verification engine
│   └── export_discovery_matrix.py                     # Central matrix CSV & ranking synchronizer
├── assets/                                            # Reusable Artifact Templates & JSON Schemas
│   ├── discovery-log-template.md                      # Standardized 8-section research dossier
│   └── scoring-matrix-schema.json                     # Draft 2020-12 dual-track evaluation schema
└── evals/                                             # Empirical Verification Suite
    ├── evals.json                                     # Multi-domain realistic evaluation test cases
    └── grading.json                                   # Automated evaluation pass-rate scorecard
```

---

## Authoritative Reference Grounding
- [14-Node Workflow & Glue-Work](references/14-node-workflow-and-glue-work.md): Deconstructs operational handoffs and human glue-work.
- [35-Point Evidence Scoring & Dual-Track Prioritization](references/35-point-evidence-scoring-and-wtp.md): Scoring dimensions, research prioritization, and evidence ladder.
- [Discovery Frameworks & Interviewing](references/discovery-frameworks-and-interviewing.md): TRACE, FOCUS, and inaction root cause analysis.
- [Complaint Mining, Dorking & Search Refinement](references/complaint-mining-and-dorking.md): Dorks, query relaxation, operator slang, and signal hygiene.
- [Anti-Opportunities & Saturation Traps](references/anti-opportunities-and-saturation-traps.md): Multi-dimensional competitor fit and non-software alternatives.
- [Smallest Suitable Solution Strategy](references/solo-builder-micro-saas-strategy.md): Choosing static utilities, extensions, or SaaS.
- [Local, Offline & Vernacular Discovery](references/local-and-offline-discovery.md): Counter shadowing, offline-first, and regional language workflows.
- [Experiment Design & Empirical Validation](references/experiment-design-and-validation.md): Low-cost trial archetypes and habit change friction.

---

## 7-Stage Sequential Execution Pipeline

Follow this disciplined pipeline to discover, qualify, and validate problem candidates:

```text
Signal Found → Problem Candidate → Corroborated Problem → Alternatives Checked → Small Experiment → Observed Outcome → Build / Revise / Park
```

At every stage, answer the **3 Mandatory Inquiries**:
1. *What do we know (proven facts)?*
2. *What do we not know (gaps & habit risks)?*
3. *What must be verified next (concrete trial)?*

### Stage 1: Domain Perimeter & Dual-Track Selection
1. Define the operational boundary: target role, workflow domain, geography, and volume.
2. Select the evaluation track:
   - **Track A (Commercial / Micro-SaaS)**: Paid software, recurring budgets, B2B workflow savings.
   - **Track B (Free Utility / Public Benefit / Local Community)**: Essential time saved, civic workflows, zero-overhead static distribution (WTP not required).

### Stage 2: Signal Mining, Search Refinement & Local Observation
1. Execute multi-platform search dorks across Reddit, review platforms, and app stores (see `references/complaint-mining-and-dorking.md`).
2. If queries return zero results, apply the **Search Refinement Cycle**: query relaxation, trade/operator slang, and regional/vernacular terms.
3. For retail shops, godowns, or field work, conduct physical **Counter Shadowing** (see `references/local-and-offline-discovery.md`).

### Stage 3: 14-Node Forensic Deconstruction & Inaction Root Cause
1. Map observed breakdowns across all 14 nodes: Actor, Trigger, Input, Steps, Tools, Decisions, Handoffs, Delays, Rework, Errors, Output, Cost, Risk, Audit.
2. Perform **Inaction Root Cause Analysis**: If operators have no workaround, determine whether the issue was abandoned due to prohibitive tool costs/complexity under severe consequence (high latent opportunity), or genuine low impact (reject).

### Stage 4: Multi-Dimensional Alternative & Non-Software Audit
Screen beyond simple software logos and pricing (see `references/anti-opportunities-and-saturation-traps.md`):
1. **Workflow & Language Fit**: Does the competitor solve this exact micro-bottleneck in the local language and currency?
2. **Device & Connectivity Realities**: Does the tool run offline on low-end mobile phones, or require desktop Chrome?
3. **Non-Software Sufficiency**: Can an Excel template, paper checklist, or WhatsApp group SOP eliminate 80% of the pain at zero cost? If yes, do not build custom software.
4. **Saturation Trap**: Discard markets dominated by subsidized category giants with lengthy committee voting.

### Stage 5: Per-Claim Evidence Scoring & Research Prioritization
1. Verify the **Evidence Quality Ladder**:
   - Level 1: Primary Behavioral (screen recordings, shadow sheets, error logs, transaction receipts).
   - Level 2: Primary Verbal (verifiable dated interview quotes with numbers and spend).
   - Level 3: Independent Corroboration (5+ reviews, forum posts, or JSON comment trees).
   - Level 4: Secondary Reports (max score = 1).
   - Level 5: Unvalidated Hypothesis (auto-score = 0).
2. Document source proof per claim (proof of frequency does NOT prove WTP).
3. Compute the 35-Point Research Prioritization Score using `scripts/score_problem_candidate.py`.
4. Enforce the **Unverified Input Hard Gate**: Scores entered without attached primary evidence artifacts output `UNVERIFIED_INPUT / RESEARCH_PRIORITY`, never `VALIDATED`.

### Stage 6: Small Experiment Design & Empirical Validation Gate
1. For qualified candidates ($\ge 23$ PTS), design a low-cost trial before scaffolding code (see `references/experiment-design-and-validation.md`):
   - *Concierge MVP*: Manually process data for 3–5 operators.
   - *Static Utility Trial*: Build a 1-page client-side file parser on Cloudflare Pages.
   - *Paper Prototype / WhatsApp Template*: Test with local operators for 1 week.
2. Document the experiment contract: Hypothesis, Test Format, Metrics, Explicit Failure Rule.
3. Validate demand through observed repeat usage, retention, or payment commitment.

### Stage 7: Smallest Suitable Solution Scoping & Dossier Sync
1. Select the leanest technical format (SaaS is NOT compulsory):
   - Non-software template $\rightarrow$ Static web utility $\rightarrow$ CLI tool $\rightarrow$ Browser extension $\rightarrow$ Full Micro-SaaS.
2. Generate and persist the research note into `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/PROB-[DATE]-[SCORE]PTS-[ID].md`.
3. Automatically synchronize `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/discovery_matrix.csv`.

---

## Gotchas & Market Validation Pitfalls

| Naive / Flawed Approach | Disciplined Evidence-Based Replacement | Why It Matters |
|---|---|---|
| Treating a 30-point score as "Validated" | Treating high scores as **Research Priority**; requiring observed usage for validation | Mathematical formulas cannot predict actual human habit change or checkout conversion. |
| Assuming "No Workaround = Low Pain" | Investigating the **root cause of inaction** (abandonment vs low impact) | Operators abandon critical tasks when available enterprise tools cost $10,000+ or require English desktop PCs. |
| Archiving if "3 tools under $50/mo exist" | Evaluating **workflow, language, offline, and device fit** | Global US-centric SaaS tools fail completely in local retail, vernacular, and offline-first environments. |
| Treating Reddit JSON as Level 1 proof | Classifying forum JSON trees as **Level 3 Corroborated Sentiment** | Data format does not alter evidence quality. JSON comment trees document reported sentiment, not observed behavior. |
| Giving bonus points for messy PDFs | Separating **User Pain** from **Technical Implementation Risk** | Hostile schemas make code harder to maintain; they do not prove that customers will adopt or pay. |
| Forcing every tool into a 3-tier SaaS | Selecting the **Smallest Suitable Solution** (stopping at a static tool or template) | Over-engineering unneeded multi-tenant SaaS creates endless database, server, and support debt. |
| Asking *"Would you buy this software?"* | Asking *"Can you show me the file or register where this was done yesterday?"* | Hypotheticals solicit polite compliments; historical artifacts reveal true operational bottlenecks. |
| Jumping into code without experiment | Executing a 5-day **Concierge or Static Utility experiment** first | Proves whether operators care enough about the output before writing backend infrastructure. |
