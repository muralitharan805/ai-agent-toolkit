# Source Inspection & Epistemic Provenance

## Overview
Defines standards for inspecting original web pages, posts, and threads beyond search snippets, extracting faithful observations, and maintaining rigorous provenance.

---

## 1. Inspection State Hierarchy

A search engine title and excerpt are frequently deceptive or clickbait. Signals must declare their level of verification honestly:

```text
FULL_SOURCE_REVIEWED  (Highest fidelity: full post/thread read and verified)
        │
        ▼
    SNIPPET_ONLY      (Medium fidelity: only search engine snippet reviewed)
        │
        ▼
    INACCESSIBLE      (Failed retrieval: 404, paywall, login gate, or blocked)
        │
        ▼
   NOT_INSPECTED      (Placeholder state before inspection step begins)
```

### Invariants:
- A signal marked `SNIPPET_ONLY` must NEVER be used to assert a verified root cause or specific workflow friction.
- If a target URL returns HTTP 403/404 or a login wall, record status as `INACCESSIBLE` and do not fabricate the underlying discussion.

---

## 2. Extracting Faithful Observations

When reviewing accessible source material, extract only what the author explicitly communicated:

1. **Actor & Role Attribution**:
   - Record exact job titles mentioned (e.g. "warehouse lead", "merchandiser", "third-party seller").
   - Flag whether the role is `self_reported` (e.g. "I run an Etsy store") or `observed_third_party` ("My suppliers struggle with...").
2. **Reported Operational Friction**:
   - Paraphrase concisely without exaggerating severity. Quote key operational terms verbatim.
3. **Current Workaround**:
   - Document the specific non-software or interim patchwork maintained (e.g., "manual copy-paste between portal and Excel", "WhatsApp group updates").
4. **Reported Frequency & Cost**:
   - If the author specifies numbers ("takes 3 hours every Monday", "cost us $500 in fines"), record them with attribution. If absent, leave as `null` / `UNKNOWN`. Never invent estimated costs.

---

## 3. Provenance Metadata
Every accepted signal must preserve immutable retrieval audit fields:
- `source.platform`: Platform identifier (`REDDIT`, `HACKERNEWS`, `GITHUB`, `FORUM`, `WEB`).
- `source.url`: Permanent permalink directly to the thread, comment, or issue.
- `source.published_at`: Original publication timestamp (ISO-8601 UTC) if discoverable.
- `source.retrieved_at`: Exact timestamp when the retrieval tool executed.
