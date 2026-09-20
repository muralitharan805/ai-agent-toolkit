---
name: problem-discovery
description: "Investigates real operational problems with traceable sources, forensic workflow mapping, evidence-gated research scoring, preregistered experiments, and CSV-first persistence."
metadata:
  dependencies: "Python >=3.10; optional manual field research and web access"
  framework_version: "Universal / Agnostic"
  last_verified_date: "2026-09-20"
---

# Universal Problem Discovery: Evidence Before Software

## Purpose and execution contract

Investigate **observed** operational problems, not speculative SaaS ideas. Distinguish candidate discovery, research priority, manually reviewed primary evidence and outcomes of small preregistered experiments. A high score, search result, source URL, spreadsheet, positive interview or LLM statement is **not** market validation. The bundled CLI does not search the internet or authenticate research participants: `--dorks` prints suggested queries only.

**Default output: one `discovery_matrix.csv` file for all candidates.** Each problem is one row, identified by stable `candidate_id`; update that row on later research instead of creating a dossier file per discovery. CSV stores the essential scoring/status columns and JSON-formatted cells for detailed 14-node workflow, evidence metadata, experiment contract and solution requirements. Record external source URLs and redacted evidence artifact paths; do not copy private research artifacts into the CSV or Git. Do not generate per-candidate Markdown unless the user explicitly asks for a full dossier. Legacy Markdown tools remain opt-in for existing vaults, not the source of truth for the CSV-first workflow.

Use the existing module (`shared/problem-discovery`) rather than generating a duplicate skill. Complete seven stages, recording known facts, unknowns and concrete next verification; leave incomplete stages unresolved. Valid outcomes include `UNVERIFIED`, `PARKED` and `EXPERIMENT_FAILED`.

## References and supporting tools

- [Evidence audit and structured experiment contract](references/evidence-audit-contract.md): machine-checkable integrity rules and human-review boundary.
- [14-node workflow and glue work](references/14-node-workflow-and-glue-work.md): Actor, Trigger, Input, Steps, Tools, Decisions, Handoffs, Delays, Rework, Errors, Output, Cost, Risk, Audit.
- [35-point scoring and WTP](references/35-point-evidence-scoring-and-wtp.md): seven 0–5 research dimensions and two tracks.
- [Interviewing and root causes](references/discovery-frameworks-and-interviewing.md): TRACE, FOCUS, counterfactuals, and historical behavior.
- [Complaint mining and query refinement](references/complaint-mining-and-dorking.md): web queries and independent-source corroboration.
- [Competitor and non-software alternatives](references/anti-opportunities-and-saturation-traps.md): actual workflow fit and switching cost.
- [Solo-builder solution choice](references/solo-builder-micro-saas-strategy.md): avoid SaaS without evidence of shared-state requirements.
- [Local and offline fieldwork](references/local-and-offline-discovery.md): consented observation and local constraints.
- [Small experiments](references/experiment-design-and-validation.md): preregistration, measured adoption, explicit failure rules.
- [CSV-first workflow](references/csv-first-workflow.md): one-file contract, commands, stable IDs, and optional legacy migration.
- `scripts/discovery_csv.py`: **primary command** — score JSON candidates and upsert one CSV without creating Markdown.
- `scripts/score_problem_candidate.py`: lower-level scorer; the `--export-obsidian` option writes individual Markdown dossiers **only when explicitly requested**.
- `scripts/export_discovery_matrix.py`: legacy one-time converter from existing Markdown dossiers to a CSV, not part of the normal CSV-first update path.
- `assets/scoring-matrix-schema.json`: structured candidate input contract.
- `assets/discovery-log-template.md`: optional long-form human dossier template.
- `evals/`: prompts and tests, not proof of actual customer demand.

## Seven-stage procedure

