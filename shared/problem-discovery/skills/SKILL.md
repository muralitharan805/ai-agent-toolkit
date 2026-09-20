---
name: problem-discovery
description: "Investigates real operational problems with traceable sources, forensic workflow mapping, evidence-gated research scoring, preregistered experiments, and constraint-driven solution scoping."
metadata:
  dependencies: "Python >=3.10; optional manual field research and web access"
  framework_version: "Universal / Agnostic"
  last_verified_date: "2026-09-20"
---

# Universal Problem Discovery: Evidence Before Software

## Purpose and execution contract

This procedural skill investigates **observed** operational problems, not speculative SaaS ideas. The agent must distinguish (a) candidate discovery, (b) research priority, (c) manual verification of primary evidence and (d) outcomes of small preregistered experiments. A score, search result, spreadsheet, statement by an LLM, or positive interview is **not** market validation. No automatic online search or source-authenticity verification is implemented by the bundled CLI: `--dorks` only prints search queries. Do not describe suggested queries as executed searches.

Use the existing module (`shared/problem-discovery`) rather than generating a duplicate skill. Work through these seven stages; at every stage state **known facts, unknowns, and the next concrete verification**. A missing stage is recorded as incomplete rather than inferred. A discovery can finish as `UNVERIFIED`, `PARKED`, or `EXPERIMENT_FAILED`; do not force a positive outcome.

## References and supporting tools

- [Evidence audit and structured experiment contract](references/evidence-audit-contract.md): machine-checkable integrity rules, human-review boundary, and CLI examples.
- [14-node workflow and glue work](references/14-node-workflow-and-glue-work.md): Actor, Trigger, Input, Steps, Tools, Decisions, Handoffs, Delays, Rework, Errors, Output, Cost, Risk, Audit.
- [35-point scoring and WTP](references/35-point-evidence-scoring-and-wtp.md): seven 0–5 research dimensions and separate commercial/free-utility tracks.
- [Interviewing and root causes](references/discovery-frameworks-and-interviewing.md): TRACE, FOCUS, counterfactuals, and historical behavior.
- [Complaint mining and query refinement](references/complaint-mining-and-dorking.md): web queries and independent-source corroboration.
- [Competitor and non-software alternatives](references/anti-opportunities-and-saturation-traps.md): actual workflow, language, device, price, and switching-cost fit.
- [Solo-builder solution choice](references/solo-builder-micro-saas-strategy.md): avoid starting with SaaS without evidence of shared-state requirements.
- [Local and offline fieldwork](references/local-and-offline-discovery.md): on-site operator observation, consent, connectivity and language.
- [Small experiments](references/experiment-design-and-validation.md): preregistration, measured adoption, and explicit failure rules.
- `scripts/score_problem_candidate.py`: deterministic scoring, local-file integrity audit, experiments, search-query suggestions, dossier export.
- `scripts/export_discovery_matrix.py`: builds a CSV that never equates a high score with validated demand.
- `assets/scoring-matrix-schema.json`: current structured input contract.
- `assets/discovery-log-template.md`: human research dossier template.
- `evals/`: evaluation prompts, not proof of user demand.

## Seven-stage procedure

