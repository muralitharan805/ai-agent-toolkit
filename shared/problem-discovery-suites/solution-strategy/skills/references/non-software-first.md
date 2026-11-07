# Non-Software First Evaluation Reference

## Purpose
This document provides the authoritative evaluation framework for the **Non-Software Sufficiency Gate**. The fundamental law of solution architecture is: *Evidence of a problem does not automatically justify custom software.* Building software introduces continuous maintenance, hosting overhead, operational debt, and security surface. A non-software solution that works immediately is superior to an over-engineered software system that takes months to ship.

---

## The 4 Non-Software Solution Classes

### 1. Checklist or Standard Operating Procedure (`CHECKLIST_OR_SOP`)
- **Primary Mechanism**: Written step-by-step instructions, pre-flight checklists, or standardized job-aid cards.
- **Best Applied When**:
  - Root cause of failure is human omission, forgotten verification steps, or inconsistent ordering.
  - Operational frequency is low to moderate ($\le 5$ times/day).
  - Workflow steps are stable and require manual inspection or discretion.
- **Example**: A 7-step checklist for verifying database migration backups before running DDL scripts in production.

### 2. Structured Spreadsheet (`STRUCTURED_SPREADSHEET`)
- **Primary Mechanism**: Standardized spreadsheet (Excel, Google Sheets, LibreOffice Calc) equipped with data validation dropdowns, lookup formulas (`XLOOKUP`), conditional formatting alerts, and locked template cells.
- **Best Applied When**:
  - Data volume is small to moderate ($< 5,000$ active rows).
  - Calculations are standard arithmetic, tabular reconciliations, or pivot aggregations.
  - Workflow is operated by a single person or a small co-located team with low concurrency.
- **Example**: Monthly expense reconciliation between credit card statements and internal receipts.

### 3. Manual Concierge Service (`MANUAL_CONCIERGE_SERVICE`)
- **Primary Mechanism**: A human service provider executes the workflow manually for the customer using existing off-the-shelf tools, without custom automation.
- **Best Applied When**:
  - The business problem is verified, but exact workflow logic, rules, and edge cases are still changing.
  - Transaction volume is low ($< 20$ requests/week), making human execution cheaper than software development.
  - The goal is to learn edge cases and test willingness to pay before writing a single line of code.
- **Example**: Manually scraping competitor prices once a week and emailing a formatted PDF report to the client.

### 4. Process or Policy Redesign (`PROCESS_OR_POLICY_REDESIGN`)
- **Primary Mechanism**: Eliminating unnecessary approval steps, consolidating duplicate handoffs, adjusting organizational policy, or switching to an off-the-shelf tool.
- **Best Applied When**:
  - Friction is caused by artificial organizational bureaucracy rather than technological limits.
  - Removing a step eliminates 100% of the friction with zero code.
- **Example**: Removing a three-tier manager signoff on developer SaaS subscriptions under $50/month instead of building an approval ticketing system.

---

## The 80% Sufficiency Rubric

A non-software intervention is deemed **SUFFICIENT** if it satisfies the following test:

$$\text{Sufficiency Score} = \frac{\text{Friction Eliminated by Non-Software}}{\text{Total Observed Friction}} \ge 0.80$$

| Criterion | Evaluation Question | Threshold for Software Transition |
|---|---|---|
| **Friction Reduction** | Does the non-software solution eliminate $\ge 80\%$ of errors or time loss? | If $< 80\%$, software utility may be considered. |
| **Execution Volume** | How often does the task execute per day/week? | If manual execution consumes $> 10$ hours/week of skilled operator time. |
| **Error Consequence** | What happens if a human operator makes a mistake? | If a mistake causes legal liability, data corruption, or catastrophic financial loss. |
| **Latency Requirement** | How fast must the output be delivered? | If output is required in $< 5$ minutes or real-time. |
| **Data Integrity at Scale** | Does the spreadsheet corrupt formulas or crash due to volume? | If rows exceed 10,000 or concurrent editing causes overwrite collisions. |

---

## Non-Software Evaluation Decision Flow

```text
Problem Candidate Validated
           │
           ▼
[Can a Checklist or SOP eliminate the omission errors?]
     ├── YES ──► Output: CHECKLIST_OR_SOP (Software REJECTED)
     └── NO
           ▼
[Can a Structured Spreadsheet handle the calculation/reconciliation?]
     ├── YES ──► Output: STRUCTURED_SPREADSHEET (Software REJECTED)
     └── NO
           ▼
[Can a Policy Redesign or Existing Tool eliminate the friction?]
     ├── YES ──► Output: PROCESS_OR_POLICY_REDESIGN (Software REJECTED)
     └── NO
           ▼
[Is transaction volume low enough that a Concierge Service learns faster?]
     ├── YES ──► Output: MANUAL_CONCIERGE_SERVICE (Software DEFERRED)
     └── NO
           ▼
Non-Software INSUFFICIENT ──► Proceed to Software Solution Class Selection
```

---

## Output Template for Non-Software Assessment

```json
{
  "non_software_evaluation": {
    "is_sufficient": true,
    "recommended_non_software_class": "STRUCTURED_SPREADSHEET",
    "friction_reduction_percentage": 85,
    "justification": "A locked Excel template with data validation and XLOOKUP eliminates 85% of invoice total mismatches without building custom billing software.",
    "software_transition_triggers": [
      "Monthly transaction volume exceeds 2,500 invoices",
      "Multiple accountants require concurrent row-level locking",
      "Automated bank feed API integration becomes legally mandatory"
    ]
  }
}
```
