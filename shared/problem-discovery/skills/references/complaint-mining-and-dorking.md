# Automated Complaint Mining, Search Dorking & Query Refinement

## Overview

Instead of searching for "SaaS ideas 2026" (which yields generic affiliate listicles), disciplined product researchers **search for the actual work people are performing and where it repeatedly breaks**.

> **The Core Realization**: You do not need to discover a problem that "nobody in the world has ever solved." An existing solution may be too expensive, complicated, inaccessible, or misaligned with a specific group's operational reality. That gap is the opportunity. However, not finding a tool via search is never proof that a tool does not exist.

---

## 1. The Atomic Search Unit

Every query and investigation must be anchored on the **Atomic Search Unit**:

$$\textbf{Search Unit} = \textbf{Specific Person} + \textbf{Specific Task} + \textbf{Current Workaround} + \textbf{Consequence}$$

- **Hypothetical Example**:
  *"Small construction contractors manually transfer worker attendance and advance payments from WhatsApp into Excel at month-end, resulting in salary miscalculations and site disputes."*
  - **Actor**: Small construction contractor
  - **Task**: Worker attendance and advance-payment tracking
  - **Workaround**: Manual month-end transfer from WhatsApp messages into Excel
  - **Consequence**: Salary miscalculations, absorbed payroll mistakes, and worker disputes
- **Contrast**: Calling this a generic *"Construction worker management SaaS"* destroys all operational precision.

### The Signal Translation Matrix:

| What You Want to Find | The Specific Signal to Search For |
|---|---|
| **Real-world problem** | Repeated operational failure, delay, or missed commercial outcome |
| **Manual glue-work** | Copy-paste routines, retyping, cross-sheet comparison, repetitive follow-up |
| **Complex workflow** | Multiple tools, handoffs, approval delays, and unmanaged exceptions |
| **Recurring need** | The identical task and failure consequence across independent operators |

> [!IMPORTANT]
> **Curiosity vs Complaint vs Buying Demand**
> - **Upvotes on Reddit**: Represent curiosity or casual agreement.
> - **Vocal complaints**: Represent emotional annoyance.
> - **Maintaining a daily workaround**: Strongest proof of authentic operational demand.

---

## 2. The Practical "Grep the Web" Query System

