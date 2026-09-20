# Problem Discovery CSV — all 30 columns explained

This is the field-by-field guide for `scripts/discovery_csv.py` and its single `discovery_matrix.csv` research register. The **canonical names and order** come from `FIELDS` in that script; do not add columns or change the CSV header just to display these explanations. **One stable `candidate_id` = one problem row; one CSV = the ongoing register.** The examples below are hypothetical interpretations, not verified customer findings.

## Identity and research priority (columns 1–8)

| # | CSV column | Meaning and how to read it |
|---|---|---|
| 1 | `candidate_id` | Stable unique problem identifier, e.g. `PROB-EMAIL-001`. Reuse exactly the same ID to update this problem; a new ID creates a new row. An ID is not an external research citation. |
| 2 | `problem_title` | Short description of the user's **broken workflow/problem**, not the name of a product you want to sell. |
| 3 | `domain` | Industry or work area in which this particular workflow occurs. Keep it within the user's requested research scope; an unrelated domain is a scope error, not a discovery for that scope. |
| 4 | `track` | `commercial` studies willingness to pay/economic value; `free_utility` studies repeated utility/accessibility without requiring payment intent. |
| 5 | `rank` | Position in this CSV **after sorting by research score** (ties by candidate ID). It can change on every update. Neither an opportunity ranking nor proof of validated demand. |
| 6 | `total_score` | Sum of the **effective** seven dimension scores, range 0–35. Evidence-level caps may reduce the entered scores. It prioritizes *further investigation*, not customer adoption. |
| 7 | `classification` | The scorer's research/action category, derived from score, stop checks, evidence and trial outcome. For example `UNVERIFIED_INPUT / RESEARCH_PRIORITY` means investigate and collect evidence; it is not an independently established market finding. |
| 8 | `status` | Current **evidence/experiment workflow state**: examples include `UNVERIFIED`, `QUALIFIED`, `RESEARCH_PRIORITY`, `EXPERIMENT_FAILED`, `VALIDATED`, `PARKED`, `REJECTED`, `KILLED`. Do not infer status from score alone. `VALIDATED` is a locally audited, metric-gated result for a defined trial, not certification that a SaaS business will succeed. |

## Evidence and experiment flags (columns 9–12)

| # | CSV column | Meaning and how to read it |
|---|---|---|
| 9 | `evidence_level` | Declared evidence category: **1** directly observed behavior, **2** primary operator interview, **3** corroborated independent discussion/reviews, **4** secondary reports, **5** unsupported hypothesis. This is a claim about input quality, **not** a verification pass. The scorer caps level-4 dimension scores at 1 and level-5 scores at 0. |
| 10 | `evidence_verified` | `true` means **at least one** level-1/2 evidence record passed the script's local artifact/hash/date/reviewer metadata checks; it does **not** establish that every claim was checked or that the artifact/interview is authentic. `false` means that required check did not pass. Human review of actual claims is still necessary. |
| 11 | `experiment_completed` | `true` means the supplied structured trial passed the date/metric/sample/artifact-integrity checks. `false` can mean **not run, incomplete or invalid data**; it does *not* mean the trial failed. Read `experiment` for the actual distinction. |
| 12 | `experiment_passed` | `true` means a completed, structurally accepted trial met its prerecorded numeric threshold. `false` alongside `experiment_completed=true` means a threshold miss; `false` alongside `experiment_completed=false` means no accepted outcome, **not** a proven failure. Independent field authenticity still needs review. |

## Seven scoring dimensions (columns 13–19)

Each dimension contributes an effective score from **0 to 5**, using the criteria in `35-point-evidence-scoring-and-wtp.md`. Record why each nonzero score is justified in the evidence/notes. Seven scores of 4 produce `total_score=28` only when evidence-level caps do not apply; seven identical values without separate support may be provisional guesses.

| # | CSV column | What the score investigates |
|---|---|---|
| 13 | `frequency` | How often the *observed* problem recurs for the specified operator/workflow. |
| 14 | `severity` | Measured or documented consequences: time, loss, errors, risk, service impact. |
| 15 | `workaround` | How costly, fragile or inconvenient current manual/tool/process workarounds are; identify the actual alternative before scoring. |
| 16 | `wtp` | On `commercial`: evidence of historical spend, budget or actual payment intent (willingness to pay); on `free_utility`: this effective dimension may be supplied using `utility_impact`, reflecting usefulness rather than price. A score is not a signed purchase commitment. |
| 17 | `decision_maker` | Whether the affected person can approve/adopt a remedy, or whether a reachable buyer/owner exists. |
| 18 | `feasibility` | Whether the *smallest useful fix* is practical to prototype and test under real constraints; not a guarantee of business viability. |
| 19 | `discrepancy` | Gap between the required workflow and the fit of existing tools, non-software fixes and current processes. Verify alternatives rather than assuming none exists. |

## Sources, workflow and stop checks (columns 20–24)

These fields contain **JSON-formatted text inside a CSV cell**. `[]` is an empty list; `null` means the structured value is absent; neither proves the researcher checked a source or completed a workflow. A pasted URL is a pointer, not proof that it was opened or supports the claim.

