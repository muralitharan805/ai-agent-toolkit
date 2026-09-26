# Field Semantics & Data Dictionary Reference

## Purpose
This document provides the authoritative data dictionary, value ranges, enum specifications, and semantics for all columns in the discovery persistence store.

---

## 1. `research_runs` Data Dictionary

| Column | Type | Nullable | Valid Values / Constraints | Semantic Purpose |
|---|---|---|---|---|
| `research_id` | `TEXT` | NO | `^run_[a-z0-9_]+$` (PK) | Canonical identifier for the exploration run. |
| `original_request` | `TEXT` | NO | Non-empty string | Raw user prompt or business inquiry triggering the run. |
| `domain` | `TEXT` | NO | e.g. `ecommerce_logistics` | Normalised domain slug. |
| `scope_type` | `TEXT` | NO | `'BROAD'`, `'NARROW'`, `'MESSY_BRAINDUMP'` | Ingested exploration scope category. |
| `geography` | `TEXT` | YES | ISO country code or regional slug | Target geographical boundary. |
| `current_stage` | `TEXT` | NO | `'PLANNED'`, `'RESEARCHED'`, `'EVALUATED'`, `'VALIDATED'`, `'COMPLETED'` | Current pipeline phase of the run. |
| `status` | `TEXT` | NO | `'ACTIVE'`, `'COMPLETED'`, `'ARCHIVED'` | Administrative state. |
| `plan_json` | `TEXT` | YES | Valid JSON (`ResearchPlan`) | Snapshot of generated streams and unknowns. |

---

## 2. `candidates` Data Dictionary

| Column | Type | Nullable | Valid Values / Constraints | Semantic Purpose |
|---|---|---|---|---|
| `candidate_id` | `TEXT` | NO | `^cand_[a-z0-9_]+$` (PK) | Canonical identifier for the problem candidate. |
| `research_id` | `TEXT` | NO | FK to `research_runs` | Parent research run that spawned this candidate. |
| `title` | `TEXT` | NO | 5–150 characters | Descriptive problem candidate title. |
| `domain` | `TEXT` | NO | Matching parent domain | Domain taxonomy classification. |
| `target_operator` | `TEXT` | YES | Role slug (e.g. `accounts_manager`) | Specific human operator experiencing the friction. |
| `track` | `TEXT` | NO | `'COMMERCIAL'`, `'FREE_UTILITY'` | SeyaliCraft monetization or utility track. |
| `research_score` | `INTEGER` | NO | `0` to `35` | 35-point empirical research score. |
| `evidence_level` | `TEXT` | NO | `'L1'`, `'L2'`, `'L3'`, `'L4'`, `'L5'`, `'UNASSESSED'` | Dominant evidence level backing the candidate. |
| `validation_status` | `TEXT` | NO | `'UNVERIFIED'`, `'VALIDATED'`, `'EXPERIMENT_FAILED'` | Empirical proof state from real-world trials. |
| `lifecycle_status` | `TEXT` | NO | `'ACTIVE'`, `'RESEARCH_PRIORITY'`, `'EXPERIMENT_DESIGNED'`, `'PARKED'`, `'ARCHIVED'`, `'READY_TO_BUILD'` | Operational readiness in builder backlog. |
| `solution_class` | `TEXT` | YES | 17 Solution Classes | Architecture class assigned by solution strategy. |
| `evaluation_json` | `TEXT` | YES | Valid JSON (`ProblemEvaluation`) | Forensic 14-node map, root cause, and 35-pt scores. |
| `solution_json` | `TEXT` | YES | Valid JSON (`SolutionAssessment`) | 15-flag constraints, SaaS justification, and STS. |

### Evidence Levels (L1–L5 Hierarchy)
- **`L1` (Regulatory / Official Standards)**: Official framework specs, government compliance statutes, RFCs.
- **`L2` (Vendor Documentation / Primary API Spec)**: Official vendor documentation, platform limits, changelogs.
- **`L3` (Practitioner Direct Observation)**: Verbatim quotes from operators on Reddit, GitHub, forums, or user interviews.
- **`L4` (Secondary Analysis)**: Practitioner blog posts, industry whitepapers, community discussions.
- **`L5` (Speculative / Unverified)**: Marketing claims, hypothetical opinions without operational evidence.

---

## 3. `evidence_signals` Data Dictionary

| Column | Type | Nullable | Valid Values / Constraints | Semantic Purpose |
|---|---|---|---|---|
| `signal_id` | `TEXT` | NO | `^sig_[a-z0-9_]+$` (PK) | Canonical signal identifier. |
| `research_id` | `TEXT` | NO | FK to `research_runs` | Research run during which the signal was collected. |
| `candidate_id` | `TEXT` | YES | Nullable FK to `candidates` | Candidate this signal supports (linked in Stage 3). |
| `stream_id` | `TEXT` | YES | e.g. `RS-001` | Query stream from `ResearchPlan`. |
| `platform` | `TEXT` | NO | `'REDDIT'`, `'HACKERNEWS'`, `'GITHUB'`, `'FORUM'`, `'INTERVIEW'` | Source platform classification. |
| `source_url` | `TEXT` | YES | Valid HTTP/HTTPS URI | Traceable permalink to the original source. |
| `actor_role` | `TEXT` | YES | Role title | Self-identified persona of author. |
| `reported_issue` | `TEXT` | NO | Verbatim text | Exact observed friction or complaint. |
| `reported_workaround`| `TEXT` | YES | Text description | Current manual glue work (e.g. Excel). |
| `evidence_level` | `TEXT` | NO | `'L1'` to `'L5'` | Epistemic rigor classification. |
| `payload_json` | `TEXT` | YES | Valid JSON | Full raw metadata from adapter. |

---

## 4. `experiments` Data Dictionary

| Column | Type | Nullable | Valid Values / Constraints | Semantic Purpose |
|---|---|---|---|---|
| `experiment_id` | `TEXT` | NO | `^exp_[a-z0-9_]+$` (PK) | Canonical experiment identifier. |
| `candidate_id` | `TEXT` | NO | FK to `candidates` | Target candidate being empirically tested. |
| `hypothesis` | `TEXT` | NO | Falsifiable statement | Immutable claim being evaluated. |
| `metric_name` | `TEXT` | NO | e.g. `csv_uploads` | Single primary observable metric. |
| `target_threshold` | `REAL` | NO | Numeric target | Pre-registered pass/fail boundary. |
| `direction` | `TEXT` | NO | `'>='`, `'<='`, `'>'`, `'<'`, `'=='` | Comparison operator for success. |
| `sample_target` | `INTEGER` | NO | $\ge 1$ | Target participant count. |
| `sample_achieved` | `INTEGER` | YES | $\ge 0$ | Actual usable participants observed. |
| `observed_value` | `REAL` | YES | Measured value | Final metric observed during trial. |
| `outcome_verdict` | `TEXT` | NO | `'NOT_RUN'`, `'VALIDATED'`, `'EXPERIMENT_FAILED'`, `'INCOMPLETE'` | Objective trial verdict. |
| `artifact_hash` | `TEXT` | YES | 64-char Hex string | SHA-256 byte digest of raw trial CSV/log. |
| `audited_by` | `TEXT` | YES | Verifiable name | Named human reviewer. |
| `audit_date` | `DATE` | YES | ISO-8601 date | Date human review was performed. |
