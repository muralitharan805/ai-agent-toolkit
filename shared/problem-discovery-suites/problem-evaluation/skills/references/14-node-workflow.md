# Forensic 14-Node Workflow Mapping Specification

## Overview
Defines the canonical 14-node workflow reconstruction model. Forces the agent to map the complete operational reality rather than jumping directly to software solutions.

---

## 1. The 14 Operational Nodes

Every candidate problem must audit and populate all 14 nodes:

| # | Node Name | Description | Example (Ecommerce Inventory Sync) |
|---|---|---|---|
| **1** | `actor` | Human worker executing the operational step. | `ecommerce merchant` |
| **2** | `trigger` | Event that starts the workflow. | `Order placed on Channel A` |
| **3** | `input` | Data, physical objects, or documents needed. | `Channel A inventory quantity` |
| **4** | `steps` | Sequential actions performed by the operator. | `[1. Open Channel B, 2. Decrement stock, 3. Repeat for Channel C]` |
| **5** | `tools` | Systems, spreadsheets, or paper tools used. | `Amazon Seller Central, Shopify dashboard` |
| **6** | `decisions` | Judgment calls made during the process. | `Whether to allocate safety buffer stock` |
| **7** | `handoffs` | Points where data or responsibility passes to others. | `Warehouse picker receiving updated pack slip` |
| **8** | `delays` | Latency or waiting periods between steps. | `15–60 minute lag before merchant notices order` |
| **9** | `rework` | Repeated manual glue-work or duplicate effort. | `Re-entering same stock number across 4 tabs` |
| **10** | `errors` | Mistakes, discrepancies, or transcription flaws. | `Overselling out-of-stock items` |
| **11** | `output` | Final state or artifact created. | `Synchronized stock values across channels` |
| **12** | `cost` | Financial, time, or operational resource drain. | `5–8 hours/week spent on manual adjustments` |
| **13** | `risk` | Downstream danger if the process fails. | `Channel suspension, seller rating penalty` |
| **14** | `audit` | How records are verified or compliance checked. | `Weekly spreadsheet reconciliation against physical rack count` |

---

## 2. Zero-Hallucination Policy
- If evidence does not provide data for a node (e.g. exact cost, decision rules, audit trails), the node MUST be explicitly set to `"UNKNOWN"`.
- Setting a node to `"UNKNOWN"` maintains transparency and triggers focused downstream research requests.
