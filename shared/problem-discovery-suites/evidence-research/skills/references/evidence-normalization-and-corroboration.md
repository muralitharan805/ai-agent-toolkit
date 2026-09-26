# Evidence Normalization, Corroboration & Alternatives Audit

## Overview
Establishes the criteria for qualifying evidence levels (L1–L5), preventing duplicate counts across shared sources, and gathering objective alternative evidence.

---

## 1. The 5-Tier Evidence Hierarchy

| Level | Evidence Classification | Verification Criterion | Permitted Scoring Ceiling in Evaluation |
|---|---|---|---|
| **L1** | Primary System / Financial Data | Sanitized spreadsheet logs, bank transaction audits, API logs, printed receipts. | Eligible for full score ($\ge 28$ PTS). |
| **L2** | Direct Operator Interview | Verified practitioner transcript with authenticated job identity. | Eligible for up to 28 PTS. |
| **L3** | Public Community Complaint | Organic Reddit thread, Hacker News discussion, GitHub issue complaint. | Capped at 20 PTS unless corroborated by L1/L2. |
| **L4** | Vendor Case Study / Marketing | SaaS vendor promotional post, sponsored blog article, sales deck. | Capped at 15 PTS (high commercial bias). |
| **L5** | Speculative Commentary | Editorial opinion, LinkedIn influencer post, generic listicle. | Capped at 10 PTS (rejected as primary evidence). |

---

## 2. Deduplication & Independence Protocols

A core failure mode in research is mistaking echo chambers for recurring enterprise pain.

### Rules:
1. **Canonical Source Deduplication**:
   - If Query 1 and Query 2 both retrieve `https://reddit.com/r/.../xyz`, create a single `signal_id`.
   - Associate both query IDs: `query_ids: ["RS-001-Q001", "RS-001-Q002"]`.
2. **Quoted Reposts & Syndication**:
   - If Blog B reprints a complaint verbatim from Reddit Thread A, do not count this as two independent signals. Link Blog B as a derivative citation.
3. **True Corroboration Standard**:
   - Corroboration requires **independent operational actors** operating in separate companies or environments encountering the same friction.

---

## 3. Alternative Evidence Collection Standard

When the incoming plan requests `audit_existing_alternatives: true`, the Evidence Research skill must gather traceable facts regarding how the market currently addresses the problem:

- **Native Platform Features**: Does the underlying platform (e.g. Shopify, Amazon, Salesforce) provide a native setting or built-in workflow?
- **Incumbent Software Tools**: What commercial tools are mentioned by name? What are their entry-level pricing tiers and documented limitations?
- **Manual Glue-Work Workarounds**: What non-software approaches (pen-and-paper registers, Excel formulas, Zapier webhooks) are operators using?

> [!IMPORTANT]
> The Evidence Research agent **does not declare an alternative sufficient or park the candidate**. It simply documents the alternatives and user-reported friction, leaving final scoring to `problem-evaluation`.
