# 14-Node Forensic Workflow Mapping & Human Glue-Work Analysis

## Overview

Traditional product discovery relies on user opinions, wishlist requests, and hypothetical surveys—all of which fail to predict real commercial willingness to pay. Grounded problem discovery replaces subjective speculation with **forensic workflow mapping**: investigating what operators actually *do* step-by-step during operational execution.

This methodology is anchored on the **PAIN $\rightarrow$ WORKFLOW $\rightarrow$ EVIDENCE $\rightarrow$ WEDGE** framework.

---

## 1. The Core Realization: "Software Exists, but Glue is Missing"

In modern organizations, the problem is almost never an absence of software. Core infrastructure already exists: ERPs, CRMs, accounting platforms, portals, and spreadsheets.

The recurring operational failure is the **Universal Broken Loop**:

$$\text{System A} \longrightarrow [\text{Human}] \longrightarrow \text{Unversioned Excel / CSV} \longrightarrow [\text{Human}] \longrightarrow \text{Chat / Email Escalation} \longrightarrow [\text{Human}] \longrightarrow \text{System B}$$

```text
┌────────────────┐      Manual Export      ┌──────────────────┐
│    System A    │ ──────────────────────► │   Local Folder   │
│ (ERP/CRM/Repo) │                         │  (Unversioned)   │
└────────────────┘                         └────────┬─────────┘
                                                    │
                                                    ▼
┌────────────────┐      Manual Re-key      ┌──────────────────┐
│    System B    │ ◄────────────────────── │ 40-Tab Excel SOP │
│ (Tax/Portal/DB)│                         │ (VLOOKUP / Glue) │
└────────────────┘                         └──────────────────┘
```

> **The Builder's Goal**: Never attempt to "replace Excel" or "replace the ERP". Identify why the manual workaround spreadsheet or script was created, and eliminate the painful copy-paste-verify loop around it.

---

## 2. The 9-Stage Operational Execution Cycle

Operators move through 9 predictable phases during recurring business tasks. Map where the breakdown occurs:

$$\textbf{Trigger} \rightarrow \textbf{Collect Data} \rightarrow \textbf{Clean / Convert} \rightarrow \textbf{Verify} \rightarrow \textbf{Calculate} \rightarrow \textbf{Get Approval} \rightarrow \textbf{Submit} \rightarrow \textbf{Track Result} \rightarrow \textbf{Correct Mistakes}$$

### The 12 Specific Glue-Work Signals to Hunt:
When shadowing an operator or auditing a process, scan for these 12 operational frictions:
1. **Copy-paste routines**: Copying values between tabs, windows, or portals.
2. **Repeated data entry**: Typing identical customer or invoice details into multiple systems.
3. **CSV import/export friction**: Downloading CSVs, modifying headers, re-saving, and uploading.
4. **PDF-to-Excel transfers**: Manually re-keying bank statements, receipts, or bills.
5. **Email attachment tracking**: Downloading attachments and manually filing them into local folders.
6. **WhatsApp / Chat follow-up**: Chasing status, missing attachments, or approvals over chat.
7. **Multiple portal logins**: Logging into 3+ third-party sites to retrieve or submit records.
8. **Manual comparison / reconciliation**: Cross-checking two sheets with eye or basic VLOOKUP.
9. **Screenshots as proof**: Taking screenshots of confirmation screens and saving them as audit proof.
10. **Manual deadline reminders**: Setting phone alarms or calendar events for filing cutoffs.
11. **Approval chasing**: Pinging managers repeatedly for purchase or invoice sign-offs.
12. **Same report in multiple formats**: Generating one PDF for management, one CSV for accounts, and one message for clients.

### The "3+ Tools Connected" Opportunity Pattern:
Workflows that bridge 3 or more disconnected systems represent high-conviction software targets:
$$\textbf{WhatsApp} \longrightarrow \textbf{Excel} \longrightarrow \textbf{Government Portal} \longrightarrow \textbf{Email Confirmation}$$
*The human glue-work connecting these disparate nodes is the exact entry point for a lean micro-utility or SaaS wedge.*

---