Use Google search operators (`site:`, exact match `"..."`, exclusions `-term`, filetypes `filetype:`) to target practitioner discussions ([Google Search Operator Guidance](https://support.google.com/websearch/answer/2466433?hl=en)).

### Standard Search Syntax:
$$\texttt{site:PLATFORM [ROLE_OR_TOOL] [TASK] [FRICTION]}$$

### 1. The Comprehensive Pain Phrase Dictionary:
When constructing queries, combine domain roles with phrases people naturally use when describing friction:
- `"takes hours"` • `"every month I have to"` • `"manually enter"` • `"copy and paste"`
- `"spreadsheet"` • `"anyone know a tool"` • `"there must be a better way"` • `"how do you manage"`
- `"tired of"` • `"frustrating"` • `"missing data"` • `"keep track of"` • `"reconcile"`
- `"workaround"` • `"too expensive"` • `"doesn't support"` • `"wish it could"` • `"alternative to"`
- `"still using Excel"` • `"export to CSV"` • `"bulk upload"` • `"duplicate entries"`

---

## 3. Multi-Platform Search Templates

### A. Community & Reddit Complaints
```text
site:reddit.com "every month I have to" invoice
site:reddit.com "manually enter" "spreadsheet" landlord
site:reddit.com/r/smallbusiness "takes hours"
site:reddit.com/r/accounting "wish there was"
site:reddit.com/r/farming "how do you keep track"
site:community.shopify.com "payout" "spreadsheet"
site:wordpress.org/support/topic/ "export" "manually"
```

### B. Existing Software Gaps & Negative Reviews ([G2](https://www.g2.com/), Capterra)
G2 exposes millions of business software reviews. Focus strictly on negative reviews and the "What do you dislike?" section rather than aggregate star ratings:
```text
"[product name]" "doesn't support"
"[product name]" "too expensive"
"[product name]" "manual workaround"
site:g2.com/products "[feature]" reviews
site:capterra.com "[software category]" "cons"
```

### C. Long Workflow Discovery via Public Filetypes (SOPs & Templates)
If an organization maintains a public 20-column Excel template, standard operating procedure (SOP), or multi-step compliance checklist, they are advertising an unsolved workflow:
```text
filetype:pdf "standard operating procedure" reconciliation
filetype:pdf "monthly process" "spreadsheet"
filetype:xlsx template inventory audit
filetype:docx checklist compliance "step by step"
"submit" "portal" "Excel" "download CSV" "upload" "manually"
```

### D. Job Postings Hunting Paid Human Glue-Work
When a company spends $30,000–$60,000/year to hire an employee to manually type data between systems, that friction is already consuming real cash:
```text
site:linkedin.com/jobs "manually reconcile"
site:indeed.com "maintain spreadsheets" "weekly report"
site:indeed.com "job description" "data entry" "multiple systems"
```

### E. Developer Gaps & GitHub Issues
GitHub Issue search supports complex Boolean logic and nested queries ([GitHub Issue Search Update](https://github.blog/changelog/2025-05-13-issues-search-now-supports-nested-queries-and-boolean-operators/)):
```text
site:github.com/issues "feature request" "export CSV"
site:github.com/issues "manual workaround"
site:github.com/issues "bulk import"
site:github.com/issues "currently not supported"
```

### F. Hacker News & Product Hunt
- **Hacker News**: Search practitioner discussions via `site:news.ycombinator.com "Ask HN" "how do you manage"` or programmatically query the [HN Algolia Search API](https://hn.algolia.com/api).
- **Product Hunt**: Do not look at launch upvotes; search comments for missing features: `site:producthunt.com/posts "alternative"`, `site:producthunt.com "too expensive"` or query the [Product Hunt GraphQL API](https://api.producthunt.com/v2/docs).

### G. Local / India / Semi-Urban Problem Dorks
Hyper-local and village-level problems rarely appear in English SaaS threads. Use local institutional queries:
```text
"[district name]" complaint application process
"[scheme name]" documents required confusion
"[occupation]" register Excel India
"[Tamil Nadu department]" grievance report PDF
"[district]" tender manual record system
"[municipality]" complaints water tax certificate
```
*Offline Ground Truth*: In semi-urban clusters, the best sources are: CSC / e-Sevai operators, document writers, small clinic receptionists, school administrators, milk collection centres, agricultural input shops, and local trade association secretaries.

---

## 4. Google Trends: Supporting Evidence vs False Validation

Google Trends allows comparing up to 5 terms, analyzing regional interest, and identifying seasonal spikes ([Google Trends Guide](https://developers.google.com/search/docs/monitor-debug/trends-start)).

> [!WARNING]
> **Google Trends $\ne$ Product Validation**
> As Google's official documentation notes, Trends data reflects search interest relative to total queries, not a scientific poll or purchasing intent ([Google Trends FAQ](https://support.google.com/trends/answer/4365533?hl=en)).  
> **"People search for X" DOES NOT mean "People will pay for X."** Use Trends strictly as secondary supporting context, never as primary market proof.

---

## 5. Platform Source Matrix: What to Learn vs What NOT to Assume

| Source Platform | What to Learn | What NOT to Assume |
|---|---|---|
| **Reddit / Operator Forums** | Unvarnished stories, active workarounds, emotional pain | Upvotes = commercial market size |
| **Product Support Forums** *(WordPress, Shopify)* | Exact task steps, failure points, attempted user fixes | Every reported bug or gap = a viable new product |
| **Review Platforms** *(G2, Capterra, App Stores)* | Gaps, missing integrations, and pricing complaints | An old 1-star complaint is still unresolved today |
| **GitHub Issues** | Developer friction, reproducible technical limitations | A high-starred feature request = willingness to pay |
| **Job Postings** *(Indeed, LinkedIn)* | Recurring tasks companies actively pay human salaries for | The entire employee role can be replaced by software |
| **Tutorials & Templates** | How work is currently done step-by-step | Popularity of a tutorial = unmet software need |
| **Local Field Observation** | Offline, physical, and informal cash/notebook workflows | One local shop represents the universal market |

---

## 6. Case Study: Interpreting Live Support Complaints

A real-world analysis of live WordPress support threads demonstrates why superficial clustering leads to flawed products:

| Observed Support Evidence | Rigorous Interpretation | Pitfall to Avoid |
|---|---|---|
| *User manually copies order variants from each order and formats them.* ([Source](https://wordpress.org/support/topic/can-i-download-orders-to-xlsx-with-variants-showing-2/)) | Real manual-work signal; support suggested existing advanced export filters. | Do not assume no tool exists before checking built-in capabilities. |
| *User reports custom fields in export appear empty; confirms another plugin solved it.* ([Source](https://wordpress.org/support/topic/ability-to-export-orders-to-include-custom-fields/)) | Valid technical gap, but **an existing alternative plugin already completely solved it**. | Do not build a tool for an issue that already has a working $0 plugin. |
| *Request for customers to download their own individual order CSV from frontend account page.* ([Source](https://wordpress.org/support/topic/customers-download-csv-of-an-order-from-frontend/)) | Valid research lead; recurring demand and commercial willingness to pay remain unverified. | Do not write code before confirming if other store owners want this. |

> [!CAUTION]
> **The Generic Solution Fallacy**
> Never bundle these 3 distinct threads into a generic *"WooCommerce CSV App"*. The actor, output requirements, and available alternatives are completely different.

---

## 7. Architecture of an Automated Problem-Mining System

For developers building continuous background intelligence tools, implement this 4-tier pipeline:

1. **Collector**: Ingest from permitted APIs (Reddit OAuth, Hacker News Algolia, RSS feeds, permitted exports) rather than blind scrapers ([Reddit Data API Guidance](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki)).
   ```json
   {
     "source": "reddit",
     "url": "https://reddit.com/r/smallbusiness/...",
     "date": "2026-09-10",
     "persona": "small landlord",
     "pain_phrase": "manually enter spreadsheet",
     "current_workaround": "Excel",
     "frequency": "monthly",
     "impact": "3 hours wasted per property",
     "requested_solution": "bulk bank statement import"
   }
   ```
2. **Classifier**: Tag raw items into functional categories:
   `Manual entry` • `Reconciliation` • `Document conversion` • `Tracking` • `Scheduling` • `Compliance` • `Communication` • `Reporting` • `Integration` • `Local-language`
3. **Clusterer**: Group by the underlying operational job:
   - *"Copy values from PDF"* + *"Type bank statement into Excel"* + *"Enter paper invoice data"*  
   $\longrightarrow$ Single Cluster: **Document to Structured Data Extraction**.
4. **100-Point Operational Prioritization Rubric**:
   - Pain severity: **15 pts**
   - Problem frequency: **15 pts**
   - Time/money/risk impact: **15 pts**
   - Existing workaround effort: **10 pts**
   - Reachability of users: **10 pts**
   - Active spending on workarounds: **10 pts**
   - 2–4 week MVP feasibility: **10 pts**
   - Competition / fit gap: **10 pts**
   - Personal domain advantage: **5 pts**
   - **Triage**:
     - $\ge 75$ PTS: Schedule live practitioner interview/pilot immediately.
     - $60–74$ PTS: Collect more corroborating evidence.
     - $< 60$ PTS: Archive; do NOT write software.
