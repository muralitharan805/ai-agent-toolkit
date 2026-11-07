# Stage Gates, Invariants & Anti-Hallucination Contracts

## 1. Absolute Prohibition of Synthetic Artifacts

The orchestrator and downstream skills are strictly forbidden from generating synthetic or fabricated evidence to simulate progress.

The following data types **MUST NEVER** be hallucinated or synthetically generated:
- Social forum discussions, Reddit threads, GitHub issue permalinks, or review quotes.
- Fictional practitioner interview transcripts.
- Fabricated participant counts or survey sample sizes.
- Simulated numerical trial observations or measured error rates.
- Fake SHA-256 evidence digests or mock auditor signatures.
- Fictitious `PASSED` experiment verdicts.

If external search or real participant evidence is unavailable, the workflow must stop or report the blocker with zero database mutation.

---

## 2. Evidence Sufficiency & Scoring Gate

Before advancing a problem candidate to `experiment-validation`:
- **Evidence Level Requirement**: The candidate must possess supporting signals with a verified provenance of at least Level 2 (Corroborated) or Level 3 (Triangulated).
- **Unassessed Snippet Rule**: Signals derived solely from superficial search snippets without primary source inspection cannot satisfy the sufficiency gate.
- **Score Cap**: Uncorroborated candidates have their research scores capped at 14/35. Full scoring (up to 35/35) is permitted only when backed by genuine multi-platform signals.

---

## 3. Preregistration Immutability Gate

When an experiment contract is preregistered:
- **Contract Freeze**: Target threshold, directional operator (`>=`, `<=`), sample target, and primary metric are permanently written into `experiments.contract_json`.
- **Zero Symmetrical Goalpost Shifts**: The assessment phase cannot alter the pass/fail threshold post-hoc.
- **Cryptographic Evidence Digest**: Real-world trial observations require a SHA-256 hash of the source data artifact (e.g. CSV/JSON log) and a named human reviewer.

---

## 4. Non-Software Sufficiency & SaaS Justification Gate

Before recommending any software build or SaaS product:
1. **Non-Software Sufficiency Audit**: If an SOP, spreadsheet, or existing off-the-shelf tool solves $\ge 80\%$ of the operational friction, software is rejected.
2. **Principle of Least Complexity**: The simplest solution among 17 solution classes (e.g. documentation, automation script, browser extension, middleware integration) must be selected before SaaS is considered.
3. **SaaS Justification Gate**: SaaS is justified only when multi-tenancy, cross-organization data synchronization, or proprietary backend processing is strictly required by the validated problem.