## 3. The 14 Forensic Workflow Nodes

Every operational process can be forensically deconstructed across **14 distinct nodes**:

| Node | Name | Definition & Forensic Discovery Question |
| :---: | :--- | :--- |
| **1** | **Actor** | Who initiates and operates this step? What is their job title, technical literacy, and who gets blamed if this breaks? |
| **2** | **Trigger** | What operational event starts this workflow? (Webhook, email attachment, portal status update, calendar cutoff). |
| **3** | **Input** | What exact raw materials or data come in? (PDF invoice, unstandardized CSV, API payload, physical scan). |
| **4** | **Steps** | The exact sequential keyboard, mouse, or terminal actions taken. What screens are open simultaneously? |
| **5** | **Tools** | Every tool touched (Outlook, Excel, Chrome tabs, ERP, terminal, Slack, custom scripts). |
| **6** | **Decisions** | What logic determines the execution branch? (e.g., Is total variance > 2%? Is vendor compliance current?). |
| **7** | **Handoffs** | Where does work pass from person A to person B, or system A to system B? (Primary bottleneck zone). |
| **8** | **Delays** | How long does data sit idle between steps? (Waiting for vendor reply, batch job queues, manager signoff). |
| **9** | **Rework** | How often must the task be redone due to bad input data, schema changes, or validation rejections? |
| **10** | **Errors** | What mistakes routinely occur? (Typo in tax/ID field, missed attachment, broken delimiter, duplicate records). |
| **11** | **Output** | Final deliverable, report, database update, or regulatory filing produced. What is sent downstream? |
| **12** | **Cost** | Calculated weekly wasted labor hours $\times$ loaded wage + software licensing overhead. |
| **13** | **Risk** | Financial penalty, regulatory audit failure, client churn, or security exposure if an error slips through. |
| **14** | **Audit** | Who signs off on the final output? How is historical proof, version history, or chain-of-custody maintained? |

---

## 4. Isolating the Repeated Failure Point

A large workflow by itself is not an opportunity. You must isolate the **repeated small failure point**. At every step of the chain, ask these **5 Diagnostic Questions**:

1. **Who is doing this step?** (Job title, vernacular literacy, device used).
2. **What exact information is required?** (Format, schema, completeness).
3. **Why does it pass to the next person or tool?** (Policy, technical limitation, sign-off).
4. **Where does idle waiting or rework occur?** (Bottlenecks, back-and-forth messaging).
5. **What is the consequence if this step fails?** (Financial loss, delay, wrong print/shipment, compliance fine).

---

## 5. The 4 Operational Friction Archetypes

Across disparate industries, operational glue-work falls into 4 predictable archetypes:

### Archetype 1: Asymmetric Two-Way Sync
- **Mechanism**: System A updates records, but System B cannot receive automated push notifications.
- **Human Workaround**: Operator downloads reports, reformats columns, and uploads to System B.
- **Failure Point**: Schema drift causes data divergence, resulting in oversold inventory or incorrect billing.

### Archetype 2: Regulatory Portal Ingestion & Reconciliation
- **Mechanism**: A government tax agency or licensing board requires periodic filing via a locked web portal lacking APIs.
- **Human Workaround**: Staff solve CAPTCHAs, manually enter 30+ form fields, download signed receipts.
- **Failure Point**: Missed deadlines lead to direct statutory penalties, revoked permits, or blocked tax credits.

### Archetype 3: The "80% SaaS" Workaround Layer
- **Mechanism**: An expensive vertical SaaS tool misses critical local compliance, micro-billing rules, or custom formats.
- **Human Workaround**: Users export raw CSVs from the SaaS and perform custom calculations in Excel.
- **Failure Point**: Employee turnover leaves complex formulas undocumented and unmaintained.

### Archetype 4: Multi-Source Document Assembly & Verification
- **Mechanism**: A business event requires cross-verifying documents from multiple parties (IDs, certificates, statements).
- **Human Workaround**: Coordinator tracks attachments in email, checks printed checklists, re-keys verification dates.
- **Failure Point**: Expired documents or fraudulent certificates go undetected until an audit occurs.
