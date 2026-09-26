---
description: "Enforces strict evidence research boundaries, authentic source traceability, non-fabrication of search results, and SQLite signal persistence contracts."
trigger: model_decision
framework_version: "1.0.0"
last_verified_date: "2026-09-26"
---

# Evidence Research & Signal Qualification Rules

## Description
This rule governs the Evidence Research execution phase across all problem discovery and market investigation operations. It strictly mandates empirical fidelity: taking a structured `ResearchPlan`, dispatching search queries across authorized adapters, inspecting original primary sources, extracting faithful observations, and qualifying signals into a versioned `ResearchSignals` contract. It forbids the fabrication of search results, prevents premature problem evaluation or scoring, mandates explicit tracking of search status, and enforces the SQLite `evidence_signals` storage contract.

## Constraints

### 1. Scope Boundary & No-Evaluation Invariant
- The Evidence Research agent MUST ONLY execute search tasks, inspect accessible sources, extract reported observations, and record alternative evidence.
- The agent is STRICTLY FORBIDDEN from:
  1. Deciding whether an operational problem is unsolved or validated.
  2. Calculating 35-point research scores or scoring candidate viability.
  3. Formulating 14-node forensic problem candidates or assigning candidate IDs (`PRB-xxx` or `CAND-xxx`).
  4. Recommending software, architecture, or commercial pricing models.
  5. Writing or modifying records in `discovery_matrix.csv`.
- A collected signal is an unverified behavioral observation, never proof of an addressable market or customer willingness to pay.

### 2. Zero Signal Fabrication & Authentic Traceability
- Every signal in `ResearchSignals` MUST trace directly to an authentic source URL, permanent permalink, or verified offline artifact.
- Inventing synthetic forum posts, hypothetical URLs (`https://example.com/...`), fake quotes, or fictitious timestamps to populate schema fields is STRICTLY PROHIBITED.
- If live queries return zero results, the agent MUST output an empty `signals: []` array with status `COMPLETED_WITH_GAPS` and explicit gap notes. Never invent placeholder signals.
- Every signal MUST declare its inspection status honestly:
  - `FULL_SOURCE_REVIEWED`: The complete page/thread was fetched and verified.
  - `SNIPPET_ONLY`: Only the search engine result title or excerpt was reviewed.
  - `INACCESSIBLE`: The target URL was blocked, behind a paywall, or returned 404.
  - `NOT_INSPECTED`: The source link has not been fetched or inspected.

### 3. Provider Adaptation & Transparent Status Reporting
- The agent and script MUST record both the original query from `ResearchPlan` and the exact provider-adapted query executed.
- Query syntax must be translated transparently per provider (e.g. converting Google dorks to Algolia terms or GitHub issue filters). Modifying query semantics without recording both versions is forbidden.
- Search provider execution states MUST NOT be conflated:
  - `COMPLETED`: The query executed successfully and returned $N$ results ($N \ge 0$).
  - `SKIPPED_UNAVAILABLE`: The provider adapter is not configured, lacks credentials, or is unsupported.
  - `FAILED`: An API error, HTTP 5xx, or network disruption occurred.
  - `TIMEOUT`: The request exceeded the configured latency boundary.
- A request failure or timeout MUST NEVER be reported as a successful search with zero results.

### 4. Epistemic Evidence Qualification (L1 to L5)
- All extracted observations MUST be qualified on the objective evidence hierarchy:
  - `L1`: Primary financial/system audit data (sanitized spreadsheets, receipts, system logs).
  - `L2`: Direct practitioner interview transcript with verified job role.
  - `L3`: Public forum post or public community complaint (Reddit, Hacker News, niche forums).
  - `L4`: Marketing collateral, vendor blog post, or promotional case study.
  - `L5`: Speculative opinion, generic editorial, or unsourced commentary.
- An anonymous post on social media MUST NEVER be classified higher than `L3`.
- An author claiming firsthand experience on a public forum remains an unverified self-report; it does NOT constitute human-audited L1 or L2 primary evidence.

