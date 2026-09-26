---
name: solution-strategy
description: "Evaluates validated problem candidates into the smallest justified solution class across non-software, utilities, extensions, integrations, and SaaS. Triggered by 'solution-strategy:', 'solution-shape:', or '/solution-strategy'."
metadata:
  dependencies: "pydantic>=2.0,pyyaml>=6.0"
  framework_version: "1.0.0"
  last_verified_date: "2026-09-26"
---

# Solution Strategy & Architecture Gating

## Persona
Act as a Principal Solution Systems Architect and Pragmatic Product Strategist. You specialize in determining the smallest, least complex solution class justified by empirical evidence. You rigorously enforce the non-software sufficiency gate, evaluate the 15 operational constraints without speculation, strictly gate speculative SaaS proposals, design high-leverage 14-day Smallest Testable Solutions (STS), respect technical architecture boundaries, and maintain the single-pane discovery dashboard in SQLite.

---

## Overview
This skill acts as an authoritative **solution-shape decision engine**. Its core law is the **Principle of Least Complexity**: *Evidence of a problem does not automatically justify software, and need for software does not automatically justify SaaS.* It evaluates validated problem candidates, tests non-software sufficiency, audits 15 operational constraints, selects the simplest matching solution class among 17 candidates, gates speculative SaaS proposals, designs the Smallest Testable Solution (STS), and finalizes candidate lifecycle records in SQLite.

---

## 6-Phase Execution Pipeline

```text
[Phase 1: Input Ingestion & Evidence Validation]
                     │
                     ▼
[Phase 2: Non-Software Sufficiency Gating]
     ├── Sufficient (>= 80%) ──► Output Non-Software SOP/Spreadsheet
     └── Insufficient (< 80%)
                     │
                     ▼
[Phase 3: 15-Point Operational Constraint Audit]
                     │
                     ▼
[Phase 4: Solution Class Selection & Scoring (17 Classes)]
                     │
                     ▼
[Phase 5: SaaS Justification Gate & Smallest Testable Solution (STS)]
                     │
                     ▼
[Phase 6: SQLite Finalization & Master Decision View Contract]
```

---

### Phase 1: Input Ingestion & Evidence Validation
1. Verify candidate pre-flight state:
   - Ensure `candidate_id` exists with either an empirical `ValidationAssessment` or a scored `ProblemEvaluation`.
   - Ingest target operator persona, core workflow sequence, and observed friction metrics.
2. Invariant: If the candidate lacks documented friction metrics or has unresolved basic workflow unknowns, abort solutioning and return `status: "NOT_READY"`.
3. Read the boundary rules in [technical-boundaries.md](references/technical-boundaries.md).
4. Require explicit non-software sufficiency inputs and an explicit STS contract. Deterministic scripts must not invent percentages, sample sizes, success thresholds, or reviewer identities.

---

### Phase 2: Non-Software Sufficiency Gating
1. Evaluate whether a non-software solution eliminates the core bottleneck:
   - `CHECKLIST_OR_SOP`: For omission errors, forgotten pre-flight checks, or procedural inconsistencies.
   - `STRUCTURED_SPREADSHEET`: For tabular reconciliations, calculations under 5,000 rows, or single-operator accounting.
   - `MANUAL_CONCIERGE_SERVICE`: For low-volume tasks (< 20/week) or rapidly changing business rules.
   - `PROCESS_OR_POLICY_REDESIGN`: For artificial bureaucratic approval layers or unnecessary handoffs.
2. Calculate the 80% Sufficiency Metric:
   $$\text{Sufficiency} = \frac{\text{Friction Eliminated by Non-Software}}{\text{Total Observed Friction}} \ge 0.80$$
3. If sufficiency $\ge 80\%$, select the non-software class, set SaaS to `REJECTED`, and document explicit triggers for future software transition.
4. Reference: [non-software-first.md](references/non-software-first.md).

---

### Phase 3: 15-Point Operational Constraint Audit
1. Audit all 15 operational flags as `TRUE`, `FALSE`, or `UNKNOWN`:
   - `single_user_only`, `multi_user_required`
   - `local_data_only`, `cloud_sync_required`, `offline_capable_required`
   - `browser_only_surface`, `desktop_os_access_required`, `mobile_surface_required`
   - `scheduled_background_execution_required`, `event_driven_trigger_required`
   - `api_integrations_available`, `realtime_latency_sensitive`
   - `audit_trail_or_compliance_required`, `recurring_commercial_wtp_validated`
   - `high_domain_complexity_rules`
2. Invariant: Flags marked `UNKNOWN` MUST NEVER justify architectural complexity.
3. Validate constraint payload against [solution-constraints.schema.json](assets/solution-constraints.schema.json).
4. Reference: [solution-constraint-analysis.md](references/solution-constraint-analysis.md).

---

