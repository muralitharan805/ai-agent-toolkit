# Existing-candidate preflight: avoid rediscovering the same problem

## When to run

Before any *repeat* Problem Discovery request for a domain, and before assigning an ID or sending newly mined problems to the scorer, read the accessible existing `discovery_matrix.csv` for the project. Use this same file as the research history, including parked, rejected, killed, failed and validated candidates. This is a **research-agent procedure**, not a built-in semantic-dedup feature of `discovery_csv.py`.

If the existing CSV is not supplied or accessible, state that historical de-duplication was not checked and request the existing file or its accessible path; do not claim the findings are new to the user's project. If this is the first run with no prior ledger, start a new CSV as usual. Do not invent or silently substitute a ledger from a different project.

## Compare underlying problem, not exact title

For each new signal, compare with existing rows in the requested domain by **actor/target role, trigger, task and workflow, actual failure/bottleneck, existing workaround, and context**. Read `problem_title`, `domain`, `workflow_14_nodes`, `research_notes`, `status`, `stop_checks_triggered` and relevant evidence URLs. The same root cause with different wording or URLs is the **same candidate**, not a new row. Similar terms can describe genuinely different problems for different users or workflows; do not collapse them automatically. When uncertain, flag a possible duplicate for manual review rather than creating an unqualified new ID.

- **Same problem, no material new findings:** do not create another candidate or re-recommend a solved/parked hypothesis. Keep its existing row and ID. The presence of another public complaint is not itself a new problem.
- **Same problem with material new evidence, a changed segment or previously unexamined constraint:** reference its stable `candidate_id`; explain whether to update/reopen that row or, only for a genuinely distinct actor/workflow, create a linked new candidate. Review previous stop-check reasons before reopening. Never silently change `PARKED`, `REJECTED`, `KILLED`, `EXPERIMENT_FAILED` or `VALIDATED`.
- **Different root problem:** assign a new stable ID and append it to the existing CSV, not a separate per-problem Markdown file.

When manual investigation finds that an existing alternative adequately solves the *specific target user's* problem, record who was checked, date, exact alternative and workflow fit in `research_notes`; when backed by the available evidence, set input stop check `commercial_alternative_fits_well: true` and re-evaluate via the scorer, producing `PARKED`. Do **not** mark such a candidate `VALIDATED` merely because the alternative works. `PARKED` is a reason to avoid proposing it again to the same segment; it is not a universal claim that no one else has that problem.

## Preserve what the current software actually does

`discovery_csv.py` detects duplicate **IDs only**, not semantically equivalent problem titles. It scores each submitted full candidate JSON and upserts its row by ID. On a same-ID update, include the complete existing research, scores, evidence, workflow, experiment and constraints in the new input; omitted fields are rebuilt as missing. Manual `research_notes` are the only previous field conditionally retained by the script. Do not take a prior CSV row and present its derived `status` or `evidence_verified` flags as independently verified source input.

Before writing, explain in the research report: `new candidate IDs`, `existing IDs reused`, `skipped duplicates / parked problems`, `possible duplicates requiring review`, and whether the prior CSV was actually examined. New rows must not be represented as guaranteed unique if the comparison was unavailable or inconclusive.

The default discovery stages, scoring, evidence gates, validation definitions and single-CSV output remain unchanged. This preflight does **not** start a scheduled miner, perform automatic public-source research or guarantee semantic uniqueness in standalone CLI runs.