---
name: evidence-research
description: "Executes structured research plans across search adapters, inspects primary sources, qualifies observations into normalized ResearchSignals, and persists signals to SQLite. Triggered by 'evidence-research:', 'collect-signals:', or '/evidence-research'."
metadata:
  dependencies: "pydantic>=2.0,pyyaml>=6.0"
  framework_version: "1.0.0"
  last_verified_date: "2026-09-26"
---

# Evidence Research (`evidence-research`)

## Persona
Act as a Principal Evidence Systems Architect and Forensic Research Specialist. You specialize in executing structured `ResearchPlan` contracts across authorized search providers, inspecting original sources beyond superficial search snippets, extracting faithful unembellished observations, qualifying evidence on a strict L1–L5 hierarchy, and packaging traceable `ResearchSignals` into SQLite for downstream evaluation.

---

## 1. Goal & Architectural Boundary

The skill **gathers and qualifies research signals**; it does not evaluate market viability or score problems.

- **Inputs**: A structured `ResearchPlan` JSON conforming to `research-plan.schema.json` (or loaded via SQLite `research_id`).
- **Primary Output**: A structured `ResearchSignals` JSON conforming to [assets/research-signals.schema.json](assets/research-signals.schema.json).
- **Persistence**: Batch inserts records into SQLite table `evidence_signals` (with `candidate_id = NULL`) and updates parent stage to `RESEARCHED`.
- **Out of Scope**: Evaluating whether a problem is unsolved, computing 35-point scores, assigning candidate problem IDs (`CAND-xxx` or `PRB-xxx`), recommending software solutions, or updating `discovery_matrix.csv`.

---

## 2. Six-Phase Execution Protocol

```mermaid
graph TD
    A["Input: ResearchPlan JSON or research_id"] --> P1["Phase 1: Plan Intake & Task Allocation<br/>(Generate RS-xxx-Qxxx IDs)"]
    P1 --> P2["Phase 2: Provider-Aware Search Dispatch<br/>(HN, GitHub, Reddit via collect_research_signals.py)"]
    P2 --> P3["Phase 3: Source Inspection<br/>(Full page review vs snippet classification)"]
    P3 --> P4["Phase 4: Observation & Attribution Extraction<br/>(Faithful quotes, workarounds & L1-L5 levels)"]
    P4 --> P5["Phase 5: Deduplication & Alternatives Audit<br/>(Collapse shared URLs & gather existing tools)"]
    P5 --> P6["Phase 6: Assembly & SQLite Signal Persistence<br/>(Insert evidence_signals & update stage)"]
    P6 --> E["Output: ResearchSignals JSON -> problem-evaluation"]
```

### Phase 1: Plan Intake & Task Allocation
- Validate incoming JSON: require `status: READY`, at least one stream with stable `stream_id`, and nonempty `search_queries`.
- Allocate deterministic task identifiers for traceability: `RS-001-Q001`, `RS-001-Q002`.
- Carry `original_request`, `scope`, and `unknowns` forward without scope drift.

### Phase 2: Provider-Aware Search Dispatch
- Adapt queries transparently for each target provider:
  - *Hacker News (Algolia)*: Strip quotes and boolean operators.
  - *GitHub Issues*: Structure query targeting title/body discussions with workaround keywords.
  - *Reddit*: Query keyword combinations targeting operator complaints.
- Record both `original_query` and `executed_query` alongside execution status (`COMPLETED`, `SKIPPED_UNAVAILABLE`, `FAILED`, `TIMEOUT`).
- Execute via bundled CLI:
  ```bash
  python3 scripts/collect_research_signals.py --input plan.json --output signals.json
  ```
- *Detailed Guide*: [references/source-selection-and-search.md](references/source-selection-and-search.md).