1. **Bound and track.** State target operator, exact workflow, location, frequency, and research budget. Pick `commercial` for economic value/WTP or `free_utility` for repeat usefulness/accessibility; zero WTP is not a defect in a free tool.
2. **Mine and observe.** Search public complaints and review evidence with provenance and independent sources; refine jargon and local-language terms. In physical environments conduct consented counter shadowing. Suggested Google queries from `--dorks` are not themselves research results.
3. **Deconstruct.** Trace all fourteen workflow nodes. Isolate the broken handoff and cost of inaction; absence of a workaround can mean either low impact or inaccessible existing products. Do not assign a score until these alternatives are investigated.
4. **Audit alternatives.** Inspect actual task fit, local constraints, language, device/offline support, switching friction, and non-software fixes. If a checklist/Excel/WhatsApp SOP solves the measured bottleneck adequately, document `non_software_sufficient` and stop at a template.
5. **Prioritize, do not validate.** Score seven dimensions (0–5 each) and record sources **per claim**. Level 4 secondary reports cap each dimension at 1; Level 5 unsupported hypotheses force zero. Stop checks park candidates before experiments. At 23–27 recommend shadowing; 28–35 recommend a small trial. At any high score without manually audited primary evidence, status must remain `UNVERIFIED`. Run the CLI with a JSON candidate conforming to the evidence contract, not raw flags alone.
6. **Preregister and measure.** Before starting a trial record a dated hypothesis, metric, direction, success threshold, explicit failure rule and test period. After the trial, collect sample size, observed numeric value, the source artifact and independent manual review details. A textual `--experiment-outcome` is accepted only as a legacy note: it cannot validate. A failing trial yields `EXPERIMENT_FAILED`, not a positive label; an incomplete trial stays research priority.
7. **Scope and persist.** Record observed requirements explicitly in `solution_constraints`: whether a non-software fix suffices; whether interactive UI, batch automation, browser integration, multi-user sync, server storage, background jobs or offline operation is needed. If the requirements are unknown, leave architecture undecided. Only then select template, static web utility, CLI, extension, or Micro-SaaS; document the rationale and verify with a human. Export to an explicitly chosen writable directory. Rebuild `discovery_matrix.csv` from the notes in the same run; never silently default to a developer's personal Obsidian path.

## Output and review gates

Every dossier must contain: problem/actor and fourteen nodes; independent source citations with observation dates; a per-claim evidence ledger with local artifact, SHA-256 and named manual reviewer; seven scores and research priority; alternative audit; experiment contract and measured outcome or explicit `NOT_RUN`; constraints-derived technical option; open questions and next verification. A manual reviewer **must check that underlying files genuinely depict the claimed work**. The tool only checks that reviewed local files exist and match recorded hashes; it cannot detect fabricated interviews, manipulated screenshots or fake engagement data.

CLI examples (run from the skill's `scripts/` directory, or use absolute paths):

```bash
python3 score_problem_candidate.py --dorks "textile reconciliation"
python3 score_problem_candidate.py --input-json candidate.json --json --strict \
  --export-obsidian /path/to/your/discovery_logs
python3 export_discovery_matrix.py --dir /path/to/your/discovery_logs
```

For a single candidate, `--evidence-json audit.json` accepts `evidence_records`, `experiment` and `solution_constraints` alongside old scoring flags. In batch mode put these fields on **each** candidate JSON object. Never use `--strict` as a market-proof certification; it only rejects parked, unverified, rejected, or failed candidates.

## Gotchas and failure paths

- **No evidence, no validation:** score 35/35 + a source URL + "customers love it" is still `UNVERIFIED`. Even a correctly hashed file requires a genuine manual audit of its contents.
- **Integrity is not truth:** an artifact digest checks bytes, not whether a claim or experiment is authentic. A date and reviewer identity are user-supplied; cross-check them independently.
- **Score is research priority:** an experiment may fail despite strong pain signals; CSV must retain actual status and never promote a legacy `TIER-1 GOLD` score to validation.
- **Pre-registration matters:** do not choose the threshold after seeing results. Numeric observed outcomes must map to the recorded metric, sample and test period.
- **No arbitrary SaaS:** do not infer stack from words in a title. Unknown constraints lead to undecided architecture; documented non-software sufficiency leads to a template, not a subscription.
- **Offline and private data:** seek consent, redact customer/transaction identifiers in artifacts, store evidence in access-controlled local directories, and avoid committing sensitive artifacts to Git.
- **Portable paths:** specify `--export-obsidian` or `--dir`; if the vault isn't mounted, show the dossier for manual saving rather than pretending a write succeeded.
- **Multi-candidate research:** carry surviving candidates into scoring; rank by research score for investigation, but never confuse rank with validated adoption.
