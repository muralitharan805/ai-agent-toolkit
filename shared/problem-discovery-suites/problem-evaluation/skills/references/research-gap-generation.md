# Research Gap Detection & Request Generation

## Overview
Defines how the Problem Evaluation agent detects missing knowledge and packages structured `research_requests` back to `evidence-research`.

---

## 1. Triggering Research Requests
Instead of performing web searches, the evaluation agent detects gaps across:
- **Frequency Gaps**: Friction is known, but repetition rate is unmeasured.
- **Financial/Impact Gaps**: Time loss is claimed, but dollar impact or error rate is unknown.
- **Alternative Fit Gaps**: Incumbent tools exist, but reasons for operator non-adoption are unverified.
- **Root-Cause Gaps**: Observable symptom is proven, but architectural cause is hypothetical.

---

## 2. Research Request Schema
Every detected gap must be formulated into an actionable query request:

```json
{
  "request_id": "RR-001",
  "priority": "HIGH",
  "reason": "Existing synchronization tool workflow fit is unknown",
  "question": "Why do SMB merchants on Shopify avoid native multi-location inventory features?",
  "target_evidence": [
    "Shopify app store reviews",
    "G2 negative reviews",
    "Seller forum discussions regarding multi-location limits"
  ]
}
```
