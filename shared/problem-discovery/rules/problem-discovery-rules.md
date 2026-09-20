---
description: "Requires traceable problem evidence, distinct research-priority and validation states, preregistered experiments, and explicit solution requirements."
trigger: model_decision
framework_version: "Universal / Agnostic"
last_verified_date: "2026-09-20"
---

# Problem Discovery: Evidence and Experiment Rules

## Description

Enforces the research/evidence/experiment boundaries of the `problem-discovery` procedural skill. Applies when discovering, scoring or evaluating software opportunities; a score ranks further investigation, not proven market demand.

## Constraints

### Non-negotiable evidence boundaries

1. A complaint is a **signal**, not proof of observed recurring operational pain. An AI-generated idea, survey hypothetical, forum JSON tree, or unchecked source URL is **not** primary behavioral evidence. Label each claim with provenance, observation date, evidence level, uncertainties and next verification. Never invent interviews, competitor research, citations, field visits or file audits. The bundled CLI `--dorks` prints query suggestions; it does not search the web.
2. Preserve separate states for **research score**, **primary evidence audited**, **experiment completed**, **experiment passed** and **validation**. A high score is high research priority only. A `VALIDATED` outcome requires primary evidence and a preregistered trial that meets a recorded numeric metric/failure rule, plus reviewed local outcome artifact. Free-text `--experiment-outcome`, score alone, raw source strings and unreviewed artifacts cannot establish validation.
3. A SHA-256 digest proves only that reviewed file bytes match a recorded digest. It does **not** prove source authenticity, representativeness, or that the claim follows from the file. A human must actually examine the underlying observation, redact personal data, and record the claim, observation date, reviewer, review date and digest. When reviewer identity or observations cannot be independently checked, call the result locally audited/user-supplied, not externally certified.
4. For every stage report: known facts, unknowns and the concrete verification step. Never silently skip interviews, alternative checks, root-cause investigation or experiments. Mark unavailable steps `NOT_RUN` or `UNVERIFIED`.

### Research evaluation procedure

Follow the seven stages in `skills/SKILL.md`: target/domain/track -> signal mining -> fourteen-node workflow reconstruction -> existing/non-software alternatives -> 35-point **research** score -> preregistered small experiment -> smallest solution with saved dossier.

- Commercial track evaluates historical spend, buyer autonomy, recurrent pain and economic consequence; free-utility track evaluates accessibility, repeated usefulness and time saved, without penalizing zero willingness to pay.
- Evidence levels: L1 directly observed behavior; L2 dated primary operator interview; L3 corroborated independent reviews/forums (including JSON comment trees); L4 secondary reports; L5 hypotheses. L4 dimension scores cap at 1; L5 at 0. Numbers without reviewed primary artifacts are not evidence of observed behavior.
- Stop checks may park low-impact, already-solved, biased, policy/training-related or unreachable candidates. No workaround needs inaction-root-cause analysis, not automatic rejection. Do not reject a domain solely because a competitor keyword appears: inspect task and local market fit.
- Inspect existing tools for exact workflow, language, device, offline access and switching friction. If a spreadsheet/checklist/WhatsApp SOP adequately addresses the measured friction, set `non_software_sufficient: true` and stop at that fix.
- Experiment prerequisites: dated preregistered hypothesis, numeric metric and threshold/direction, failure rule, period, sample size, observed result, local artifact and dated named human review. A result below threshold is `EXPERIMENT_FAILED`. Absent, contradictory or unauditable information cannot be `VALIDATED`.
- Select technical format from observed `solution_constraints` (non-software fix, interactive UI, local batch, page integration, shared state, server storage, background jobs and offline need). Unknown requirements -> undecided architecture. No keyword-based default Micro-SaaS or imaginary pricing. Human technical/security review is required for the final scope.

### Persistence and reporting

Write dossiers only to an explicitly requested accessible directory using `--export-obsidian /path/to/discovery_logs`, and rebuild its CSV. Do not hardcode a developer's home folder. CSV retains real `validation_status`, `evidence_verified`, `experiment_completed` and `experiment_passed` separately from score. Never promote high-scoring unaudited legacy notes to `VALIDATED` or report a write to an unavailable vault.

## Examples

- **High score, no primary audited file:** 33/35 + several forum URLs + "customers liked the idea" -> `UNVERIFIED`, not `VALIDATED`.
- **Observed primary artifact but no trial:** 30/35 + manually reviewed register -> `RESEARCH_PRIORITY`; preregister a small field test.
- **Reviewed trial misses preregistered threshold:** record `EXPERIMENT_FAILED` and revise or park, regardless of score.
- **Observed task is already solved with a checklist:** `non_software_sufficient: true` -> template/SOP, not full SaaS.
