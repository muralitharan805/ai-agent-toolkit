---
name: problem-discovery
description: "Discovers, validates, and qualifies software and automation problem candidates across B2B, B2C, Micro-SaaS, and developer workflows using forensic 14-node mapping, mining dorks, 35-point scoring, and 3-tier scoping."
metadata:
  framework_version: "Universal / Agnostic"
  last_verified_date: "2026-09-12"
---

# Universal Problem Discovery & Validation

Systematically discovers, qualifies, and scopes high-leverage software and automation opportunities grounded in traceable operational evidence. Replaces opinion surveys and premature brainstorming with the 8-stage discovery pipeline: 14-node forensic workflow mapping, multi-platform complaint mining, Willingness to Pay (WTP) economic audits, deterministic 35-point evidence scoring, saturation trap gatekeeping, and 3-tier production prototype scoping.

---

## 5-Pillar Modular Directory Architecture

```text
shared/problem-discovery/skills/
├── SKILL.md                                           # Tier 2 Core Pipeline Guidance (< 500 lines)
├── references/                                        # Tier 3 Authoritative Technical Manuals
│   ├── 14-node-workflow-and-glue-work.md             # Forensic workflow mapping & 4 friction archetypes
│   ├── 35-point-evidence-scoring-and-wtp.md          # 7-dimension scoring rubric & evidence ladder hard gate
│   ├── discovery-frameworks-and-interviewing.md      # TRACE, FOCUS, The Mom Test & operator shadowing
│   ├── complaint-mining-and-dorking.md               # Multi-platform Google Dorking & automated ingestion
│   ├── anti-opportunities-and-saturation-traps.md    # 3 fatal idea archetypes & 4-question risk screen
│   └── solo-builder-micro-saas-strategy.md           # Gold problem profile & 3-tier validation roadmap
├── scripts/                                           # Standalone Automation Tools (PEP 723)
│   └── score_problem_candidate.py                     # CLI 35-point candidate scoring and decision engine
├── assets/                                            # Reusable Artifact Templates & JSON Schemas
│   ├── discovery-log-template.md                      # Standardized 9-section Obsidian research dossier
│   └── scoring-matrix-schema.json                     # Draft 2020-12 evaluation schema
└── evals/                                             # Empirical Verification Suite
    ├── evals.json                                     # Multi-domain realistic evaluation test cases
    └── grading.json                                   # Automated evaluation pass-rate scorecard
```

---

## Authoritative Reference Grounding
- [14-Node Workflow & Glue-Work](references/14-node-workflow-and-glue-work.md): Deconstructs operational steps and the Universal Broken Loop.
- [35-Point Evidence Scoring & WTP](references/35-point-evidence-scoring-and-wtp.md): 7 scoring dimensions, thresholds, and evidence ladder hard gate.
- [Discovery Frameworks & Interviewing](references/discovery-frameworks-and-interviewing.md): TRACE, FOCUS, and The Mom Test field protocols.
- [Complaint Mining & Dorking](references/complaint-mining-and-dorking.md): High-intent search dorks for Reddit, G2, Capterra, and App Stores.
- [Anti-Opportunities & Saturation Traps](references/anti-opportunities-and-saturation-traps.md): Red flags, saturated markets, and risk screens.
- [Solo Builder Micro-SaaS Strategy](references/solo-builder-micro-saas-strategy.md): Unit economics and 3-tier progressive validation.

---

## 8-Stage Sequential Execution Pipeline

Follow this disciplined pipeline to discover, validate, and qualify software problem candidates:

### Stage 1: Domain Boundary Definition & Problem-First Mindset
1. Define the research perimeter: target user role, operational domain (B2B, Developer Tools, Micro-SaaS, E-Commerce), geography, and volume.
2. Enforce the **Problem-First Axiom**: Never ask *"What app can I build?"* Always investigate *"What operational handoff keeps breaking, and why is the current workaround terrible?"*
3. Distinguish between cosmetic inconveniences and economic pain. Valid candidates require active wasted labor or financial/regulatory liability.

### Stage 2: Automated Signal Mining & Multi-Platform Dorking
Execute high-intent search dorks across operator communities and review platforms (see `references/complaint-mining-and-dorking.md`):
- **Reddit Operator Discussions**:
  * `site:reddit.com inurl:comments "[domain]" "spend hours every week"`
  * `site:reddit.com inurl:comments "[domain]" "our team is stuck using excel for"`
  * `site:reddit.com inurl:comments "[domain]" "nightmare to reconcile"`
- **B2B Review Gaps (G2, Capterra, Trustpilot)**:
  * `site:g2.com/products/* "[domain]" "what do you dislike" OR "missing"`
  * `site:capterra.com "[domain]" "manual export" OR "clunky"`
- **Vertical App Stores (Shopify, WordPress, Chrome Web Store)**:
  * `site:apps.shopify.com/reviews "[domain]" "fails to sync"`
  * `site:chromewebstore.google.com/detail "[domain]" "no longer works"`
- **Raw JSON Extraction**: Append `.json` to public Reddit thread URLs to extract structured comment trees directly.

### Stage 3: 14-Node Forensic Workflow Deconstruction
Map every observed workflow breakdown across all 14 operational nodes (see `references/14-node-workflow-and-glue-work.md`):
1. *Actor*, 2. *Trigger*, 3. *Input*, 4. *Steps*, 5. *Tools*, 6. *Decisions*, 7. *Handoffs*, 8. *Delays*, 9. *Rework*, 10. *Errors*, 11. *Output*, 12. *Cost*, 13. *Risk*, 14. *Audit*.
- Identify **Human Glue-Work**: Isolate where operators manually bridge disconnected systems using spreadsheets, copy-paste routines, or messaging groups.

