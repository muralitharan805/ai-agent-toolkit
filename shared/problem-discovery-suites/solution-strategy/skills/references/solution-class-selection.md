# Solution Class Selection Reference

## Purpose
This document specifies the 17 standardized Solution Classes, their operational boundaries, prerequisite constraint profiles, and architectural trade-offs. The goal is to always select the **least complex solution class** that fully satisfies the validated problem evidence.

---

## The 17 Solution Classes Taxonomy

### Tier 1: Non-Software Interventions (Complexity: 0/5)
1. **`CHECKLIST_OR_SOP`**: Operational written instructions or verification card. Zero code.
2. **`STRUCTURED_SPREADSHEET`**: Excel/Sheets template with data validation and formulas. Zero code.
3. **`MANUAL_CONCIERGE_SERVICE`**: Human-operated service testing viability before code. Zero code.
4. **`PROCESS_OR_POLICY_REDESIGN`**: Organizational streamlining or existing SaaS reconfiguration. Zero code.

### Tier 2: Local & Single-User Utilities (Complexity: 1/5)
5. **`LOCAL_SCRIPT`**: Standalone, single-file script (Python/Bash/Node) run on demand.
   - *Prerequisites*: `single_user_only = TRUE`, `local_data_only = TRUE`, technical operator.
   - *Trade-off*: Lowest build overhead; requires CLI familiarity from the operator.
6. **`CLI_UTILITY`**: Structured command-line tool with flags, subcommands, help menus, and exit codes.
   - *Prerequisites*: `single_user_only = TRUE`, local/remote parameters, developer or sysadmin operator.
   - *Trade-off*: Easy to automate via cron or CI/CD; unsuitable for non-technical office staff.
7. **`DESKTOP_APP`**: Native OS application (GUI) running locally.
   - *Prerequisites*: `desktop_os_access_required = TRUE`, non-technical operator needing local GUI.
   - *Trade-off*: Rich OS access (system tray, local file tree); high distribution and OS packaging friction.

### Tier 3: Surface Extensions & Browser Automations (Complexity: 2/5)
8. **`BROWSER_EXTENSION`**: Manifest V3 extension injecting content scripts or side panels.
   - *Prerequisites*: `browser_only_surface = TRUE`, interaction with third-party web pages without official APIs.
   - *Trade-off*: Direct context in operator's active tab; high fragility to third-party DOM changes and Web Store review delays.
9. **`BROWSER_AUTOMATION`**: Headless browser script (Playwright/Puppeteer) automating UI flows.
   - *Prerequisites*: `api_integrations_available = FALSE`, repeated web workflow, scheduled execution.
   - *Trade-off*: Can bypass lack of APIs; high operational maintenance due to bot detection and UI drift.

### Tier 4: Integrations & Headless Services (Complexity: 2.5/5)
10. **`INTEGRATION_SERVICE`**: Background daemon synchronizing data between two or more external APIs.
    - *Prerequisites*: `api_integrations_available = TRUE`, `scheduled_background_execution_required = TRUE`.
    - *Trade-off*: Highly reliable with official APIs; requires token management, rate limit handling, and alerting.
11. **`WEBHOOK_HANDLER`**: Serverless or lightweight endpoint receiving and routing push events.
    - *Prerequisites*: `event_driven_trigger_required = TRUE`, `api_integrations_available = TRUE`.
    - *Trade-off*: Real-time instant reaction; requires signature validation, retry idempotency, and high uptime.

### Tier 5: Web Applications & Internal Tools (Complexity: 3/5)
12. **`INTERNAL_TOOL`**: Administrative dashboard for authenticated internal team members (Retool, Appsmith, or simple CRUD).
    - *Prerequisites*: `multi_user_required = TRUE`, enterprise internal use, no public billing or signups needed.
    - *Trade-off*: Rapid deployment, bounded user count; restricted to corporate VPN or internal SSO.
13. **`STATIC_SITE_OR_JAMSTACK`**: Pre-rendered informational or client-side interactive tool.
    - *Prerequisites*: Low computational complexity, no private server state, public distribution.
    - *Trade-off*: Near-zero hosting cost, high global performance; cannot maintain private multi-tenant databases.
14. **`SINGLE_USER_WEB_APP`**: Hosted web application designed for a single user/organization with isolated database or local storage.
    - *Prerequisites*: Cross-device web access needed, but no cross-organization data isolation required.
    - *Trade-off*: Web convenience without complex multi-tenant isolation or RBAC overhead.

### Tier 6: Multi-Tenant SaaS & Platforms (Complexity: 5/5)
15. **`MULTI_TENANT_SAAS`**: Full-fledged cloud platform with tenant isolation, subscription billing, RBAC, background queues, and shared infrastructure.
    - *Prerequisites*: Multi-tenant data isolation, recurring commercial WTP, ongoing operational value.
    - *Trade-off*: High revenue leverage; extreme engineering complexity, high hosting costs, SOC2/security obligations.
16. **`API_PLATFORM`**: Hosted API service consumed by external developer code or third-party platforms.
    - *Prerequisites*: Developer audience, programmatic consumption, metering, rate-limiting.
    - *Trade-off*: High developer stickiness; demanding backward-compatibility and documentation requirements.
17. **`EMBEDDED_LIBRARY_OR_SDK`**: Reusable code package (npm, PyPI, Go module) imported into developer codebases.
    - *Prerequisites*: In-process execution, zero network overhead, client-side embedding.
    - *Trade-off*: Zero hosting cost; version deprecation and multi-runtime support overhead.

---

## Solution Class Decision Matrix

| Solution Class | Single User? | Multi User? | Cloud Sync? | APIs Exist? | Background Job? | Recurring WTP? |
|---|---|---|---|---|---|---|
| `CHECKLIST_OR_SOP` | YES | Optional | NO | N/A | NO | NO |
| `STRUCTURED_SPREADSHEET` | YES | NO | Optional | NO | NO | NO |
| `LOCAL_SCRIPT` | YES | NO | NO | Optional | Optional | NO |
| `CLI_UTILITY` | YES | NO | Optional | Optional | Optional | NO |
| `BROWSER_EXTENSION` | YES | NO | Optional | NO (DOM-based) | NO | Low/Optional |
| `INTEGRATION_SERVICE` | N/A | N/A | YES | YES | YES | Medium |
| `WEBHOOK_HANDLER` | N/A | N/A | Optional | YES | Event-driven | Medium |
| `INTERNAL_TOOL` | NO | YES | YES | YES | Optional | Internal ROI |
| `MULTI_TENANT_SAAS` | NO | YES | YES | YES | YES | Mandatory (YES) |

---

## Comparative Trade-off Evaluations

### CLI Utility vs. Browser Extension
- If the workflow operates inside a specific web portal (e.g. LinkedIn, AWS console) without an API: Choose `BROWSER_EXTENSION`.
- If the workflow processes local files, directories, or developer git repos: Choose `CLI_UTILITY`.

### Integration Service vs. Full SaaS
- If the core problem is simply keeping Tool A and Tool B in sync without a unique UI: Choose `INTEGRATION_SERVICE`.
- Do not build a SaaS product when a background integration service completely solves the problem.
