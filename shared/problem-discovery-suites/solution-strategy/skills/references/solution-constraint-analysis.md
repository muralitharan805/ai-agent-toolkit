# Solution Constraint Analysis Reference

## Purpose
This document provides the authoritative specification for auditing the 15 operational constraints during the Solution Strategy evaluation. Every constraint determines the physical boundaries, deployment models, and technical complexity justified by empirical evidence.

---

## The 15 Operational Constraints

| # | Constraint Key | Type | Description | Positive Evidence Trigger | Default if Unproven |
|---|---|---|---|---|---|
| 1 | `single_user_only` | `BOOLEAN / UNKNOWN` | The workflow is executed by an isolated operator with no collaborative handoffs. | Direct observation of solo operator without handoffs or shared state. | `UNKNOWN` |
| 2 | `multi_user_required` | `BOOLEAN / UNKNOWN` | The workflow requires real-time or asynchronous collaboration, approval handoffs, or shared visibility across multiple operators. | Observed handoffs, team queues, or multi-party review steps. | `UNKNOWN` |
| 3 | `local_data_only` | `BOOLEAN / UNKNOWN` | Data operates strictly on local disk/memory without needing cloud persistence or sharing. | Filesystem operations, local SQLite, strictly confidential files. | `UNKNOWN` |
| 4 | `cloud_sync_required` | `BOOLEAN / UNKNOWN` | State must be accessible across multiple devices, external services, or geographical locations. | Multi-device access needs or cross-system cloud sync demands. | `UNKNOWN` |
| 5 | `offline_capable_required` | `BOOLEAN / UNKNOWN` | The operator performs the task in intermittent or zero-connectivity environments. | Field operations, travel, or strict air-gapped networks. | `UNKNOWN` |
| 6 | `browser_only_surface` | `BOOLEAN / UNKNOWN` | The workflow is executed entirely inside web browsers against web applications. | DOM scraping, web app automation, browser tab context. | `UNKNOWN` |
| 7 | `desktop_os_access_required` | `BOOLEAN / UNKNOWN` | The workflow requires low-level OS access (local filesystem, system tray, hardware ports, native processes). | Interacting with native desktop applications or local file trees. | `UNKNOWN` |
| 8 | `mobile_surface_required` | `BOOLEAN / UNKNOWN` | The operator requires handheld execution (camera, GPS, on-the-go notifications). | Field agents, warehouse workers, mobile-first tasks. | `UNKNOWN` |
| 9 | `scheduled_background_execution_required` | `BOOLEAN / UNKNOWN` | The task must run unattended on a schedule (cron) or polling loop without operator intervention. | Daily/nightly synchronization, automated report compilation. | `UNKNOWN` |
| 10 | `event_driven_trigger_required` | `BOOLEAN / UNKNOWN` | The task is triggered instantly by an external event (webhook, message queue, email arrival). | Inbound webhook handling, immediate alert routing. | `UNKNOWN` |
| 11 | `api_integrations_available` | `BOOLEAN / UNKNOWN` | Official, authenticated APIs exist for the target third-party services. | Documented REST/GraphQL/gRPC APIs with accessible credentials. | `UNKNOWN` |
| 12 | `realtime_latency_sensitive` | `BOOLEAN / UNKNOWN` | The task requires sub-second processing (audio/video streaming, high-frequency trading, immediate interactive feedback). | Interactive user feedback loop < 200ms or real-time streaming. | `UNKNOWN` |
| 13 | `audit_trail_or_compliance_required` | `BOOLEAN / UNKNOWN` | Regulatory or organizational rules mandate immutable logging, SOC2/HIPAA compliance, or data retention. | Regulated domains (finance, healthcare, legal) with legal audit mandates. | `UNKNOWN` |
| 14 | `recurring_commercial_wtp_validated` | `BOOLEAN / UNKNOWN` | Evidence verifies that customers will pay a recurring subscription for an automated solution. | Signed letters of intent (LOI), prepayments, or existing SaaS spend. | `UNKNOWN` |
| 15 | `high_domain_complexity_rules` | `BOOLEAN / UNKNOWN` | The task involves complex calculations, tax codes, multi-variant business rules, or mathematical models. | Deep domain formulas, regulatory calculation engines, complex state machines. | `UNKNOWN` |

---

## Constraint Conflict & Incompatibility Rules

Architectural evaluation must enforce logical consistency across constraints:

### Rule 1: Single User vs. Multi-User Incompatibility
- `single_user_only = TRUE` and `multi_user_required = TRUE` are mutually exclusive.
- If both appear indicated by initial signals, the evaluator must decompose the workflow into distinct roles or mark `multi_user_required = UNKNOWN` until team handoffs are empirically observed.

### Rule 2: Local Data vs. Cloud Sync
- If `local_data_only = TRUE`, then `cloud_sync_required` MUST be `FALSE`.
- Imposing cloud databases on a local-data workflow creates unnecessary attack surfaces, GDPR/compliance burdens, and hosting costs.

### Rule 3: Browser Surface vs. Native OS Access
- If `browser_only_surface = TRUE`, desktop OS access must be `FALSE`.
- Browser extensions cannot access arbitrary local files without native messaging hosts (which dramatically increases installation friction and security review requirements).

### Rule 4: Unknowns Rule
- If an operational requirement is not explicitly proven by verified signals, it MUST be marked `UNKNOWN`.
- **An `UNKNOWN` constraint cannot justify architectural complexity**. For instance, if `cloud_sync_required` is `UNKNOWN`, the solution cannot default to a cloud-hosted backend.

---

## Output Representation in JSON

```json
{
  "constraints": {
    "single_user_only": true,
    "multi_user_required": false,
    "local_data_only": true,
    "cloud_sync_required": false,
    "offline_capable_required": true,
    "browser_only_surface": false,
    "desktop_os_access_required": true,
    "mobile_surface_required": false,
    "scheduled_background_execution_required": false,
    "event_driven_trigger_required": false,
    "api_integrations_available": false,
    "realtime_latency_sensitive": false,
    "audit_trail_or_compliance_required": false,
    "recurring_commercial_wtp_validated": false,
    "high_domain_complexity_rules": false
  },
  "inferred_complexity_tier": "LOCAL_UTILITY",
  "constraint_notes": [
    "Operator processes local PDF files on personal laptop.",
    "No remote collaboration or cloud storage indicated.",
    "Commercial willingness to pay is unverified; SaaS is disqualified."
  ]
}
```
