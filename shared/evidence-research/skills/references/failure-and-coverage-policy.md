# Failure Handling, Rate Limits & Coverage Policy

## Overview
Defines robust failure isolation policies, rate limit handling, partial result reporting, and security boundaries during evidence research.

---

## 1. Failure Isolation & Transparent Reporting Matrix

| Failure Mode | Root Cause | Required System Action | Recorded Status |
|---|---|---|---|
| **Invalid Plan Payload** | Missing `stream_id` or empty queries. | Fail immediately with structured validation JSON. Do not invent missing queries. | `INVALID_PLAN` |
| **Provider Unconfigured** | No API credentials or tool adapter. | Skip provider and log explicit gap in `run_limitations`. | `SKIPPED_UNAVAILABLE` |
| **HTTP 429 Rate Limit** | Provider quota exceeded. | Perform exponential backoff (up to 3 retries). If still blocked, record explicit rate limit. | `RATE_LIMITED` |
| **HTTP 5xx Server Error** | Provider outage. | Retry once. If failed, isolate error without crashing entire stream. | `FAILED` |
| **Request Timeout** | Network latency $> 10$ seconds. | Abort specific query task, log timeout, proceed to next query. | `TIMEOUT` |
| **Zero Search Hits** | No documents match query. | Record 0 results honestly. Do NOT interpret as proof that no problem exists. | `COMPLETED` (Count: 0) |
| **Paywall / Login Barrier** | Content gated behind auth. | Preserve search snippet; mark inspection status as `INACCESSIBLE`. | `INACCESSIBLE` |

---

## 2. Partial Coverage & Execution Status

When some providers or queries fail, the overall research run must not fail silently:
- If all queries across all streams succeed: `status: "COMPLETED"`.
- If some providers were skipped, timed out, or returned zero hits: `status: "COMPLETED_WITH_GAPS"`.
- If all providers failed across all queries: `status: "FAILED"`.

---

## 3. Privacy, Confidentiality & Compliance Boundaries
1. **No Scraping Behind Private Logins**: The agent must NEVER attempt to bypass authentication walls, CAPTCHAs, or private user accounts.
2. **Redaction of PII**: When ingesting forum threads or public complaints, redact personal identifiers (phone numbers, personal email addresses, national tax IDs).
3. **No Secret Material in Logs**: API keys, Bearer tokens, or credentials must never appear in raw output JSON or stderr diagnostics.