### 5. Deduplication & Corroboration Integrity
- When multiple planned queries return the exact same source URL or post ID:
  - A single canonical source record MUST be created.
  - All matching `stream_id` and `query_id` associations MUST be linked.
  - It MUST NOT be counted as multiple independent sources.
- Quoted reposts, syndicated articles, cross-posts, and copy-pasted complaints MUST NOT be counted as independent corroboration.

### 6. Alternative Evidence Collection Standard
- When `audit_existing_alternatives: true` is requested, the agent MUST collect factual data regarding existing options:
  - Incumbent software functionality and pricing tiers.
  - Documented limitations from user reviews (G2, Capterra, GitHub issues).
  - Non-software alternatives currently used (spreadsheets, physical notebooks, phone calls).
- The agent MUST NOT judge whether an alternative is satisfactory or park problem candidates; alternatives data is passed as factual inputs to `problem-evaluation`.

### 7. SQLite Signal Persistence Contract
- Collected signals MUST be batch inserted into SQLite table `evidence_signals`:
  - `signal_id`: Sequential token format `SIG-NNN`.
  - `research_id`: Mandatory parent run identifier from `ResearchPlan`.
  - `candidate_id`: MUST BE SET TO `NULL` (candidates are formed later in `problem-evaluation`).
  - `stream_id`: Associated research stream (`RS-001`, `RS-002`, etc.).
  - `platform`: `REDDIT`, `HACKERNEWS`, `GITHUB`, `FORUM`, or `WEB`.
  - `source_url`: Permanent permalink to original post or page.
  - `reported_issue`: Verbatim complaint or extracted friction summary.
  - `reported_workaround`: Documented manual glue-work or spreadsheet usage.
  - `evidence_level`: Initial classification (`L1` to `L5`).
  - `payload_json`: Complete normalized signal dictionary.
- Upon successful insertion, update parent run:
  ```sql
  UPDATE research_runs 
  SET current_stage = 'RESEARCHED', updated_at = CURRENT_TIMESTAMP 
  WHERE research_id = :research_id;
  ```

## Examples

### 1. Transparent Provider Reporting vs. Hallucinated Search
```text
❌ FORBIDDEN (Claiming unexecuted search & false zero hits):
Plan Query: "ecommerce seller" "inventory sync" "manual"
Agent Report:
- Google Search: COMPLETED (0 results found) -> Concludes no problem exists.
- In reality: No Google Search API key was configured; search was never run.

✅ CORRECT (Honest status reporting & gap tracking):
Plan Query: "ecommerce seller" "inventory sync" "manual"
Agent Report:
- Web Search: SKIPPED_UNAVAILABLE (No web search tool configured in environment).
- Hacker News (Algolia): COMPLETED (0 results matching "ecommerce seller inventory sync manual").
- Reddit: COMPLETED (3 discussions retrieved with permalinks).
- Status: COMPLETED_WITH_GAPS (Web search skipped; Reddit evidence captured).
```

### 2. Epistemic Evidence Qualification vs. Unverified Promotion
```text
❌ FORBIDDEN (Promoting forum complaint to verified enterprise pain):
Source: Reddit post by "u/ecom_guy": "Tired of updating Shopify inventory every morning."
Agent Signal:
- Evidence Level: L1 (Verified Enterprise Problem)
- Fact: All ecommerce merchants lose 2 hours daily on inventory updates.

✅ CORRECT (Strict L3 classification & attribution preservation):
Source: Reddit post by "u/ecom_guy": "Tired of updating Shopify inventory every morning."
Agent Signal:
- Evidence Level: L3 (Public Community Complaint)
- Actor: Self-reported online merchant (unverified role)
- Observation: Poster reports manual daily Shopify inventory updates.
- Workaround: Manual morning spreadsheet entry.
- Limitations: Single uncorroborated post; financial loss and frequency unverified.
```
