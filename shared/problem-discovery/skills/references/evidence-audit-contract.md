# Evidence audit and experiment contract

The CLI is a **local integrity gate**, not an online fact checker. An LLM, source URL, numerical score, or JSON `verified: true` cannot confirm that customers have a problem. A named researcher must inspect an actual observation or interview artifact and judge whether its contents support the **specific claim**. The digest below protects the artifact against accidental changes after review; it does not prove the artifact or reviewer is genuine. Do not store personal identifiers in public Git repositories.

## Required progression

`SIGNAL -> RESEARCH_PRIORITY -> PRIMARY_EVIDENCE_REVIEWED -> PREREGISTERED_TRIAL -> OBSERVED_METRIC -> VALIDATED / EXPERIMENT_FAILED / UNVERIFIED`.

A research score can rank what to investigate, not infer human habit change. An observed trial that misses its predefined threshold is an explicit failed experiment, not a success reframed after the fact. Keep `evidence_verified`, `experiment_completed`, `experiment_passed`, `status`, `classification`, and `total_score` distinct in results and CSV. Never elevate an old `TIER-1 GOLD` note to `VALIDATED` from a score.

## Example candidate.json

Save a **redacted** observation in a local file; calculate its hash with `sha256sum /secure/research/observation.csv`. Replace the sample paths, digest, dates, reviewer, metric and scores with real material. Do not use the placeholders as evidence.

```json
{
  "id": "PROB-EXAMPLE-001",
  "title": "Example handoff mismatch",
  "domain": "Manufacturing",
  "track": "commercial",
  "evidence_level": 1,
  "scores": {
    "frequency": 4,
    "severity": 4,
    "workaround": 4,
    "wtp": 3,
    "decision_maker": 4,
    "feasibility": 4,
    "discrepancy": 4
  },
  "stop_checks": {},
  "evidence_sources": ["Interview provenance and independent issue URLs (not proof by themselves)"],
  "evidence_records": [{
    "level": 1,
    "claim": "Operator reconciled two registers by hand during the observed week",
    "observed_on": "2026-09-14",
    "artifact_path": "/secure/research/observation.csv",
    "sha256": "REPLACE_WITH_ACTUAL_SHA256",
    "reviewed_by": "Researcher name",
    "reviewed_on": "2026-09-15"
  }],
  "solution_constraints": {
    "needs_interactive_ui": true,
    "needs_multi_user_sync": false,
    "needs_server_storage": false,
    "needs_background_jobs": false,
    "offline_required": true,
    "notes": "Operator uses a shared low-end phone; verify during pilot."
  }
}
```

With **audited primary evidence but no experiment**, even 35/35 remains `RESEARCH_PRIORITY`. A `--evidence-source` URL or `--evidence-artifact` path on its own cannot pass the audit. Level 2 claims need a dated interview transcript or record which the reviewer actually examined. Level 3 forum JSON and review summaries stay corroborated sentiment, even when downloaded as files.

## Experiment contract: add `experiment` to the candidate after preregistration

```json
{
  "hypothesis": "At least three of five operators use the output twice",
  "metric": "operators_with_two_uses",
  "failure_rule": "If fewer than three repeat, revise or park; do not build backend",
  "direction": "at_least",
  "success_threshold": 3,
  "preregistered_on": "2026-09-15",
  "started_on": "2026-09-16",
  "ended_on": "2026-09-20",
  "sample_size": 5,
  "observed_value": 3,
  "artifact_path": "/secure/research/pilot-redacted.csv",
  "sha256": "REPLACE_WITH_ACTUAL_SHA256",
  "reviewed_by": "Researcher name",
  "reviewed_on": "2026-09-20"
}
```

The CLI requires ordered ISO dates, a finite numeric result, a nonzero sample, a named dated manual review, and an existing matching local artifact. The only supported directional comparisons are `at_least` and `at_most`. A self-attested JSON contract or passing numbers are **not independently verified market demand**; a human must check that the artifact really counts the declared metric for the declared sample and trial period, and that preregistration occurred before the trial. Store the original signed preregistration separately if authenticity matters; this CLI does not verify external timestamps or signatures.

## CLI operation

```bash
cd shared/problem-discovery/skills/scripts
python3 score_problem_candidate.py --input-json /path/to/candidate.json --json \
  --export-obsidian /path/to/discovery_logs
python3 export_discovery_matrix.py --dir /path/to/discovery_logs
```

`--evidence-json /path/to/audit.json` can supply `evidence_records`, `experiment` and `solution_constraints` with original single-candidate CLI flags. An unreviewed, missing, tampered, or remotely hosted file leaves the candidate `UNVERIFIED`; a passed numerical trial plus reviewed artifact yields `VALIDATED` as a **locally audited result**, not an independent certification. A trial failing its registered numeric threshold is `EXPERIMENT_FAILED`. If `--export-obsidian` is absent, the CLI prints its result and writes no notes; if the destination is unavailable, it must return an error, not a simulated success.

## Architecture constraints

`non_software_sufficient: true` -> template/SOP. Otherwise server storage, multi-user shared state or background jobs -> hosted Micro-SaaS; browser page integration -> extension; local headless batch -> CLI; standalone interactive client UI -> static utility. Unresolved requirements -> `null` solution, **not** default Micro-SaaS. Offline requirement alone must be recorded and checked against the proposed format; it does not imply a backend. These are scoping hypotheses subject to human review, security, distribution, and operating-cost analysis.
