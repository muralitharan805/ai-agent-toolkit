# Primary Metric & Failure Rule Design

## Overview
Establishes principles for defining unambiguous primary metrics, success directions, and symmetrical failure rules before trial launch.

---

## 1. Single Primary Metric Rule
- Every trial must designate **exactly one** primary metric that directly tests the core hypothesis.
- Secondary metrics (e.g. participant satisfaction, qualitative quotes) provide context but CANNOT be used to declare success if the primary metric fails.

---

## 2. Threshold Operators & Symmetrical Rules

| Direction Operator | Mathematical Meaning | Example Application |
|---|---|---|
| `>=` | Greater than or equal to | Minimum frequency or conversion target |
| `<=` | Less than or equal to | Maximum tolerable error rate or cost |
| `>` / `<` | Strictly greater / less than | Outperforming a strict historical baseline |
| `==` | Exact match | Binary milestone achievement |

### Symmetrical Rule Structure:
- **Success Rule**: State exact condition required to pass.
  - *Example*: *"At least 3 of 5 eligible sellers must log $\ge 3$ manual sync events over 7 days."*
- **Failure Rule**: Explicit statement of what constitutes rejection.
  - *Example*: *"Fail if fewer than 3 of 5 eligible sellers achieve $\ge 3$ manual sync events."*