1. **Bound and track.** State operator, precise workflow, location, frequency, research budget and stable `candidate_id`. Choose `commercial` for WTP or `free_utility` for observed usefulness/accessibility; zero WTP does not disqualify a free utility.
2. **Mine and observe.** Search complaints, reviews and operators' actual work with provenance, observation dates and independent sources. Refine industry jargon and local-language queries. Obtain consent before local shadowing. Suggested queries are not executed searches.
3. **Deconstruct.** Map all fourteen workflow nodes and identify the broken handoff, existing workaround, inaction causes and cost. Keep detail in `workflow_14_nodes` (a JSON-formatted CSV cell); do not drop evidence merely to keep columns short.
4. **Audit alternatives.** Inspect competitors and non-software fixes against actual tasks, language, devices, offline access, price, and switching cost. If a checklist or spreadsheet adequately resolves the measured problem, record `non_software_sufficient`.
5. **Prioritize, not validate.** Record seven 0–5 scores and evidence **per claim**. Secondary evidence level 4 caps every score at 1; unvalidated level 5 forces all scores to zero. Stop checks park candidates. At 23–27 prioritize more shadowing; 28–35 prioritize a small trial. Even with 35/35, no manually audited primary evidence means `UNVERIFIED`.
6. **Preregister and measure.** Before the trial record dated hypothesis, metric, direction, threshold, failure rule and start time; afterwards record sample size, numeric observation, supporting artifact and named dated human review. Free-text `--experiment-outcome` cannot confer validation. A completed failing trial must remain `EXPERIMENT_FAILED`.
7. **Scope and persist in CSV.** Supply explicit `solution_constraints`: non-software sufficiency, interactive UI, batch automation, browser integration, multi-user sync, server storage, background jobs, and offline use. Unknown requirements mean undecided architecture. Upsert by candidate ID to **the same** `discovery_matrix.csv`; preserve existing candidates and analyst notes. Do not auto-generate Markdown dossiers or silently write to a personal Obsidian path.

## Output and review gates

Each CSV row must retain: stable ID, actor/problem and 14-node mapping, independent evidence source URLs and dates, per-claim artifact paths/hashes/manual-review details, all seven scores, evidence and experiment flags, explicit status, alternate solutions, trial contract and result or `NOT_RUN`, requirements-driven solution format, unknowns and next verification. The scorer validates only local file integrity and supplied reviewer metadata, **not** authenticity of a customer, screenshot or experiment; a human must independently review underlying claims.

Run from the skill `scripts/` directory or invoke the script with an absolute path:

```bash
# Generate a query list only (no browsing):
python3 score_problem_candidate.py --dorks "textile reconciliation"

# ONE CSV file for any number of candidates. Run again with the same ID to UPDATE its row:
python3 discovery_csv.py --input-json candidate.json --output ./discovery_matrix.csv
python3 discovery_csv.py --input-json next_candidates.json --output ./discovery_matrix.csv

# Optional legacy export ONLY when long-form Markdown dossiers are explicitly requested:
python3 score_problem_candidate.py --input-json candidate.json --export-obsidian ./legacy_dossiers
```

For one candidate supply `evidence_records`, `experiment`, `solution_constraints`, and optional `workflow_14_nodes` / `research_notes` in the input JSON. For a batch supply an array of candidate objects with **unique IDs**. `discovery_csv.py` refuses to overwrite a CSV whose header does not match its schema, preserving any pre-existing legacy/hand-edited CSV for explicit migration. It can store JSON-formatted detail cells without generating auxiliary JSON output files; the `--input-json` file is caller-supplied input, not a per-candidate dossier created by the tool.

## Gotchas and failure paths

- **CSV is a research register, not a verifier.** Editing status or evidence cells in a spreadsheet cannot establish real-world validation; re-run the evidence-gated scorer and manually audit any claim before publishing it.
- **No evidence, no validation.** Score 35/35 + one source URL + a positive free-text outcome remains `UNVERIFIED`.
- **Integrity is not truth.** A file hash verifies bytes only. Reviewer names, observations and dates are supplied data to cross-check independently.
- **No post-hoc experiment goalposts.** Document thresholds before the trial; compare outcomes against exactly that preregistration.
- **Rank is research priority.** A trial can fail despite a high score; preserve the actual validation status in the CSV.
- **No arbitrary SaaS.** Unknown solution constraints leave the format undecided; documented non-software sufficiency points to a template.
- **Safety of sources.** Obtain consent, redact sensitive identifiers, and store evidence in a secure local folder outside Git. CSV contains pointers and summaries, not raw confidential data.
- **One candidate, one row.** Keep IDs stable to avoid duplicates; never overwrite an incompatible or legacy CSV without explicit conversion and backup.
- **Legacy notes are opt-in.** A dossier-generated CSV is not automatically synchronized with the CSV-first register. If old Markdown logs exist, review and migrate them once rather than running both workflows concurrently.
