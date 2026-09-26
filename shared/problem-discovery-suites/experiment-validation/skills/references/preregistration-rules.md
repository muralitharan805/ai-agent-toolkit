# Experiment Preregistration & Immutability Rules

## Overview
Defines the strict preregistration locking mechanism that eliminates researcher bias, retrospective threshold adjustments, and goalpost shifting.

---

## 1. The Preregistration Lock Contract

Before data collection starts, the experiment record must be frozen with `preregistration_locked: true`.

### Immutable Fields:
1. `hypothesis`
2. `population.inclusion_criteria` and `exclusion_criteria`
3. `primary_metric.name` and `unit`
4. `success_threshold` and `direction`
5. `failure_rule`
6. `sample.target` and `sample.minimum_usable`
7. `period.duration_days`
8. `artifact_requirements.expected_type`

---

## 2. Managing Material Protocol Changes
If a researcher realizes midway through an experiment that the metric, sample criteria, or threshold must change:
1. **Never edit the existing contract.**
2. Mark the active experiment as `outcome_verdict = 'CANCELLED'` or `'INVALID'`.
3. Document the rationale for cancellation in `assessment_json`.
4. Issue a new experiment contract with a sequential ID (e.g. `EXP-002`) and fresh preregistration timestamp.
