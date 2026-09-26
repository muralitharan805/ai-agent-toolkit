# Root Cause Analysis & Diagnostic Separation

## Overview
Establishes diagnostic boundaries between symptoms, workarounds, proximate mechanisms, and unverified root-cause hypotheses.

---

## 1. The 4-Tier Diagnostic Hierarchy

Confusing an observable workaround with a root cause leads directly to building redundant software that fails to solve the real problem.

```text
Tier 1: Reported Symptom   ("We oversell stock twice a week.")
        │
        ▼
Tier 2: Workaround         ("Clerk manually checks each channel every morning.")
        │
        ▼
Tier 3: Proximate Cause    ("Channel A and Channel B operate on independent inventories.")
        │
        ▼
Tier 4: Root Cause         ("No unified webhook or real-time event pipeline exists between channels.")
```

---

## 2. Invariants for Root Cause Formulation

1. **Workaround $\neq$ Root Cause**:
   - An operator maintaining an Excel spreadsheet is an observable workaround, NOT the root cause. The root cause is why the primary enterprise systems cannot exchange data.
2. **Root Cause Status**:
   - Unless primary architectural or API evidence is in hand, the root cause MUST be declared with `status: "UNVERIFIED"` containing explicit hypotheses.
3. **Multi-Hypothesis Mapping**:
   - Frame multiple plausible root causes rather than assuming a single narrative. For example:
     - Hypothesis A: Software exists, but subscription cost exceeds operator budget.
     - Hypothesis B: Software exists, but regional tax compliance is unsupported.
     - Hypothesis C: Marketplace APIs rate-limit real-time balance queries.
