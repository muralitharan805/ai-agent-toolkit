# Scope Classification & Domain Decomposition

## Overview
Decomposes raw input into manageable, structured research scopes. Ensures research plans do not arbitrarily expand or artificially restrict operational boundaries.

---

## 1. Request Archetypes & Scope Sensing

| Request Archetype | Characteristics | Required Decomposition Behavior |
|---|---|---|
| **Broad Domain** | High-level industry name (e.g., "ecommerce logistics", "construction supply"). | Identify 3–5 representative operators and core operational workflows across the 5 lenses. |
| **Messy Brain-dump** | Multi-paragraph, stream-of-consciousness text with mixed complaints and ideas. | Disentangle distinct tasks, attribute claims per operator, and isolate user biases. |
| **Narrow Workflow** | Explicit operator and localized task (e.g., "radiology report billing handoff"). | Remain strictly bounded to the requested workflow; avoid generating unrelated streams. |
| **Multi-Domain** | Request covering disparate industries (e.g., "real estate agents and preschool teachers"). | Partition into separate research scopes or explicitly segregated streams. |
| **Continuation** | Follow-up iteration referencing existing research run. | Preserve prior plan entity IDs, highlight incremental delta, and audit existing context. |

---

## 2. Hierarchical Decomposition Model

All operational planning follows the strict 3-tier hierarchy:
```text
Actor (Who performs the job?)
  └── Task (What concrete activity occurs?)
        └── Workflow (What end-to-end operational sequence connects these tasks?)
```

Example:
- **Actor**: Merchandiser
- **Task**: Fabric delivery tracking
- **Workflow**: Pre-production sourcing coordination

---

## 3. The 5 Adaptive Operational Lenses

To ensure balanced operational coverage across real businesses, the planner checks candidate workflows against 5 diagnostic lenses:

1. **Frontline / Intake**:
   - Initial touchpoints where data, physical goods, or customer requests enter the organisation.
   - *Examples*: Patient intake, truck weighbridge logging, supplier purchase order reception.
2. **Multi-party Handoffs**:
   - Transfer of responsibility, data, or artifacts between separate internal teams or external entities.
   - *Examples*: Warehouse-to-courier dispatch, design-to-production specs, broker-to-underwriter files.
3. **Back-office Reconciliation**:
   - Comparison and alignment of records across disparate systems, spreadsheets, and bank statements.
   - *Examples*: Marketplace payout matching, freight bill audits, inventory physical-to-ERP sync.
4. **Regulatory / Portal Workflows**:
   - Compliance submissions, statutory filings, government portal interactions, and mandatory recordkeeping.
   - *Examples*: Customs e-way bill generation, tax deductions, environmental safety audits.
5. **Exceptions & Disputes**:
   - Deviations from the standard operating procedure requiring manual escalation and rework.
   - *Examples*: Damaged goods in transit, customer chargebacks, mispicked orders, payroll discrepancies.

> [!NOTE]
> The 5 lenses are **diagnostic tools** to verify thorough coverage. Narrow requests need only touch relevant lenses. Do NOT manufacture artificial problems to satisfy all 5 lenses if not applicable.
