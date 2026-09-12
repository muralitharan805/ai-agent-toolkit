# 14-Node Forensic Workflow Mapping & Human Glue-Work Analysis

## Overview

Traditional product discovery relies on user opinions, wishlist requests, and hypothetical surveys—all of which fail to predict real commercial willingness to pay. Grounded problem discovery replaces subjective speculation with **forensic workflow mapping**: investigating what operators actually *do* step-by-step during operational execution.

This methodology applies across **all software problem domains**:
- **B2B Back-Office Operations**: Multi-system reconciliation, compliance auditing, invoice splitting.
- **Developer Tooling & DevOps**: Pipeline glue, configuration drift between environments, schema migrations.
- **E-Commerce & Retail Ops**: Multi-channel inventory sync, return processing, marketplace fee reconciliation.
- **Solo Builder Micro-SaaS**: Targeted workflow bottlenecks where single operators rely on error-prone manual steps.

---

## 1. The Core Realization: "Software Exists, but Glue is Missing"

In modern organizations, the problem is almost never an absence of software. Core infrastructure already exists: ERPs, CRMs, accounting platforms, issue trackers, and databases.

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

The builder's goal is **never** to "replace Excel" or "replace the ERP". The builder's goal is to **identify why the workaround spreadsheet or manual script was created, and eliminate the painful copy-paste-verify loop around it.**

---

## 2. The 14 Forensic Workflow Nodes

Every business or technical operational process can be forensically deconstructed across **14 distinct nodes**. When examining a failure point, document each node:

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

## 3. The 4 Universal Friction Archetypes

Across disparate industries, operational glue-work falls into 4 predictable archetypes:

### Archetype 1: Asymmetric Two-Way Sync
- **Mechanism**: System A updates records, but System B (or an external partner database) cannot receive automated push notifications.
- **Human Workaround**: An operator manually downloads a report daily, filters modified rows, reformats date/currency columns, and uploads to System B.
- **Failure Point**: Schema drift or human omission causes data divergence, resulting in oversold inventory or incorrect billing.

### Archetype 2: Regulatory Portal Ingestion & Reconciliation
- **Mechanism**: A government tax agency, licensing board, or municipal authority requires periodic data filing via a locked web portal lacking public REST APIs.
- **Human Workaround**: Staff solve CAPTCHAs, manually enter 30+ form fields from internal systems, download signed receipts, and archive them in shared drives.
- **Failure Point**: Missed deadlines lead to direct statutory penalties, revoked permits, or blocked tax credits.

### Archetype 3: The "80% SaaS" Workaround Layer
- **Mechanism**: An expensive vertical SaaS tool solves core functions (e.g., job dispatching or CRM), but misses critical local compliance, micro-billing rules, or custom customer requirements.
- **Human Workaround**: Users export raw CSVs from the SaaS, perform custom calculations in Excel, and communicate exceptions over messaging apps.
- **Failure Point**: High employee turnover leaves complex spreadsheet formulas undocumented and unmaintained.

### Archetype 4: Multi-Source Document Assembly & Verification
- **Mechanism**: A single business event (loan approval, contractor onboarding, vendor payout) requires cross-verifying documents from multiple independent parties (IDs, insurance certificates, bank statements).
- **Human Workaround**: A coordinator tracks incoming attachments in an email inbox, checks boxes on a printed checklist, and re-keys verification dates into an ERP.
- **Failure Point**: Expired documents or fraudulent certificates go undetected until an audit or incident occurs.

---

## 4. Forensic Interviewing Protocols

When interviewing subject matter experts and operators:

- **NEVER ASK**: *"Would you buy a tool that automates X?"* (Hypothetical questions yield polite false positives).
- **ALWAYS ASK**: *"Can you share your screen and walk me through the exact steps you took the last time this broke?"*
- **PROBE THE WORKAROUND**: *"When this file was missing or formatted incorrectly, what did you do next? Who did you call?"*
- **AUDIT THE ECONOMICS**: *"How many hours did your team spend on this reconciliation last week? What tools are currently billed for this?"*
