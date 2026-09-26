# Outcome Assessment & Decision Classification Guide

## Overview
Guides the ASSESS mode execution logic in evaluating observed participant data against immutable contracts.

---

## 1. Step-by-Step Assessment Protocol

1. **Verify Preregistration Existed**: Verify `preregistration_locked: true` and timestamp prior to data collection.
2. **Verify Usable Sample Gate**:
   - $\text{usable\_sample} \ge \text{minimum\_usable\_sample}$ $\rightarrow$ Valid sample.
   - $\text{usable\_sample} < \text{minimum\_usable\_sample}$ $\rightarrow$ Emit status `INCOMPLETE`.
3. **Audit Verification Check**: Verify presence of local artifact path, valid 64-char SHA-256 hash, and named reviewer metadata.
4. **Evaluate Primary Threshold**: Compare observed numbers against the locked rule.
5. **Classify Final Status**:
   - `EXPERIMENT_PASSED`: All success criteria satisfied.
   - `EXPERIMENT_FAILED`: Failed to meet primary threshold.
   - `INCOMPLETE`: Participant attrition or observation interrupted.
   - `INVALID`: Contract violated or unverified data source.

---

## 2. Incomplete vs. Failed Distinction
- An experiment that achieves 3 participants out of a target of 5 is `INCOMPLETE`, NOT failed.
- Do NOT declare failure if the minimum sample size was never reached, unless participant refusal was explicitly part of the failure rule.
