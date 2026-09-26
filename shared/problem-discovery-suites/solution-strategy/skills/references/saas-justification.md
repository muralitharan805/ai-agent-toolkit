# SaaS Justification Gate Reference

## Purpose
This document specifies the rigorous gating mechanism required to classify a solution as `MULTI_TENANT_SAAS`. Building a SaaS application carries severe fixed engineering, operational, and regulatory costs. Labeling a product concept as "SaaS" without empirical justification leads to capital waste and premature over-engineering.

---

## The 7-Dimension SaaS Justification Scorecard

To earn `STRONG_CANDIDATE` status, the problem evidence must affirmatively satisfy all 7 dimensions. If any single foundational dimension is `FALSE` or `UNKNOWN`, the status defaults to `NOT_YET_JUSTIFIED` or `REJECTED`.

| # | Dimension | Requirement for SaaS Qualification | Default if Evidence Missing |
|---|---|---|---|
| 1 | **Multi-User Collaboration** | The workflow requires multiple operators across different roles, teams, or organizations interacting on shared items. | `UNKNOWN` $\rightarrow$ Disqualifies SaaS |
| 2 | **Multi-Tenant Isolation** | Data belonging to different customer organizations must be securely separated in shared cloud infrastructure. | `UNKNOWN` $\rightarrow$ Disqualifies SaaS |
| 3 | **Shared Cloud State** | Data must persist in the cloud and be accessed continuously across different sessions, browsers, and geographic locations. | `UNKNOWN` $\rightarrow$ Disqualifies SaaS |
| 4 | **Unattended Background Jobs** | The system must execute scheduled crons, webhooks, asynchronous workers, or heavy processing without an operator active. | `UNKNOWN` $\rightarrow$ Disqualifies SaaS |
| 5 | **Role-Based Access (RBAC)** | Distinct permission tiers (Admin, Editor, Viewer, Auditor) are strictly required for security or organizational policy. | `UNKNOWN` $\rightarrow$ Single-user app |
| 6 | **Validated Commercial WTP** | Verified evidence exists that operators will pay a recurring subscription ($/month or $/seat) rather than a one-time utility price. | `UNKNOWN` $\rightarrow$ `NOT_YET_JUSTIFIED` |
| 7 | **Ongoing Workflow Retention** | The solution delivers continuous monthly value rather than solving a one-time migration or infrequent annual task. | `UNKNOWN` $\rightarrow$ One-time utility |

---

## The Three SaaS Verdict States

```text
                  [SaaS Justification Gate]
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
[STRONG_CANDIDATE]    [NOT_YET_JUSTIFIED]      [REJECTED]
```

### 1. `STRONG_CANDIDATE`
- **Definition**: All 7 dimensions have positive, verified empirical evidence.
- **Criteria**:
  - `multi_user_required = TRUE`
  - `cloud_sync_required = TRUE`
  - `recurring_commercial_wtp_validated = TRUE`
  - Multi-tenancy and background processing are mandatory for the core value proposition.
- **Next Step**: Proceed to architectural blueprint for multi-tenant service, preceded by an STS to de-risk highest technical uncertainty.

### 2. `NOT_YET_JUSTIFIED`
- **Definition**: The problem is valid, but critical operational needs (multi-user collaboration or commercial willingness to pay) remain unproven.
- **Criteria**:
  - Problem validated, but `multi_user_required = UNKNOWN` or `recurring_commercial_wtp_validated = UNKNOWN`.
- **Next Step**: Build an immediate low-complexity tool (CLI, script, spreadsheet, or single-user web app) to validate user retention and payment readiness before building multi-tenant infrastructure.

### 3. `REJECTED`
- **Definition**: The problem is effectively solved by a local utility, single-user script, browser extension, or non-software process.
- **Criteria**:
  - `single_user_only = TRUE` OR `local_data_only = TRUE` OR non-software sufficiency score $\ge 80\%$.
- **Next Step**: Build the local utility or implement the non-software process. Custom SaaS is explicitly barred.

---

## The True Cost of Premature SaaS

Every SaaS application incurs an unavoidable "Operational Tax" regardless of user count:

1. **Authentication & Identity**: OAuth, MFA, password reset, session token invalidation, JWT rotation.
2. **Tenant Data Isolation**: Row-Level Security (RLS), tenant schema segregation, accidental leak risk.
3. **Billing & Subscription Lifecycle**: Stripe webhooks, prorations, failed charge retries, invoice generation, tax nexus compliance.
4. **DevOps & Infrastructure**: Docker containers, SSL certs, database migrations, connection pooling, automated backups, 99.9% uptime SLA.
5. **Security & Compliance**: SOC2 type II audit trails, GDPR data deletion endpoints, cookie consent banners, penetration testing.

Building all of the above for a single-user utility is catastrophic engineering negligence.
