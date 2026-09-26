---
description: "Enforces evidence-based problem evaluation boundaries, signal clustering rules, 14-node workflow completeness, and SQLite candidate persistence contracts."
trigger: model_decision
framework_version: "1.0.0"
last_verified_date: "2026-09-26"
---

# Problem Evaluation & Evidence Interpretation Rules

## Description
This rule governs the Problem Evaluation stage across the discovery lifecycle. It enforces strict epistemic interpretation of empirical evidence: transforming structured `ResearchSignals` into distinct, bounded problem candidates, mapping forensic workflows across 14 operational nodes, separating observable symptoms from root causes, auditing alternative workflow fit, applying evidence-gated 35-point scoring, and managing candidate persistence in SQLite. It strictly forbids executing live web searches, inventing missing workflow details, ignoring contradictory evidence, and confusing research prioritization scores with validated market demand.

## Constraints

### 1. Scope Boundary & No Fresh Research Invariant
- The Problem Evaluation agent is strictly an **evidence interpretation engine**; it MUST NOT perform fresh internet searches, query live search APIs, fetch external web pages, or contact human subjects.
- If critical evidence is missing (e.g. unknown frequency, unverified impact, uninspected alternative), the agent MUST generate structured `research_requests` and pass them back to the orchestrator for `evidence-research`.
- The agent MUST NOT recommend final software architecture, design UI wireframes, determine commercial pricing, or write to `discovery_matrix.csv`.

### 2. Signal Clustering & Anti-Inflation Rules
- Research signals MUST be clustered into problem candidates by matching:
  `[Specific Actor] + [Specific Trigger] + [Operational Task] + [Core Mechanism Failure]`
- The agent MUST NOT merge signals into a single candidate solely because:
  - They share generic industry keywords (e.g. "inventory" or "shipping").
  - They mention the same software product (e.g. "Shopify").
  - They belong to the same high-level research stream.
- The agent MUST NOT split a single underlying problem into multiple candidates merely because different sources use distinct wording or complain about different downstream symptoms.
- When clustering confidence is low, the agent MUST flag the candidate as `POSSIBLE_DUPLICATE` and request additional operator evidence.

### 3. Forensic 14-Node Workflow Completeness
- Every candidate problem MUST map the operational sequence across all 14 forensic nodes:
  1. `actor`, 2. `trigger`, 3. `input`, 4. `steps`, 5. `tools`, 6. `decisions`,
  7. `handoffs`, 8. `delays`, 9. `rework`, 10. `errors`, 11. `output`, 12. `cost`,
  13. `risk`, 14. `audit`.
- **Zero Hallucination Invariant**: Any node lacking direct supporting evidence in the input `ResearchSignals` MUST be explicitly recorded as `UNKNOWN`. Inventing plausible steps, costs, or tools to complete the schema is STRICTLY FORBIDDEN.

### 4. Epistemic Separation: Symptom vs. Workaround vs. Root Cause
- The agent MUST rigorously separate operational elements:
  - `Reported Symptom`: The observable pain point or complaint (e.g., "manual inventory updates take hours").
  - `Reported Workaround`: The interim patchwork maintained by the operator (e.g., "exporting CSV to Google Sheets").
  - `Known Cause`: Direct operational mechanism verified by primary evidence.
  - `Root Cause`: Suspected underlying architectural or institutional failure.
- A reported workaround MUST NEVER be classified as a root cause. Root causes without primary operational proof MUST remain marked as `UNVERIFIED` hypotheses.

### 5. Contradictory Evidence Preservation Invariant
- Evidence that contradicts, limits, or disproves a problem candidate MUST NEVER be omitted or discarded to improve a candidate's score.
- The agent MUST separate `supporting_signal_ids` from `contradicting_signal_ids` in every candidate record.
- If some operators report severe friction while others report existing tools work adequately, the agent MUST document the discrepancy as a segment-specific friction rather than claiming universal pain.

