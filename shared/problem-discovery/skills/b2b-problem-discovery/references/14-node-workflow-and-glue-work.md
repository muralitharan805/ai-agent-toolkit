# 14-Node Forensic Workflow Mapping & Glue-Work Analysis

## Overview

Traditional market research relies heavily on user opinions, wishlist feature requests, and hypothetical surveys—all of which fail to predict real Willingness to Pay (WTP). Grounded problem discovery replaces opinion with **forensic workflow mapping**: decomposing what users actually *do* step-by-step during their daily operations.

---

## The 14 Forensic Workflow Nodes

Every B2B and operational workflow can be broken down into 14 distinct nodes:

| # | Node | Definition | Forensic Discovery Questions |
|---|---|---|---|
| **1** | **Actor** | The specific job title / role executing the work | Who sits in the chair? Who gets blamed if this breaks? |
| **2** | **Trigger** | The operational event that initiates the workflow | What email, date, webhook, or invoice starts this cycle? |
| **3** | **Input** | Raw data, files, credentials, or physical items required | What format is the data in (PDF, CSV, portal, scan)? |
| **4** | **Steps** | Sequential manual or automated actions taken | Walk me through click-by-click. What screen is open? |
| **5** | **Tools** | Software, scripts, spreadsheets, portals, paper used | Which applications are open simultaneously? |
| **6** | **Decisions** | Business logic, calculations, or threshold rules applied | How do you know when an item passes vs fails review? |
| **7** | **Handoffs** | Transfers across teams, vendors, or external parties | Where does the work sit waiting for someone else? |
| **8** | **Waiting** | Latency, batch queues, or managerial approval delays | How long does an item sit idle before the next action? |
| **9** | **Rework** | Re-keying, format conversions, and fixing validation errors | How often do you have to re-enter data into another system? |
| **10** | **Errors** | Failure rates, missed deadlines, or calculation discrepancies | What happens when an edge case or mismatch occurs? |
| **11** | **Output** | Deliverable, report, database record, or filing produced | What is the final artifact sent to the customer/auditor? |
| **12** | **Cost** | Direct labor hours and software licensing expenditure | How many hours per week are spent on this exact task? |
| **13** | **Risk** | Financial penalty, client churn, or regulatory compliance exposure | What is the worst-case dollar penalty if a mistake slips through? |
| **14** | **Audit** | Oversight, reconciliation, or compliance verification | Who signs off on the final output and checks the math? |

---

## Deconstructing Human "Glue-Work"

**Human Glue-Work** is the manual interstitial labor required to bridge two disconnected enterprise software platforms:

```text
┌──────────────┐      Manual Export      ┌──────────────────┐
│   System A   │ ──────────────────────► │   Local Folder   │
│   (ERP/CRM)  │                         │   (Unversioned)  │
└──────────────┘                         └────────┬─────────┘
                                                  │
                                                  ▼
┌──────────────┐      Manual Re-key      ┌──────────────────┐
│   System B   │ ◄────────────────────── │ 40-Tab Excel SOP │
│ (Accounting) │                         │  (VLOOKUP / Glue)│
└──────────────┘                         └──────────────────┘
```

### Hallmarks of High-Value Glue-Work:
1. **The "Shadow" Excel Template**: A complex spreadsheet with multiple macro/VLOOKUP tabs maintained by a single person who "knows how it works".
2. **Double Data Entry**: Re-typing numbers from a vendor portal or PDF invoice into an internal ERP.
3. **Zapier/Make Spaghetti**: Multiple multi-step webhooks failing intermittently on schema changes.
4. **Copy-Paste Handoffs**: Copying data out of emails or WhatsApp groups into ticketing systems.

---

## Forensic Interviewing Protocols

When interviewing subject matter experts:
- **Never ask**: "Would you buy a software that automates X?" (Triggers false positive validation).
- **Always ask**: "Can you share your screen and show me the last time you performed this task?"
- **Ask "Why" twice**: When a user asks for a feature, dig into the operational trigger that caused the request.
- **Trace the file trail**: Ask to see the actual Excel spreadsheet, invoice, or screenshot of the error.