### Stage 4: Saturation & Trap Gatekeeper
Screen against the 3 fatal idea archetypes before proceeding (see `references/anti-opportunities-and-saturation-traps.md`):
- **The Saturation Trap**: Avoid markets dominated by subsidized category giants with multi-month committee voting (e.g., apartment/housing society management, generic coaching institute ERPs).
- **The Phantom Problem**: Discard vocal complaints where users lack economic budget or active willingness to pay.
- **The Platform Risk Box**: Reject dependencies on unapproved private APIs or fragile screen scrapers.

### Stage 5: Competitor "Already Solved" Audit Guard & 6 Stop Checks
1. Execute direct commercial search: `best software for [workflow]` and `alternative to [workaround tool]`.
2. **Stop Check #3 Guard**: If $\ge 3$ dedicated, modern SaaS tools exist under $\$50/\text{month}$ solving this exact workflow $\longrightarrow$ Trigger Stop Check #3 (*Alternative fits well*) and **PARK/ARCHIVE**.
3. Evaluate all **6 Mandatory Stop Checks**:
   - 1. Infrequent & low operational consequence.
   - 2. No meaningful workaround maintained.
   - 3. Commercial alternative fits well ($<\$50/\text{month}$).
   - 4. Single source bias / uncorroborated complaint.
   - 5. Internal policy or onboarding issue (not software gap).
   - 6. Target users unreachable for direct validation.

### Stage 6: Deterministic 35-Point Evidence Scoring & Hard Gate
Score strictly on documented, source-backed evidence using `scripts/score_problem_candidate.py`:
1. Verify **Evidence Quality Ladder** (Hard Gate):
   - Level 1 (Behavioral) / Level 2 (Verbal) / Level 3 (Corroborated Reviews): Full 0–5 scoring allowed.
   - Level 4 (Secondary Reports): Max dimension score capped at 1.
   - Level 5 (AI Hypothesis): Auto-scores 0 across all dimensions.
2. Score across the 7 dimensions (0–5):
   *1. Frequency*, *2. Severity & Risk*, *3. Workaround Investment*, *4. WTP Clarity*, *5. Single Decision-Maker*, *6. Solo Feasibility*, *7. Data Discrepancy*.
3. Execute CLI scoring tool:
   ```bash
   python3 scripts/score_problem_candidate.py \
     --freq 5 --severity 5 --workaround 4 --wtp 5 --decision-maker 5 --feasibility 4 --discrepancy 4 --evidence-level 1
   ```
4. Evaluate Triage Action:
   - **Score $< 15$ PTS**: Output `"Could not find an evidence-backed operational problem in the supplied domain input."` and HALT.
   - **Score 15–22 PTS**: REJECT / KILL. Archive research.
   - **Score 23–27 PTS**: QUALIFIED OPPORTUNITY. Conduct 2–3 field customer interviews or operator shadowing sessions.
   - **Score 28–35 PTS**: TIER-1 GOLD PROBLEM. Proceed to Stages 7 and 8.

### Stage 7: Standardized Obsidian Discovery Log Dossier Generator
Format the complete findings into a structured Markdown research note using `assets/discovery-log-template.md`:
- Save note as `PROB-[DATE]-[SCORE]PTS-[ID].md` into `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/`.
- If external file-write is unavailable, emit complete markdown content for manual saving.

### Stage 8: 3-Tier Production Solution Wedge Derivation
For validated opportunities ($\ge 28$ PTS), derive a progressive 3-tier execution roadmap (see `references/solo-builder-micro-saas-strategy.md`):
- **Tier 1 (Free Client-Side Utility)**: Standalone Angular component or static web utility (browser-side CSV/PDF variance parser, SEO-ready, zero backend overhead, lead capture).
- **Tier 2 (Micro-Utility / Extension)**: Chrome Extension (Manifest V3) or CLI binary ($19–$49 one-time payment to test commercial willingness to pay).
- **Tier 3 (Production Micro-SaaS)**: Full-stack application (NestJS REST API + PostgreSQL Prisma ORM + Angular OnPush UI + Stripe recurring billing $49–$199/month).

---

## Gotchas & Market Validation Pitfalls

| Naive / Flawed Approach | Disciplined Evidence-Based Replacement | Why It Matters |
|---|---|---|
| Asking *"Would you buy this software if I built it?"* | *"Can you share your screen and show me how you handled this last week?"* | Hypotheticals yield 80%+ false positive validation; past behavior predicts actual payment. |
| Counting social media complaints as validation | Auditing economic workarounds (SOP spreadsheets, Zapier bills, VA invoices) | Free complaints represent emotional annoyance, not commercial willingness to pay. |
| Assuming a market is open without commercial search | Scanning competitor directories for tools $<\$50$/mo | Proposing solutions for workflows already commoditized by established tools wastes engineering time. |
| Inventing friction when research input lacks acute pain | Halting discovery with the Anti-Hallucination No-Problem fallback | Fabricating fake friction leads to building products nobody pays for. |
| Treating feature requests as customer problems | Asking "Why" repeatedly to uncover the underlying operational bottleneck | Users request local patches to visible symptoms rather than fundamental root causes. |
| Jumping immediately into multi-tenant SaaS architecture | Scaffolding Tier-1 Client Utility $\rightarrow$ Tier-2 Extension $\rightarrow$ Tier-3 SaaS | Progressive derivation mitigates engineering risk and builds distribution early. |
