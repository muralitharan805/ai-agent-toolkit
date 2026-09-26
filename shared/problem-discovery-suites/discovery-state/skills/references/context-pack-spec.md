# Dynamic Context Pack Specification Reference

## Purpose
This document provides the authoritative specification for **Dynamic Context Packs** assembled by `build_agent_context.py`. Context Packs solve three critical failure modes in multi-agent reasoning:
1. **SQL Token Bloat**: Reasoning agents never see DDL statements, schemas, or raw table structures.
2. **Counting Hallucinations**: Quantitative distributions (signal totals, platform counts, experiment results) are computed deterministically in Python.
3. **Chat History Dependency**: Every agent can be invoked in a zero-history, isolated turn with a self-contained, fully hydrated context pack.

---

## Context Pack Tasks & Specifications

### 1. `PROBLEM_EVALUATION` Context Pack
Assembled when research signals have been gathered under a `research_id` and must be evaluated into problem candidates.

```json
{
  "schema_version": "1.0",
  "task": "PROBLEM_EVALUATION",
  "research_run": {
    "research_id": "run_2026_001",
    "domain": "ecommerce_logistics",
    "scope_type": "NARROW",
    "original_request": "Explore Indian D2C courier weight discrepancy disputes"
  },
  "research_plan": {
    "streams": [
      {
        "stream_id": "RS-001",
        "name": "Courier Weight Disputes",
        "operators": ["dispatch_manager", "accounts_executive"]
      }
    ],
    "unknowns": ["Target geography", "Monetary loss per shipment"]
  },
  "signals": [
    {
      "signal_id": "sig_001",
      "stream_id": "RS-001",
      "platform": "REDDIT",
      "source_url": "https://reddit.com/r/ecom/comments/xyz123",
      "actor_role": "D2C Brand Owner",
      "reported_issue": "Courier charged 1.5kg for 400g t-shirt packet",
      "reported_workaround": "Manual Excel VLOOKUP matching SKU weights vs courier bills",
      "evidence_level": "L3"
    }
  ],
  "deterministic_summary": {
    "total_signals": 1,
    "platform_breakdown": { "REDDIT": 1 },
    "evidence_level_distribution": { "L1": 0, "L2": 0, "L3": 1, "L4": 0, "L5": 0 }
  },
  "existing_candidate_matches": [],
  "constraints": {
    "do_not_search_web": true,
    "max_allowed_evidence_score_per_dim": 3,
    "enforce_14_nodes": true
  }
}
```

---

### 2. `EXPERIMENT_VALIDATION` Context Pack
Assembled when a candidate is ready for preregistered experiment design (DESIGN mode) or trial outcome assessment (ASSESS mode).

```json
{
  "schema_version": "1.0",
  "task": "EXPERIMENT_VALIDATION",
  "mode": "DESIGN",
  "candidate": {
    "candidate_id": "cand_courier_disputes",
    "title": "Courier Weight Dispute Reconciliation",
    "domain": "ecommerce_logistics",
    "target_operator": "accounts_manager",
    "research_score": 28,
    "evidence_level": "L3",
    "validation_status": "UNVERIFIED"
  },
  "evaluation_summary": {
    "observed_costs": "15 hrs/wk manual Excel reconciliation",
    "core_friction": "4-day strict dispute window with courier partner",
    "current_glue_work": "Manual copy-paste into courier dispute portal"
  },
  "deterministic_summary": {
    "total_supporting_signals": 6,
    "prior_experiments_count": 0
  },
  "constraints": {
    "require_immutable_threshold": true,
    "single_primary_metric_only": true,
    "require_symmetrical_failure_rule": true
  }
}
```

---

### 3. `SOLUTION_STRATEGY` Context Pack
Assembled when an evaluated and validated candidate is ready for solution class gating.

```json
{
  "schema_version": "1.0",
  "task": "SOLUTION_STRATEGY",
  "candidate": {
    "candidate_id": "cand_courier_disputes",
    "research_id": "run_2026_001",
    "title": "Courier Weight Dispute Reconciliation",
    "domain": "ecommerce_logistics",
    "target_operator": "accounts_manager",
    "research_score": 28,
    "evidence_level": "L3",
    "validation_status": "VALIDATED",
    "lifecycle_status": "READY_FOR_SOLUTION"
  },
  "experiments_summary": {
    "total_trials": 1,
    "passed": 1,
    "failed": 0,
    "latest_trial": {
      "experiment_id": "exp_weight_001",
      "metric_name": "csv_submissions",
      "target_threshold": 3.0,
      "observed_value": 4.0,
      "outcome_verdict": "VALIDATED",
      "audited_by": "Murali"
    }
  },
  "constraints": {
    "enforce_non_software_first": true,
    "enforce_15_operational_flags": true,
    "gate_saas_speculation": true,
    "require_sts_under_14_days": true
  }
}
```
