---
description: "Enforces empirical evidence boundaries, dual-track prioritization, search dorking, multi-dimensional competitor audit, inaction analysis, and experiment gates for problem discovery."
trigger: model_decision
framework_version: "Universal / Agnostic"
last_verified_date: "2026-09-14"
---

# Universal Problem Discovery & Evidence Grounding Rules

## Description
Enforces empirical evidence boundaries, search dorking, alternative audits, dual-track prioritization (Commercial vs Free Utility), inaction analysis, and small experiment validation gates.

## Constraints

### 1. Evidence & Experiment Decision Flow
Problem discovery must strictly progress through the 7-stage evidence pipeline:
$$\textbf{Signal Found} \rightarrow \textbf{Problem Candidate} \rightarrow \textbf{Corroborated Problem} \rightarrow \textbf{Alternatives Checked} \rightarrow \textbf{Small Experiment} \rightarrow \textbf{Observed Outcome} \rightarrow \textbf{Build/Revise/Park}$$

At every stage, the agent MUST explicitly evaluate the **3 Core Inquiries**:
1. **What do we know?** (Verified facts, quotes, artifacts, and sources).
2. **What do we not know?** (Assumptions, habit change hurdles, technical risks).
3. **What must be verified next?** (The exact concrete test to remove ambiguity).

### 2. Evidence Quality Boundary & 5-Level Hard Gate
- AI-generated opportunity lists and un-evidenced assertions are PROHIBITED as market validation.
- Evidence MUST be categorized by the 5-Level Evidence Quality Ladder:
  1. **Level 1 (Primary Behavioral)**: Screen recordings, shadow Excel files, actual error logs, transaction receipts.
  2. **Level 2 (Primary Verbal)**: Verifiable, dated operator interview quotes with specific numbers and historical spend.
  3. **Level 3 (Independent Corroboration)**: $\ge 5$ unconnected reviews, forum threads, or raw JSON comment trees reporting the identical failure pattern.
  4. **Level 4 (Secondary Interpretation)**: Industry articles, market reports, analyst whitepapers.
  5. **Level 5 (Unvalidated Hypothesis)**: AI-generated lists, hypothetical survey polls, founder assumptions.
- **Data Format Invariant**: Forum comment trees extracted via `.json` URLs remain **Level 3 Corroborated Sentiment**, NOT Level 1 behavioral evidence.
- **Hard Gate**: Level 4–5 sources MUST NOT contribute to any dimension score above 1. Level 5 sources auto-score 0.
- **Unverified Input Rule**: Entering raw numbers without attached primary evidence artifacts results in `UNVERIFIED_INPUT / RESEARCH_PRIORITY`. The agent and scripts are STRICTLY FORBIDDEN from marking a candidate `VALIDATED` without verified primary evidence or experiment outcomes.

### 3. Dual-Track Prioritization Model
Candidates MUST be evaluated under the appropriate track:
- **Track A (Commercial / Micro-SaaS)**: Evaluates willingness to pay (WTP), recurring budget ($29–$199/mo), economic ROI, and single-buyer purchasing power.
- **Track B (Free Utility / Public Benefit / Local Community)**: Evaluates repeat utility frequency, time saved, accessibility, SEO/traffic or social impact, and zero-maintenance architecture. Zero WTP is expected and MUST NOT penalize non-monetized utilities.

### 4. 7-Dimension 35-Point Research Prioritization Matrix
Scores govern **Research Prioritization** (measure of research urgency, NOT validated market proof):

| Dimension | Track A: Commercial (0–5) | Track B: Free Utility (0–5) |
|---|---|---|
| **1. Frequency** | Rare (0) to Daily continuous (5) | Rare (0) to Daily continuous (5) |
| **2. Severity & Risk** | Cosmetic (0) to Direct fines/lost cash (5) | Trivial (0) to Major hours lost/fines (5) |
| **3. Workaround** | None (0) to Dedicated staff/macros (5) | None (0) to Notebook/WhatsApp groups (5) |
| **4. Track Dimension** | **WTP**: Expects free (0) to High ROI $200+/mo (5) | **Utility**: Curiosity (0) to Daily essential (5) |
| **5. Decision-Maker** | Enterprise RFP (0) to Self-serve card (5) | Bureaucracy (0) to 1-tap instant install (5) |
| **6. Solo Feasibility** | Hardware/AI (0) to Lean micro-tool (5) | Heavy backend (0) to Static client utility (5) |
| **7. Discrepancy** | Unified (0) to Acute handoff breakdown (5) | Unified (0) to Multi-party mismatch (5) |

