# Experiment Readiness & Pre-Flight Gate Guide

## Overview
Ensures that experiments are only designed for well-defined problem candidates, preventing wasted effort on ill-conceived or premature trials.

---

## 1. Readiness Audit Checklist

Before transitioning a candidate from `problem-evaluation` to `experiment-validation`, verify the 5 pre-flight gates:

1. **Clear Target Population**: Is the operator persona unambiguous (e.g., "SMB Shopify merchant with 2+ stores", not "anyone in retail")?
2. **Established Core Workflow**: Has the 14-node workflow mapped the trigger, steps, and existing workaround without critical structural gaps?
3. **Falsifiable Behavior**: Does the claimed friction involve observable human actions (clicks, spreadsheet edits, manual reconciliations) that can be measured?
4. **Resolved Contradictions**: Have major contradictory signals been addressed or scoped to specific operator segments?
5. **No Active Stop Checks**: Has the candidate avoided being flagged for adequate existing alternatives or low impact?

---

## 2. Readiness Status Classifications

- `READY`: All 5 gates pass. Proceed with `DESIGN` mode.
- `PARTIALLY_READY`: Problem is real, but eligibility criteria or primary metric needs refinement.
- `NOT_READY`: Critical workflow or actor gaps remain. Emit `status: "NOT_READY"` and return `next_action: "REQUEST_MORE_EVIDENCE"`.
