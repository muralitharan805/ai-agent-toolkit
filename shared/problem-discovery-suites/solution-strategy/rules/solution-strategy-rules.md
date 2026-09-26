---
description: "Enforces non-software sufficiency gating, 15-point constraint auditing, solution class selection, SaaS justification gates, and SQLite lifecycle completion."
trigger: model_decision
framework_version: "1.0.0"
last_verified_date: "2026-09-26"
---

# Solution Strategy & Architecture Gating Rules

## Description
This rule governs the Solution Strategy stage of the problem discovery lifecycle. It enforces the foundational principle of least complexity: problem evidence does not automatically justify software, and software need does not automatically justify SaaS. It mandates rigorous non-software sufficiency evaluations, an evidence-based 15-point operational constraint audit, strict gating for SaaS candidates, prioritization of the Smallest Testable Solution (STS), adherence to architectural boundaries without low-level stack hallucination, and the final SQLite candidate persistence and `v_discovery_dashboard` contract.

## Constraints

### 1. The Least Complexity Invariant
- The agent MUST select the simplest, lowest-friction solution class that completely satisfies the validated evidence.
- The default presumption is always:
  1. Non-Software (SOP, Checklist, Spreadsheet, Process Redesign)
  2. Local / Single-User Utility (CLI Script, Batch Automation, Local Utility)
  3. Surface Plugin / Extension (Browser Extension, Workspace Add-on)
  4. Integration Service (Headless Webhook, API Sync Service)
  5. Internal Tool / Standalone Web App
  6. Multi-Tenant SaaS (strictly last resort, requiring affirmative proof)
- Choosing a higher-complexity tier when a lower-complexity tier suffices is STRICTLY FORBIDDEN.

### 2. Non-Software Sufficiency Gate
- Before entertaining any software design, the agent MUST evaluate whether non-software interventions resolve the core friction:
  - `CHECKLIST_OR_SOP`: When errors are caused by inconsistent human execution or forgotten procedural steps.
  - `STRUCTURED_SPREADSHEET`: When data volume is low (< 5,000 rows), single-user, and calculations are standard tabular logic.
  - `MANUAL_CONCIERGE_SERVICE`: When operational volume is low or process rules are rapidly evolving.
  - `PROCESS_OR_POLICY_REDESIGN`: When friction stems from redundant approvals, misaligned handoffs, or unnecessary steps.
- If a non-software intervention resolves $\ge 80\%$ of the observed friction, the software path MUST be deferred or rejected.

### 3. The 15-Point Operational Constraint Audit
- Every solution assessment MUST explicitly evaluate the 15 operational flags:
  1. `single_user_only`
  2. `multi_user_required`
  3. `local_data_only`
  4. `cloud_sync_required`
  5. `offline_capable_required`
  6. `browser_only_surface`
  7. `desktop_os_access_required`
  8. `mobile_surface_required`
  9. `scheduled_background_execution_required`
  10. `event_driven_trigger_required`
  11. `api_integrations_available`
  12. `realtime_latency_sensitive`
  13. `audit_trail_or_compliance_required`
  14. `recurring_commercial_wtp_validated`
  15. `high_domain_complexity_rules`
- Each flag MUST be evaluated strictly as `TRUE`, `FALSE`, or `UNKNOWN`.
- Flags marked `UNKNOWN` MUST NEVER be treated as affirmative justification for complex architectural tiers.

### 4. SaaS Justification Gate
- A solution class of `SAAS_APPLICATION` or `MULTI_TENANT_SERVICE` is strictly gated and MUST NOT be assigned speculative validity.
- SaaS classification MUST be assigned exactly one of three states:
  - `STRONG_CANDIDATE`: Multi-user collaboration, persistent cloud state, background jobs, role-based access, and recurring commercial willingness to pay (WTP) are empirically verified.
  - `NOT_YET_JUSTIFIED`: The problem is validated, but multi-user collaboration, cross-tenant data sharing, or recurring commercial monetization remain unproven or unknown.
  - `REJECTED`: Single-user, local-only, or non-software interventions completely satisfy the operational need.
- Claiming SaaS status when `multi_user_required` or `cloud_sync_required` is `UNKNOWN` is STRICTLY PROHIBITED.

### 5. Smallest Testable Solution (STS) Priority
- The agent MUST differentiate between the "Ultimate Architectural Destination" and the "Smallest Testable Solution (STS)".
- Every assessment MUST define an immediate, low-risk STS (pilot intervention, script, concierge workflow, or prototype) designed to test the critical remaining hypothesis in $< 2$ weeks.
- The STS definition MUST include:
  - `intervention_type`: The concrete operational pilot (e.g. Concierge, Script, Spreadsheet).
  - `falsification_metric`: Objective metric that determines if the STS succeeded or failed.
  - `estimated_build_days`: Realistic turnaround time ($\le 14$ days).

### 6. Technical Architecture Boundaries
- The agent MUST define the *solution class*, *distribution surface*, and *operational profile*.
- The agent is STRICTLY FORBIDDEN from hallucinating:
  - Specific UI frameworks (e.g., Next.js, Angular, React) unless mandated by consumer environment constraints.
  - Specific databases (e.g., PostgreSQL, MongoDB) or ORMs without explicit scale or data structure requirements.
  - Pricing models, subscription tiers, or marketing slogans without empirical business validation.
- Architectural guidance must remain at the structural systems level (e.g., "Stateless worker with persistent queue and webhook endpoint", NOT "Node.js Express on AWS ECS with Redis").

### 7. SQLite Finalization & Master Decision View Contract
- When an assessment is finalized, the agent MUST persist the results to SQLite:
  - **Candidates Table**: Update `solution_class`, set `lifecycle_status = 'READY_TO_BUILD'`, and store structured `solution_json`.
  - **Research Runs Table**: Set parent run `current_stage = 'COMPLETED'` and `status = 'COMPLETED'`.
  - **Master Decision View**: Ensure `v_discovery_dashboard` exists, joining `candidates`, `evidence_signals`, and `experiments` to provide a single-pane-of-glass overview.
- Mutations MUST be executed within an explicit atomic transaction.

## Examples

### 1. Correct Non-Software Sufficiency Gating
```text
Candidate: "E-commerce invoice total reconciliation mismatches"
Constraint Audit:
- single_user_only: TRUE
- local_data_only: TRUE
- cloud_sync_required: FALSE
- scheduled_background_execution_required: FALSE
Evaluation:
Non-Software Sufficiency: PASS (CHECKLIST_OR_SOP + Excel reconciliation template).
Decision: Reject custom SaaS application. Recommended: Standardized reconciliation template with validation formulas.
STS: 5-operator pilot with Excel template over 10 business days.
```

### 2. Forbidden Speculative SaaS Escalation
```text
❌ FORBIDDEN:
"Problem is slow CSV parsing for HR managers. We will build a multi-tenant microservices SaaS platform with Next.js, Stripe subscriptions, and PostgreSQL."
(Violates Least Complexity: Single-user local script or desktop utility was never considered; SaaS was assumed without multi-user or commercial validation).

✅ CORRECT:
"Constraint audit indicates single_user_only = TRUE, local_data_only = TRUE, recurring_commercial_wtp_validated = UNKNOWN.
Solution Class: LOCAL_SCRIPT / CLI_UTILITY.
SaaS Justification: NOT_YET_JUSTIFIED.
STS: Standalone Python script running locally on HR desktop."
```
