---
description: "Enforces preregistered experiment immutability, objective threshold evaluation, evidence artifact hashing, and SQLite experiment lifecycle contracts."
trigger: model_decision
framework_version: "1.0.0"
last_verified_date: "2026-09-26"
---

# Experiment Validation & Empirical Preregistration Rules

## Description
This rule governs the Experiment Validation stage across the problem discovery lifecycle. It enforces strict empirical discipline: converting evaluated problem candidates into measurable, preregistered experiment contracts (`DESIGN` mode) and evaluating actual observed trial results against immutable thresholds (`ASSESS` mode). It prevents post-hoc goalpost shifting, separates problem behavior observation from commercial willingness to pay, mandates SHA-256 evidence artifact digests with human review verification, and governs the SQLite `experiments` table persistence contract.

## Constraints

### 1. Dual Mode Separation & Scope Boundary
- The Experiment Validation capability MUST operate in exactly one of two distinct modes:
  - `DESIGN` Mode: Ingests `ProblemEvaluation` and outputs an `ExperimentContract`.
  - `ASSESS` Mode: Ingests `ExperimentContract` + observed participant data + artifact metadata and outputs `ValidationAssessment`.
- The agent is STRICTLY FORBIDDEN from performing live internet research, fabricating participant observations, executing real-world trials autonomously, or designing final software UI/architecture.

### 2. Candidate Readiness Gate
- Before designing an experiment, the agent MUST verify that the candidate problem is well-defined:
  - Target operator, trigger, and core workflow sequence must be established.
  - Basic research questions must be resolved (no fundamental workflow unknowns).
  - Stop checks must be clear (candidate not parked due to existing adequate solutions).
- If the problem definition is vague or unverified, the agent MUST return `status: "NOT_READY"` with `next_action: "REQUEST_MORE_EVIDENCE"`. Designing experiments for unready candidates is prohibited.

### 3. Preregistration Immutability Invariant
- Once an `ExperimentContract` is registered, the following fields become strictly immutable:
  1. `hypothesis`, 2. `population`, 3. `primary_metric`, 4. `direction`,
  5. `success_threshold`, 6. `failure_rule`, 7. `sample_target`,
  8. `minimum_usable_sample`, 9. `observation_period`.
- **Zero Post-Hoc Adjustments**: Lowering a threshold after observing data (e.g. changing threshold from 3 to 2.5 because only 2.5 was achieved) is STRICTLY PROHIBITED.
- If a material change to the experiment protocol is required:
  - The original experiment MUST be marked `status: "INVALID"` or `"CANCELLED"`.
  - A new experiment record MUST be created with a distinct `experiment_id`.
  - History MUST NEVER be rewritten or overwritten.

### 4. Primary Metric & Explicit Failure Rule Standard
- Every experiment MUST define exactly one primary numeric or observable metric. Secondary metrics may be monitored but MUST NEVER be substituted post-hoc to declare success.
- Success and failure MUST be defined symmetrically before execution:
  - Direction: Explicit operator (`>=`, `<=`, `>`, `<`, `==`).
  - Failure Rule: Explicit condition under which the hypothesis is rejected.
- Vague success metrics (e.g., "users liked the concept", "participants were receptive") are STRICTLY FORBIDDEN.

### 5. Evidence Artifact Digest & Named Human Audit
- Every empirical assessment MUST reference a physical evidence artifact (e.g., CSV observation log, timestamped transaction exports).
- A valid SHA-256 hexadecimal digest (64 characters) of the artifact MUST be recorded.
- **Human Review Requirement**: A file hash proves only local byte integrity, NOT factual authenticity. Every valid trial MUST include:
  - `audited_by`: Verifiable name of the human reviewer who validated the observations.
  - `audit_date`: ISO-8601 date of verification ($\le$ today).
- In the absence of human review metadata, the assessment MUST NOT be granted `VALIDATED` status.

