# Source Selection & Search Dispatching Guide

## Overview
Guides the Evidence Research agent and search dispatchers in mapping planned queries to provider-compatible formats and recording rigorous search execution states.

---

## 1. Provider Adapter Capabilities & Query Adaptation

Different search backends require distinct syntax adaptation. Submitting raw Google-style dorks with advanced operators (`site:`, `filetype:`, `OR`) into APIs that do not support them results in zero hits or API errors.

| Provider Backend | Target Data | Query Adaptation Protocol | Syntax Nuance |
|---|---|---|---|
| **Hacker News (Algolia API)** | Technical practitioner discussions, "Ask HN", tool debates. | Strip quotes and advanced dorks. Combine keywords: `[domain] [operator] [task]`. | Supports standard keyword matching. Filter by `story` or `comment` tags. |
| **GitHub Issues API** | Bug reports, feature requests, manual workflow workarounds. | Convert to issue search syntax: `[domain] in:title,body state:closed "workaround"`. | Exclude code/commit searches. Focus on open/closed discussions. |
| **Reddit Public Search** | Unvarnished operator complaints, daily frustrations, shadow tools. | Use URL-encoded keyword searches: `[domain] [task] "takes hours"`. | Handle rate limits. Target relevant subreddits when domain is specialized. |
| **General Web Search** | Broad industry blogs, regional gazettes, public SOPs, PDFs. | Use exact phrase matching (`"..."`) and filetype filters (`filetype:xlsx`). | Only invoke if an authorized web search tool or API is configured. |

---

## 2. Execution Task Lifecycle

Every query from the incoming `ResearchPlan` is assigned a deterministic task ID:
$$\text{Task ID} = \text{[stream\_id]} + \text{"-Q"} + \text{[3-digit index]} \quad (\text{e.g., } \text{RS-001-Q001})$$

### Execution Status States:
1. `COMPLETED`: Search executed successfully. May contain 0 or more results. Zero results is a valid finding, not an error.
2. `SKIPPED_UNAVAILABLE`: The provider adapter is not configured or lacks API access.
3. `FAILED`: The provider returned an unrecoverable error (e.g., HTTP 500, network disconnect).
4. `TIMEOUT`: The request exceeded the maximum allowed response window (default: 10s).
5. `RATE_LIMITED`: The provider returned HTTP 429; bounded backoff was exhausted.

---

## 3. Query Execution Record Schema
Every query attempt must preserve both the planned intent and the concrete execution:

```json
{
  "stream_id": "RS-001",
  "query_id": "RS-001-Q001",
  "original_query": "\"ecommerce seller\" \"inventory sync\" \"manual\"",
  "provider_runs": [
    {
      "provider": "hackernews",
      "executed_query": "ecommerce seller inventory sync manual",
      "status": "COMPLETED",
      "result_count": 2,
      "latency_ms": 320,
      "error": null
    }
  ]
}
```