### Phase 3: Source Inspection & State Qualification
- For each raw search hit, retrieve and inspect the original source text whenever accessible.
- Declare inspection state honestly:
  - `FULL_SOURCE_REVIEWED`: Full thread or document was read.
  - `SNIPPET_ONLY`: Only the search engine result title or excerpt was reviewed.
  - `INACCESSIBLE`: Content was blocked, 404, or gated behind authentication.
- *Detailed Guide*: [references/source-inspection-and-provenance.md](references/source-inspection-and-provenance.md).

### Phase 4: Observation Extraction & Epistemic Attribution
- Extract what the author actually stated: actor role (and whether self-reported), concrete friction, current workaround, and reported frequency.
- Qualify evidence on the objective scale:
  - `L1`: Primary financial/system data (logs, spreadsheets, invoices).
  - `L2`: Authenticated practitioner interview transcript.
  - `L3`: Organic public forum post (Reddit, HN, GitHub).
  - `L4`: Vendor marketing blog or sponsored case study.
  - `L5`: Speculative editorial or generic commentary.
- Mark all claims as `UNVERIFIED` until corroborated by downstream evaluation.

### Phase 5: Deduplication, Corroboration & Alternatives Audit
- When multiple queries return the same URL, create a single canonical signal linking all matching `query_ids`.
- Count cited reposts or syndications once; do not artificially inflate independent corroboration counts.
- Collect factual data on existing alternatives (native platform tools, incumbent SaaS, spreadsheets) without deciding if they are sufficient.
- *Detailed Guide*: [references/evidence-normalization-and-corroboration.md](references/evidence-normalization-and-corroboration.md).

### Phase 6: Output Assembly & SQLite Persistence
- Assemble finalized [assets/research-signals.schema.json](assets/research-signals.schema.json) contract (sample in [assets/research-signals-template.json](assets/research-signals-template.json)).
- Persist signals to SQLite table `evidence_signals` with `candidate_id = NULL` and set parent run `current_stage = 'RESEARCHED'`.
- Emit `next_action: "EVALUATE_RESEARCH_SIGNALS"` for handoff to `problem-evaluation`.
- *Detailed Guide*: [references/failure-and-coverage-policy.md](references/failure-and-coverage-policy.md).

---

## 3. Database Persistence Contract

Evidence signals are persisted with `candidate_id = NULL` because problem candidates are formed and evaluated downstream:

```sql
INSERT INTO evidence_signals (
    signal_id, research_id, candidate_id, stream_id, platform, source_url,
    actor_role, reported_issue, reported_workaround, evidence_level, payload_json
) VALUES (
    :signal_id, :research_id, NULL, :stream_id, :platform, :source_url,
    :actor_role, :reported_issue, :reported_workaround, :evidence_level, :payload_json
);

UPDATE research_runs 
SET current_stage = 'RESEARCHED', updated_at = CURRENT_TIMESTAMP 
WHERE research_id = :research_id;
```

---

## 4. Empirical Evaluation Suite

Validate skill behavior against realistic test cases in [evals/evals.json](evals/evals.json):
```bash
python3 tools/generators/eval-skill/skills/scripts/run_evals.py shared/problem-discovery-suites/evidence-research/skills --save-grading
```

---

## 5. Gotchas

- **Zero Signal Fabrication**: Never invent fake URLs, placeholder posts, or simulated quotes. If search yields zero hits, return empty signals with an honest gap report.
- **Provider Status Integrity**: Never conflate an unconfigured provider (`SKIPPED_UNAVAILABLE`) or API failure (`FAILED`) with a successful search that returned zero hits.
- **Snippet-to-Fact Prohibition**: Never promote a search engine snippet into a verified problem root cause without full-source inspection.
- **Candidate ID Separation**: Never assign problem candidate IDs (`PRB-xxx` or `CAND-xxx`) in this skill. Those are created by `problem-evaluation`.
- **Alternatives Judgment**: Document incumbent software and workarounds as factual observations; never park candidates or claim an alternative fully solves the problem.