### 6. Validation Scope Separation Invariant
- A passed experiment proves ONLY the specific claim it was preregistered to test.
- The agent MUST keep the 5 validation scopes explicitly separated:
  1. `problem_behavior_observed`: Did the target friction occur in the sample?
  2. `market_demand_validated`: Is there evidence of widespread market demand?
  3. `willingness_to_pay_validated`: Did operators commit real financial payment?
  4. `solution_adoption_validated`: Did operators actively adopt the intervention?
  5. `retention_validated`: Did operators continue using the intervention over time?
- A passed behavior-frequency experiment MUST NEVER set `willingness_to_pay_validated: true` or `market_demand_validated: true`.

### 7. Failure Preservation & Incomplete Classification
- If observed data misses the threshold, the experiment MUST be classified as `EXPERIMENT_FAILED`.
- A failed experiment MUST NEVER be overridden or called "promising" because the candidate had a high prior research score.
- **Incomplete Sample Gate**: If usable sample size falls below `minimum_usable_sample`, the experiment MUST be classified as `INCOMPLETE`, NOT `EXPERIMENT_FAILED` (unless the failure rule explicitly governs attrition).

### 8. SQLite Experiment Persistence Contract
- **DESIGN Mode**: Insert record into `experiments` with `outcome_verdict = 'NOT_RUN'` and set candidate `lifecycle_status = 'EXPERIMENT_DESIGNED'`:
  ```sql
  INSERT INTO experiments (
      experiment_id, candidate_id, hypothesis, metric_name, target_threshold,
      direction, sample_target, outcome_verdict, contract_json
  ) VALUES (
      :experiment_id, :candidate_id, :hypothesis, :metric_name, :target_threshold,
      :direction, :sample_target, 'NOT_RUN', :contract_json
  );
  UPDATE candidates SET lifecycle_status = 'EXPERIMENT_DESIGNED', updated_at = CURRENT_TIMESTAMP WHERE candidate_id = :candidate_id;
  ```
- **ASSESS Mode**: Update `experiments` record with observed outcomes, artifact hash, and reviewer metadata:
  - If Passed: Update candidate `validation_status = 'VALIDATED'` and `lifecycle_status = 'READY_FOR_SOLUTION'`.
  - If Failed: Update candidate `validation_status = 'EXPERIMENT_FAILED'` and `lifecycle_status = 'PARKED'`.
- Deleting failed experiment records is STRICTLY FORBIDDEN.

## Examples

### 1. Post-Hoc Threshold Modification vs. Honest Failure
```text
❌ FORBIDDEN (Goalpost shifting after results):
Contract: Success defined as >= 4 orders reconciled manually per week (Sample: 10 sellers).
Observed Result: Only 2 sellers reached 4 reconciliations; average was 2.8.
Agent Assessment: Adjusts threshold to 2.5 and declares experiment PASSED.

✅ CORRECT (Strict failure preservation):
Contract: Success defined as >= 4 orders reconciled manually per week (Sample: 10 sellers).
Observed Result: 2 of 10 sellers reached 4 reconciliations.
Agent Assessment:
- Verdict: EXPERIMENT_FAILED
- Reason: Threshold of 4 reconciliations met by only 2 of 10 sellers (Target was >= 7 of 10).
- Candidate Status: Updated to PARKED.
- Next Action: REVIEW_HYPOTHESIS_OR_SEGMENT.
```

### 2. Validation Scope Separation
```text
❌ FORBIDDEN (Over-claiming validation scope):
Experiment Target: Behavior Frequency (Tracking manual spreadsheet edits).
Observed: 5 of 5 merchants edited spreadsheets daily -> PASS.
Agent Conclusion: "Market demand and commercial SaaS willingness to pay are now validated!"

✅ CORRECT (Strict scope boundary):
Experiment Target: Behavior Frequency.
Observed: 5 of 5 merchants edited spreadsheets daily -> PASS.
Agent Assessment:
- problem_behavior_observed: true
- market_demand_validated: false (Unverified beyond tested 5-seller cohort)
- willingness_to_pay_validated: false (No payment experiment conducted)
- Supported Claim: Repeated manual spreadsheet edits occurred in observed cohort.
- Next Action: Design willingness-to-pay or solution concierge experiment.
```