### 6. Alternative Assessment & Workflow Fit Standard
- The presence of an existing commercial tool does NOT prove a problem is solved. The agent MUST evaluate **Workflow Fit**:
  - Does the tool support the target operator's specific scale, language, and geography?
  - Does it eliminate the reported manual workaround?
  - Are adoption barriers (cost, complexity, API permissions) preventing use?
- Conversely, a candidate MUST NOT be promoted if evidence shows an existing free or commercial alternative already solves the exact workflow well. In this case, the `stop_checks` MUST be triggered.

### 7. Evidence-Gated 35-Point Scoring Integrity
- Scoring MUST follow the 7-dimension model (0–5 points each, 35 max):
  1. `frequency`, 2. `severity`, 3. `workaround`, 4. `wtp` (or utility adoption),
  5. `decision_maker`, 6. `feasibility`, 7. `discrepancy`.
- The score represents **Research Prioritization**, NEVER market demand validation.
- Scoring caps MUST be enforced based on the highest verified evidence level:
  - `L1` (Primary system/financial records): Eligible for $\ge 28$ PTS.
  - `L2` (Direct practitioner interview): Eligible for up to 28 PTS.
  - `L3` (Public community post): Capped at 20 PTS.
  - `L4/L5` (Marketing or opinion): Capped at 15 PTS.
- If evidence sufficiency is `INSUFFICIENT`, the agent MUST set `research_score: null` with status `INSUFFICIENT_EVIDENCE`. Fabricating numeric scores without supporting evidence is STRICTLY PROHIBITED.

### 8. SQLite Candidate Persistence & Soft-Delete Invariant
- Finalized candidates MUST be inserted into SQLite table `candidates`:
  - `candidate_id`: Sequential token `CAND-NNN`.
  - `research_id`: Parent run foreign key.
  - `lifecycle_status`: Initialized to `ACTIVE`, `RESEARCH_PRIORITY`, or `PARKED`.
- Link all underlying evidence signals by updating `evidence_signals`:
  ```sql
  UPDATE evidence_signals 
  SET candidate_id = :candidate_id 
  WHERE signal_id IN (:supporting_signal_ids);
  ```
- Update parent run stage to `EVALUATED`:
  ```sql
  UPDATE research_runs 
  SET current_stage = 'EVALUATED', updated_at = CURRENT_TIMESTAMP 
  WHERE research_id = :research_id;
  ```
- **Soft-Delete Invariant**: If a candidate triggers stop checks or proves non-viable, it MUST be set to `lifecycle_status = 'PARKED'` or `'ARCHIVED'`. Deleting records from SQLite is STRICTLY FORBIDDEN.

## Examples

### 1. Signal Clustering vs. Keyword Merging
```text
❌ FORBIDDEN (Merging disparate workflows by keyword):
Signal A: "Shopify seller struggles with checkout tax calculation."
Signal B: "Shopify seller manually prints thermal labels."
Agent Action: Merges into single candidate: "Shopify store operations."

✅ CORRECT (Workflow-specific clustering):
Signal A: Target workflow is Checkout Tax Compliance.
Signal B: Target workflow is Fulfillment Label Dispatch.
Agent Action: Forms two distinct candidates (PC-001: Checkout Tax Calculation, PC-002: Batch Shipping Labels) with dedicated 14-node workflows.
```

### 2. Evidence-Gated Score Capping
```text
❌ FORBIDDEN (Uncapped scoring on forum hearsay):
Signals: 2 Reddit posts where anonymous users complain about software.
Agent Output:
- Frequency: 5/5, Severity: 5/5, WTP: 5/5 -> Total Score: 33/35 (READY_TO_BUILD)
- Claim: Validated high-priority SaaS opportunity.

✅ CORRECT (Strict L3 score cap & gap detection):
Signals: 2 Reddit posts where anonymous users complain about software.
Agent Output:
- Evidence Level: L3 (Public Community Complaint)
- Score Status: Capped at maximum 20 PTS.
- Validation Status: UNVERIFIED.
- Unknowns: Measured financial impact, willingness to pay, verified frequency.
- Research Request: Generate RR-001 targeting direct operator interviews.
```
