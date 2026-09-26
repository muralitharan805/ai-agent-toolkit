# Signal Clustering & Candidate Formation Guide

## Overview
Guides the Problem Evaluation agent in clustering unstructured or normalized research signals into distinct, non-overlapping candidate problems without artificial inflation or false merging.

---

## 1. The 4-Anchor Clustering Test
To determine whether two signals belong to the same candidate problem, evaluate the 4 operational anchors:

1. **Target Actor**: Is the human worker encountering the friction in the same operational role (e.g. accounts clerk vs warehouse picker)?
2. **Operational Trigger**: What specific business event initiates the activity (e.g. inventory quantity change vs order payout deposit)?
3. **Core Task**: What concrete operational sequence is being executed?
4. **Failure Mechanism**: Where and why does the breakdown occur (e.g. missing API sync vs manual spreadsheet re-keying)?

### Clustering Rule:
- If all 4 anchors align, group signals under a **single candidate problem** with multiple supporting signal IDs.
- If the trigger or task differs, separate them into **distinct candidates** even if they share keywords or products.

---

## 2. Anti-Patterns in Signal Clustering

### Anti-Pattern 1: Keyword Coincidence (False Merging)
- *Bad*: Grouping "inventory count mismatch" and "inventory purchase order delay" together because both mention "inventory".
- *Good*: Keeping them separate. Count mismatch is a Back-office Reconciliation issue; purchase order delay is a Multi-party Handoff issue.

### Anti-Pattern 2: Downstream Symptom Splitting (False Splitting)
- *Bad*: Creating Candidate 1 for "delayed invoicing" and Candidate 2 for "angry customer emails", when both stem from the identical failure of sales-to-billing handoff.
- *Good*: Merging into a single candidate focused on the sales-to-billing handoff failure, capturing invoicing delay and customer complaints as symptom expressions.

---

## 3. Candidate Problem Naming & Statement Formula
Format candidate titles and statements using neutral, non-sensational phrasing:

- **Candidate Ref**: `PC-001`, `PC-002` (temporary evaluation references).
- **Problem Title**: `[Operational Mode] + [Target Task] + [Core Friction]`
  - *Example*: "Manual Multi-Channel Inventory Synchronization"
- **Problem Statement**:
  $$\text{[Specific Actor]} + \text{may experience} + \text{[Operational Failure]} + \text{when performing} + \text{[Task]} + \text{in} + \text{[Context]}$$
  - *Example*: *"Ecommerce sellers with multi-channel storefronts may experience out-of-sync inventory levels when manually updating stock across marketplace seller dashboards."*
