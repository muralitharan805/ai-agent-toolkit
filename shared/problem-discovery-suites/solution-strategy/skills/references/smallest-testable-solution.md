# Smallest Testable Solution (STS) Reference

## Purpose
This document provides the operational blueprint for designing the **Smallest Testable Solution (STS)**. In modern product engineering, building a full-scale architecture before proving the core workflow is the leading cause of wasted capital. The STS is an empirical probe designed to test the single most vulnerable hypothesis with the least possible engineering investment.

---

## STS vs. Traditional MVP

| Dimension | Traditional MVP | Smallest Testable Solution (STS) |
|---|---|---|
| **Primary Goal** | Deliver a minimal version of the final software platform. | Test a specific behavioral or technical hypothesis immediately. |
| **Build Time** | 2 to 6 months | $\le 14$ days (strictly bounded) |
| **Infrastructure** | Database, Auth, CI/CD, Hosting, UI | Local scripts, spreadsheets, manual concierge, or no-code |
| **Failure Cost** | High (months of sunk engineering effort) | Negligible (1–2 weeks of exploration) |
| **Output** | Software product | Verified empirical evidence & validated workflow rules |

---

## The 4 STS Archetypes

### 1. The Concierge Pilot (`CONCIERGE_PILOT`)
- **Mechanism**: The builder performs the service manually for target operators using standard desktop tools, delivering results via email or shared drive.
- **Hypothesis Tested**: "Do operators value the output enough to change their existing workflow or pay money?"
- **Build Effort**: 0 to 2 days.
- **Example**: Manually parsing and formatting 20 supplier invoices into QuickBooks format for a local retail chain before writing an OCR parser.

### 2. The Local Script Pilot (`LOCAL_SCRIPT_PILOT`)
- **Mechanism**: A single-file, idempotent Python or Node CLI script provided directly to a technical or semi-technical operator.
- **Hypothesis Tested**: "Does automated parsing/transformation eliminate the operational bottleneck under real-world data variation?"
- **Build Effort**: 2 to 5 days.
- **Example**: A 150-line script parsing messy CSV bank statements and outputting formatted tax summaries.

### 3. The No-Code Integration Pipeline (`NO_CODE_WORKFLOW`)
- **Mechanism**: Connecting existing commercial SaaS tools via Zapier, Make, or n8n with a Google Sheet as the temporary database.
- **Hypothesis Tested**: "Does automated synchronization between System A and System B prevent human data entry errors?"
- **Build Effort**: 1 to 3 days.
- **Example**: Webhook catching new Stripe sales, validating VAT numbers via public API, and appending rows to a shared reconciliation sheet.

### 4. The Thin Extension Prototype (`THIN_EXTENSION_PROTOTYPE`)
- **Mechanism**: An unpacked Chrome Manifest V3 extension with a simple content script that alters a single DOM element or extracts page data.
- **Hypothesis Tested**: "Will operators click an in-browser action button to automate their repetitive data transfer?"
- **Build Effort**: 3 to 7 days.
- **Example**: A browser extension adding a "Copy to CRM" button on LinkedIn profile pages.

---

## The 14-Day Delivery Constraint

An STS must be deliverable within **14 calendar days** (maximum 80 engineering hours). If an STS proposal requires:
- Multi-tenant database migrations
- Custom OAuth 2.0 servers
- Kubernetes cluster provisioning
- Cross-platform mobile builds

**The proposal is REJECTED as over-scoped**. The evaluator must decompose the hypothesis into a narrower, non-software or script-based pilot.

---

## Structure of an STS Specification

Every `SolutionAssessment` must output an STS contract with the following fields:

```json
{
  "smallest_testable_solution": {
    "archetype": "LOCAL_SCRIPT_PILOT",
    "target_hypothesis": "Accountants will use a CLI script to reconcile invoices daily if it runs in < 5 seconds.",
    "estimated_build_days": 3,
    "pilot_population": "5 target e-commerce bookkeepers",
    "observation_duration_days": 10,
    "success_threshold": "At least 4 of 5 bookkeepers run the script on >= 80% of business days",
    "falsification_rule": "Fewer than 3 bookkeepers adopt the script due to manual preference or edge-case errors",
    "next_step_if_passed": "Wrap script into local desktop utility or headless background integration service",
    "next_step_if_failed": "Pivot to structured spreadsheet checklist or abandon candidate"
  }
}
```
