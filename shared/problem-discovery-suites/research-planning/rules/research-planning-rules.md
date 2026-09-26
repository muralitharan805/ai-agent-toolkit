---
description: "Enforces strict research planning boundaries, epistemic provenance preservation, non-negotiable unknowns labeling, and SQLite run initialization contracts."
trigger: model_decision
framework_version: "1.0.0"
last_verified_date: "2026-09-26"
---

# Research Planning & Epistemic Scoping Rules

## Description
This rule governs the Research Planning phase across all problem discovery and market investigation initiatives. It enforces strict epistemic discipline: converting raw, unstructured, broad, or messy user requests into an actionable, traceable, and versioned `ResearchPlan`. It mandates the separation of planning from live search execution and market validation, establishes non-negotiable provenance preservation, forbids silent geographical or demographic assumptions, prevents premature solution anchoring, and governs the SQLite `research_runs` lifecycle initialization.

## Constraints

### 1. Scope Isolation & Strict No-Validation Boundary
- The Research Planning agent MUST ONLY plan research; it is STRICTLY FORBIDDEN from executing live web/API searches, fetching external signals, evaluating problem validity, scoring market viability, or designing solutions.
- The planner MUST NOT assign candidate problem IDs (`PRB-xxx`), calculate 35-point research scores, or write records into `discovery_matrix.csv`.
- A status of `READY` in a `ResearchPlan` indicates solely that the research strategy is structurally complete and executable by downstream search agents—NOT that a problem is verified, validated, or commercially viable.

### 2. Epistemic Provenance & Quad-Classification
- Every asserted claim, task, constraint, and friction MUST be categorized into one of four distinct epistemic states:
  1. `EXPLICIT_REPORTED`: Stated directly by the user. Must preserve exact source attribution (e.g., "user firsthand observation", "secondhand colleague report", "customer quote").
  2. `INFERRED`: Logically deduced by the agent based on established domain workflows, explicitly marked as model inference.
  3. `HYPOTHESIS`: An unverified assumption, suspected bottleneck, or potential friction requiring empirical testing.
  4. `UNKNOWN`: Information not supplied and not safely inferable from primary evidence.
- Stripping attribution qualifiers (e.g. converting "my friend claimed delays occur daily" into a verified fact of "daily production delays") is STRICTLY PROHIBITED.
- User complaints, frustrations, and sentiment MUST remain classified as unverified behavioral signals, never objective facts.

### 3. Absolute Prohibition of Silent Defaults
- When critical context (e.g., target geography, operating jurisdiction, target company size, regulatory framework) is omitted from the request, the agent MUST explicitly record it as `UNKNOWN` (or `null`).
- Silently defaulting to arbitrary locations (e.g., defaulting to India, the United States, or local regions without explicit user confirmation) is STRICTLY FORBIDDEN.
- Missing geography must remain an explicit unknown unless the user prompt contains unambiguous geographic anchors (e.g., currency, state law, regional agency).

### 4. Solution Independence & Anti-Anchoring
- When a user request expresses a desired solution type (e.g., "Find SaaS ideas for logistics", "Build a micro-tool for invoice reconciliation"), the agent MUST categorize the software form factor as a user-stated preference, NOT as proof that software is necessary.
- Research questions MUST focus on frontline tasks, handoffs, existing manual workarounds (spreadsheets, paper registers, WhatsApp groups), and operational costs before investigating software alternatives.
- The agent MUST NOT anchor research queries purely to software products; it must include queries targeting non-software workarounds, manual glue-work, and standard operating procedures (SOPs).

### 5. Domain, Actor & Workflow Decomposition
- Broad requests MUST be decomposed hierarchically: `Actor -> Task -> Workflow`.
- Operational coverage MUST be audited against the 5 Adaptive Operational Lenses:
  1. Frontline / Intake (data entry, physical reception, customer initiation)
  2. Multi-party Handoffs (cross-department, vendor-to-client, field-to-office)
  3. Back-office Reconciliation (audit, invoice matching, spreadsheet sync)
  4. Regulatory / Portal Workflows (statutory reporting, compliance filing, license renewals)
  5. Exceptions / Disputes (chargebacks, rework, returns, error escalations)