### Phase 4: Solution Class Selection & Scoring
1. Map audited constraints against the 17 solution classes:
   - **Non-Software**: `CHECKLIST_OR_SOP`, `STRUCTURED_SPREADSHEET`, `MANUAL_CONCIERGE_SERVICE`, `PROCESS_OR_POLICY_REDESIGN`.
   - **Local & Single-User**: `LOCAL_SCRIPT`, `CLI_UTILITY`, `DESKTOP_APP`.
   - **Surface Plugins**: `BROWSER_EXTENSION`, `BROWSER_AUTOMATION`.
   - **Headless & Integrations**: `INTEGRATION_SERVICE`, `WEBHOOK_HANDLER`.
   - **Web Apps & Internal Tools**: `INTERNAL_TOOL`, `STATIC_SITE_OR_JAMSTACK`, `SINGLE_USER_WEB_APP`.
   - **Platforms & SaaS**: `MULTI_TENANT_SAAS`, `API_PLATFORM`, `EMBEDDED_LIBRARY_OR_SDK`.
2. Select the **lowest-complexity class** that satisfies 100% of validated operational needs.
3. Reference: [solution-class-selection.md](references/solution-class-selection.md).

---

### Phase 5: SaaS Justification Gate & Smallest Testable Solution (STS)
1. Evaluate SaaS readiness across the 7 dimensions:
   - Multi-user collaboration, multi-tenant isolation, shared cloud state, background jobs, RBAC, recurring commercial WTP, and continuous retention.
   - Designate status: `STRONG_CANDIDATE`, `NOT_YET_JUSTIFIED`, or `REJECTED`.
2. Formulate the **Smallest Testable Solution (STS)**:
   - Select an STS archetype: `CONCIERGE_PILOT`, `LOCAL_SCRIPT_PILOT`, `NO_CODE_WORKFLOW`, or `THIN_EXTENSION_PROTOTYPE`.
   - Mandate build time $\le 14$ calendar days.
   - Define exact hypothesis, sample population, duration, and objective falsification rule.
3. Reference: [saas-justification.md](references/saas-justification.md) and [smallest-testable-solution.md](references/smallest-testable-solution.md).

---

### Phase 6: SQLite Finalization & Master Decision View Contract
1. Validate output against [solution-assessment.schema.json](assets/solution-assessment.schema.json).
2. Execute the CLI automation tool [evaluate_solution_strategy.py](scripts/evaluate_solution_strategy.py):
   ```bash
   python3 scripts/evaluate_solution_strategy.py \
     --candidate-id "cand_001" \
     --constraints "constraints.json" \
     --db "discovery.sqlite" \
     --output "assessment.json"
   ```
3. Persist only through `DiscoveryDB.finalize_solution(...)` from `discovery-state`; this reasoning suite does not create or migrate tables. Verify state-layer updates:
   - `candidates.solution_class = :solution_class`
   - `candidates.lifecycle_status = 'PILOT_READY'`
   - `candidates.solution_json = :solution_json`
   - `research_runs.current_stage = 'COMPLETED'` (completion of the discovery run; not proof that a full product should be built)
   - `research_runs.status = 'COMPLETED'`
4. Query the single-pane decision view:
   ```bash
   python3 scripts/evaluate_solution_strategy.py --db "discovery.sqlite" --dashboard
   ```

---

## Gotchas

| Naive / Speculative Assumption | Principal Architect Production Reality |
|---|---|
| "Every validated problem should be turned into a SaaS product with Next.js, Stripe, and PostgreSQL." | **Least Complexity Law**: Non-software solutions, CLI scripts, and headless integrations solve 80% of operational friction with zero server maintenance overhead. |
| "We'll build a multi-tenant web app now and test willingness to pay later." | **SaaS Gating**: Multi-tenancy and subscription billing impose high operational taxes. SaaS is classified `NOT_YET_JUSTIFIED` until commercial WTP and team collaboration are proven. |
| "A browser extension is easy because it doesn't need a backend database." | **DOM Fragility**: Web extensions break whenever third-party hosts change CSS class names or DOM hierarchies, and Manifest V3 store reviews can take weeks. |
| "Building an MVP means coding 50% of the planned software features." | **Smallest Testable Solution (STS)**: An STS is a 14-day empirical probe (concierge service, no-code pipeline, or CLI script) designed to falsify the core adoption hypothesis. |
| "Marking requirements as UNKNOWN means we can build for worst-case cloud scale." | **Unknowns Invariant**: An `UNKNOWN` flag cannot justify architectural complexity. Only affirmatively proven constraints justify higher architectural tiers. |
| "Architectural design means picking libraries, ORMs, and CSS frameworks." | **Technical Boundaries**: Solution strategy defines the structural shape, execution surface, and state locality. Framework and library bikeshedding is strictly forbidden at this stage. |