*Separation of Concerns*: Technical implementation complexity (messy PDFs, hostile schemas) represents engineering risk, NOT opportunity strength. Score user pain and technical feasibility separately.

#### Triage Thresholds:
- **0–14 PTS**: **HALT / NO-PROBLEM FALLBACK**. Output anti-hallucination fallback.
- **15–22 PTS**: **LOW RESEARCH PRIORITY**. Archive data. Do not design solutions.
- **23–27 PTS**: **QUALIFIED RESEARCH CANDIDATE**. Conduct 2–3 field user shadow sessions.
- **28–35 PTS**: **HIGH RESEARCH PRIORITY**. Design and execute a low-cost trial experiment.

### 5. Multi-Dimensional Alternative Fit & Inaction Root Cause
Before advancing any candidate, perform a multi-dimensional alternative scan:
- **Stop Check #3 Refinement**: Do not blindly count competitor logos or pricing. Evaluate:
  1. *Exact workflow fit*: Does the tool solve the specific bottleneck, or is it bloated generic software?
  2. *Geography & Language*: Does it support local statutory compliance, vernacular language, and local currency?
  3. *Device & Connectivity*: Does it run offline on low-end mobile phones, or require desktop Chrome?
  4. *Switching friction*: Is migrating existing data prohibitively painful?
- **Non-Software Alternative Check**: If an Excel template, paper checklist, or WhatsApp SOP eliminates 80% of the pain at zero cost, **do not build custom software**.
- **Inaction Analysis**: If operators have no workaround, investigate why:
  - Abandoned because the issue is trivial $\longrightarrow$ **REJECT**.
  - Abandoned because available tools are unaffordable ($5,000+/yr) or inaccessible while consequences remain severe $\longrightarrow$ **LATENT HIGH-CONVICTION OPPORTUNITY**.

### 6. Local, Offline & Smallest Suitable Solution Mandates
- **Local & Offline Protocol**: For retail shops, godowns, or clinics, conduct physical "Counter Shadowing", observe physical registers/WhatsApp workflows, and enforce **Offline-First** local caching.
- **Smallest Suitable Solution**: SaaS progression is **NOT compulsory**. Select the leanest format that resolves the bottleneck:
  1. *Non-Software Template / SOP* (Stop here)
  2. *Static Client-Side Web Utility* (Standalone Angular/Vanilla JS, zero backend, client-side only)
  3. *CLI Automation Tool* (Standalone script/binary)
  4. *Browser Extension* (Manifest V3 DOM injection/export)
  5. *Full-Stack Micro-SaaS* (NestJS + Postgres + Stripe; only when multi-user/background sync strictly required)

### 7. Anti-Hallucination Fallback & Dossier Persistence
- If input lacks documented operational friction or scores $< 15$ PTS, return: `"Could not find an evidence-backed operational problem in the supplied domain input."`
- Dossiers MUST be saved under `/home/murali/Documents/obsidian-notes/01_Inbox/discovery_logs/PROB-[DATE]-[SCORE]PTS-[ID].md` and central matrix CSV synchronized in the same turn.

## Examples

### 1. Verified B2B Problem Candidate
- **Candidate**: Subcontractor Certificate of Insurance (COI) tracker.
- **Evidence**: Level 1 (8 contractor logs, $150/mo Zapier bill, fine receipt).
- **Classification**: HIGH RESEARCH PRIORITY (Score: 32 PTS, Track A).
- **Next Action**: Execute 7-day concierge trial verifying renewal response rate before scaffolding code.

### 2. Track B Free Utility Candidate
- **Candidate**: Tamil Nadu Ration Shop Stock & Token Helper.
- **Evidence**: Level 2 (Interviews with 12 village cardholders, physical token queue photo).
- **Classification**: HIGH RESEARCH PRIORITY (Score: 31 PTS, Track B: Free Utility).
- **Verdict**: Validated for zero-backend static web utility (Offline PWA + AdSense), bypassing WTP requirements.