| # | CSV column | Meaning and how to read it |
|---|---|---|
| 20 | `evidence_sources` | List of source URLs or safe references to complaints/reviews/observations. Open each source, check exact claim, context, date and independence; query suggestions and unvisited links are not research findings. |
| 21 | `evidence_artifacts` | References to supporting screenshots, redacted logs, interview notes or trial files. Empty `[]` means no references supplied; the links/paths alone do not satisfy an evidence audit. Keep confidential originals outside public CSV/Git. |
| 22 | `evidence_records` | Structured **per-claim** audit input, such as `claim`, `level`, `observed_on`, `artifact_path`, `sha256`, `reviewed_by`, `reviewed_on`. `null` means no records supplied. Local hash matching confirms file integrity, *not* authenticity of the reviewer, person or observation. |
| 23 | `workflow_14_nodes` | Detailed mapping of **actor, trigger, input, steps, tools, decisions, handoffs, delays, rework, errors, output, cost, risk, audit** for this operator/problem. `null` means the map was not supplied; do not silently invent missing nodes. The CSV writer stores the supplied JSON but does not independently verify all 14 nodes are filled. |
| 24 | `stop_checks_triggered` | List of blocker flags identified in the input/scorer, e.g. low impact, suitable existing alternative, single-source bias, internal training issue or unreachable audience. `[]` says no flag was **recorded as triggered**, not that all alternatives and biases were investigated or ruled out. |

## Experiment and solution scope (columns 25–28)

| # | CSV column | Meaning and how to read it |
|---|---|---|
| 25 | `experiment` | JSON trial contract and supplied result: preregistered hypothesis/date, metric/direction/threshold/failure rule, trial dates, sample, observed numeric result, supporting artifact/hash and dated reviewer. `null` means none supplied. Distinguish `NOT_RUN` from a completed failed trial; do not retroactively set targets after seeing results. |
| 26 | `solution_constraints` | JSON of **observed or explicitly labelled hypothetical** requirements: `non_software_sufficient`, interactive UI, batch automation, browser integration, multi-user sync, server storage, background jobs, offline use and notes. A researcher's proposed feature list is **not yet user evidence**. |
| 27 | `smallest_solution` | JSON of the scorer's proposed `format`, reasoning, requirements and `review_required`. Possible formats include `template_sop`, `static_web_utility`, `cli_tool`, `browser_extension`, `micro_saas`; no supported constraints may yield `null`. A `micro_saas` result can be caused by input flags such as `needs_server_storage=true` or `needs_background_jobs=true`: **architecture hypothesis, not validated SaaS demand**. |
| 28 | `recommended_action` | The next concrete research/verification step derived by the scorer, e.g. audit a primary artifact, run a preregistered trial, revisit stop checks or narrow scope. It is a next action, not proof that the step was performed. |

## Analyst context and update time (columns 29–30)

| # | CSV column | Meaning and how to read it |
|---|---|---|
| 29 | `research_notes` | Analyst explanation, score rationale, observed facts versus hypotheses, open questions, competing solutions, source limitations and next interview. The writer preserves existing notes when a same-ID update omits/empties `research_notes`; explicitly supplied nonempty notes replace them. Never claim a research step happened just because it appears as a plan here. |
| 30 | `updated_at` | UTC ISO 8601 timestamp of the **last CSV row write**, e.g. `2026-09-20T04:56:47+00:00`. It is **not** the date the problem occurred, the source was published, a participant was interviewed or a trial finished. Record those dates in the corresponding research fields. |

## How to interpret a sample row

A candidate with `total_score=28`, `status=UNVERIFIED`, `evidence_level=3`, `evidence_verified=false`, `experiment_completed=false`, `experiment_passed=false`, `workflow_14_nodes=null`, and `smallest_solution.format=micro_saas` means: **high *research* priority according to supplied scores, but no accepted primary evidence or completed trial; the actual workflow is not mapped; SaaS was proposed based on submitted constraints only.** It does **not** say the URL claims have been verified, the trial failed, people will pay, or hosted infrastructure is required in practice.

## Update discipline and data safety

- Keep the same `candidate_id` for the same problem; never merge unrelated domains or give an unrelated problem a matching ID. `rank` is recalculated when CSV is updated.
- **Provide the complete current candidate JSON on every same-ID update.** The scorer regenerates most row fields from the new input; it does *not* merge missing evidence, scores, workflow or experiment JSON from the old row. Only nonempty historical `research_notes` get a special preservation rule. Back up valuable research before revising it.
- For a user-requested domain, record out-of-scope leads separately or omit them; do not present unrelated email-infrastructure research as evidence of an AI-agent regression problem.
- Keep customer identifiers and raw private material out of public spreadsheets and Git. Use safe/redacted artifact references and only publish reviewed conclusions.
- `discovery_csv.py` produces the register; the legacy Markdown-to-CSV exporter has a **different header**. Do not mix them or overwrite an incompatible CSV.
