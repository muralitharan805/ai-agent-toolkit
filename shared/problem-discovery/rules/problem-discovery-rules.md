---
description: "Requires traceable problem evidence, separate research and validation states, preregistered experiments, and a single CSV-first research ledger."
trigger: model_decision
framework_version: "Universal / Agnostic"
last_verified_date: "2026-09-20"
---

# Problem Discovery: Evidence and Experiment Rules

## Description

Enforces evidence, experiment, solution and CSV-first persistence boundaries for the `problem-discovery` skill. A score prioritizes further research; it does not prove market demand.

## Constraints

### Non-negotiable evidence boundaries

1. A complaint is a signal, **not proof** of recurring operational pain. AI-generated ideas, survey hypotheticals, forum JSON and unchecked URLs are not primary behavioral evidence. Record provenance, observation date, evidence level, uncertainty and next verification per claim. Never invent interviews, competitor research, field visits, citations or audits. `--dorks` only suggests searches; it does not browse.
2. Maintain separate **research score**, **primary evidence audited**, **experiment completed**, **experiment passed** and **validation** states. A high score alone is high research priority. `VALIDATED` requires primary evidence, a preregistered trial meeting the numeric threshold, and a reviewed local outcome artifact. Free-text outcomes, score, raw source strings and unreviewed files cannot establish validation.
3. SHA-256 verifies artifact bytes, not source authenticity, representativeness or truth. A human must inspect the underlying observation, redact sensitive data, and record claim, observed date, reviewer, review date and digest. Without independent checks, refer only to locally audited/user-supplied evidence.
4. State known facts, unknowns and concrete next verification at each stage. Unperformed interviews, alternative checks, root-cause research and experiments remain `NOT_RUN` or `UNVERIFIED`.

### Research evaluation procedure

Follow `skills/SKILL.md`: scope/track -> signals -> fourteen workflow nodes -> alternative audit -> 35-point research prioritization -> preregistered small trial -> smallest suitable solution and **CSV-first persistence**.

- Commercial research tracks demonstrated historical spend and buyer autonomy; free utility tracks repeated usefulness/accessibility without a required WTP.
- Evidence levels: L1 direct behavioral observation, L2 primary operator interview, L3 independently corroborated complaints, L4 secondary reports, L5 hypotheses. Cap each L4 scoring dimension at 1 and L5 at 0; scores without reviewed primary artifacts are not observed proof.
- Stop checks can park low-impact, already-solved, biased, training-related or unreachable candidates. Missing workaround requires inaction-root-cause analysis; do not reject based on a competitor keyword alone.
- Audit tools against real workflow, language, devices, offline need and switching friction. If a checklist, spreadsheet or SOP adequately addresses the problem, record `non_software_sufficient: true`.
- A trial requires dated preregistration, numeric metric/threshold/direction, failure rule, period, sample size, numeric result, local artifact and dated named human review. A measured miss is `EXPERIMENT_FAILED`; missing or unauditable information cannot produce `VALIDATED`.
- Select technical format from explicitly observed `solution_constraints`, not title/domain keywords. Unknown requirements -> undecided architecture; no invented pricing. Human technical/security review remains necessary.

### Persistence and reporting

- **Default: one `discovery_matrix.csv` file for the whole discovery project.** Use `skills/scripts/discovery_csv.py --input-json candidates.json --output /path/to/discovery_matrix.csv`. One stable candidate ID -> one row; upsert updates that row and preserves unrelated candidates. Store the fourteen-node workflow, evidence metadata, experiment and constraints as JSON-formatted cells when necessary, with useful filterable status and score columns. Do not create a Markdown file per candidate by default.
- Keep sensitive supporting evidence outside Git/CSV and store redacted references and manual-review metadata. CSV content is not independent verification: do not elevate a status by manually editing cells.
- Existing `--export-obsidian` and Markdown-to-CSV regeneration are **opt-in legacy modes only** when explicitly requested. Never run the CSV-first updater and Markdown-based CSV rebuild against the same output file; a mismatched existing CSV header must be preserved, backed up and migrated deliberately.
- Do not hardcode developer home directories or report nonexistent vault writes. Preserve status/evidence/experiment flags separately from 35-point research score; never promote a high-scoring legacy candidate to `VALIDATED` by score.

## Examples

- **33/35, no audited primary file:** several forum URLs and "customers liked it" -> `UNVERIFIED`.
- **30/35, reviewed operator register, no trial:** `RESEARCH_PRIORITY`; preregister a small experiment.
- **Trial misses threshold:** record `EXPERIMENT_FAILED` regardless of score.
- **Checklist adequately resolves observed task:** choose template/SOP, not SaaS.
- **Twenty discovered problems:** one 20-row CSV, zero per-candidate Markdown files; update an existing ID in place when new research is collected.