- The 5 lenses are diagnostic coverage tools, NOT mandatory quotas. Narrow requests MUST remain bounded to the specific workflow requested without artificial expansion.

### 6. Atomic Search Unit Standard
- Every search query generated in the plan MUST follow the Atomic Search Unit formulation:
  `[Specific Actor] + [Specific Task] + [Known or Hypothesized Workaround/Friction] + [Observable Consequence]`
- Search queries MUST be allocated across the 5 Search-Source Categories:
  1. Community & Practitioner Discussions (`reddit.com`, `news.ycombinator.com`, specialized forums)
  2. Public Filetypes & Operational Artifacts (`filetype:xlsx`, `filetype:pdf` SOPs, templates)
  3. Job Postings Hunting Human Glue-Work (`linkedin.com/jobs`, `indeed.com`, `naukri.com`)
  4. Software Gaps & Negative Reviews (`g2.com`, `capterra.com`, GitHub issue trackers)
  5. Regional Regulatory Gazettes & Public Grievances (statutory portals, consumer complaints)

### 7. SQLite Lifecycle & Claim-Check Contract
- Every finalized `ResearchPlan` MUST initiate a parent record in SQLite table `research_runs`:
  - `research_id`: Sequential identifier format `RUN-YYYY-NNN` (e.g., `RUN-2026-001`).
  - `original_request`: Exact unmodified user prompt.
  - `domain`: Normalized domain key (e.g., `ecommerce_logistics`).
  - `scope_type`: `BROAD`, `NARROW`, `MESSY_BRAINDUMP`, or `MULTI_DOMAIN`.
  - `geography`: String name or `NULL`.
  - `current_stage`: Initialized to `PLANNED`.
  - `status`: Initialized to `ACTIVE`.
  - `plan_json`: Canonical JSON string conforming to `research-plan.schema.json`.
- The downstream `evidence-research` agent MUST receive only the `research_id` claim-check token.

## Examples

### 1. Epistemic Labeling & Geography Guard
```text
❌ FORBIDDEN (Silent default & erased attribution):
User: "A friend told me customs clearance takes 4 days."
Agent Plan:
- Geography: India (Defaulted)
- Verified Fact: Customs clearance takes 4 days.
- Target Solution: SaaS automated clearance platform.

✅ CORRECT (Strict epistemic classification & explicit unknowns):
User: "A friend told me customs clearance takes 4 days."
Agent Plan:
- Geography: UNKNOWN (Source: OMITTED_BY_USER)
- Friction Hypothesis: Secondhand report that customs clearance experiences 4-day latency.
- Status: UNVERIFIED (Reported by peer, requires primary bill-of-entry audit).
- Research Questions:
  1. What documented statutory milestones exist in the target jurisdiction?
  2. What manual workarounds or paper filings are maintained by customs brokers?
```

### 2. User Solution Anchoring vs. Workflow Discovery
```text
❌ FORBIDDEN (Premature software anchoring):
User: "I want to build an AI SaaS for gym owners."
Agent Strategy:
- Search Queries: "best AI SaaS for gyms", "gym management SaaS features"
- Assumption: Boutique gyms need an AI SaaS application.

✅ CORRECT (Workflow-first decomposition):
User: "I want to build an AI SaaS for gym owners."
Agent Strategy:
- User Solution Preference: Stated preference for AI SaaS (not validated).
- Actor: Boutique gym owner / studio manager.
- Target Workflows: Class scheduling, trainer payouts, member churn intake.
- Operational Lens: Back-office Reconciliation & Exceptions/Disputes.
- Search Queries:
  1. site:reddit.com/r/gymowners "trainer payout" "spreadsheet" "error"
  2. filetype:xlsx "gym schedule template" "reconciliation"
  3. site:g2.com "Mindbody" "too expensive" OR "clunky"
```
