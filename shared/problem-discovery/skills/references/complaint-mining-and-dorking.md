# Automated Complaint Mining & Multi-Platform Search Dorking

## Overview

Instead of guessing what problems exist, modern product researchers employ **automated complaint mining pipelines**. By systematically scanning developer forums, operational communities, and software review sites for high-intent dissatisfaction patterns, builders uncover unaddressed software gaps grounded in real-world friction.

---

## 1. Multi-Platform Google Dorking Cheat Sheet

Search dorking uses targeted Google search operators to bypass SEO marketing landing pages and surface authentic operator discussions:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      SEARCH DORK OPERATORS MATRIX                      │
├───────────────────┬────────────────────────────────────────────────────┤
│ Reddit            │ site:reddit.com/r/[sub] "hours manually"           │
│ B2B Reviews       │ site:g2.com/products/*/reviews "what do you dislike│
│ Vertical Stores   │ site:apps.shopify.com/reviews "sync error"         │
│ Browser Extension │ site:chromewebstore.google.com "broken" "update"   │
│ Job Postings      │ site:indeed.com "reconcile" "advanced Excel"       │
└───────────────────┴────────────────────────────────────────────────────┘
```

### 1. Reddit Operator Community Dorks
- `site:reddit.com inurl:comments "why is there no tool to"`
- `site:reddit.com inurl:comments "our team is stuck using excel for"`
- `site:reddit.com inurl:comments "spend hours every week" "manually"`
- `site:reddit.com inurl:comments "nightmare to reconcile" OR "painful to track"`
- `site:reddit.com inurl:comments "looking for a simple alternative to [Tool]"`

### 2. Software Review Gaps (G2, Capterra, Trustpilot)
- `site:g2.com/products/*/reviews "what do you dislike" "missing"`
- `site:g2.com/products/*/reviews "workaround" OR "export to excel"`
- `site:capterra.com "cons" OR "manual export" OR "lack of integration"`
- `site:trustpilot.com/review/* "pricing increase" OR "broken sync" OR "lost data"`

### 3. Vertical App Store & Plugin Directory Dorks
Competitor review breakdowns in specialized app ecosystems reveal immediate plug-in or micro-SaaS opportunities:
- **Shopify App Store**:
  `site:apps.shopify.com/reviews "does not sync" OR "tax mismatch" OR "inventory bug"`
- **WordPress / WooCommerce Directory**:
  `site:wordpress.org/plugins "breaks" OR "slow" OR "fatal error" OR "refund"`
- **Chrome Web Store**:
  `site:chromewebstore.google.com/detail "no longer works" OR "stopped working" OR "manifest v3"`

### 4. Job Posting Dorks (Hunting Paid Glue-Work)
Companies do not hire employees to solve imaginary problems. When job descriptions mandate spending hours in spreadsheets, they are advertising an unsolved software integration:
- `site:indeed.com "must have advanced Excel" "manual reconciliation"`
- `site:linkedin.com/jobs "responsible for daily data entry" "cross-reference"`

---

## 2. Reddit Raw JSON Extraction Protocol

When researching complaints on Reddit via HTTP tools:
1. Append `.json` to the public URL:
   `https://www.reddit.com/r/accounting/comments/xyz/thread_title.json`
2. This bypasses client-side JavaScript rendering, ads, and layout elements, returning a clean, structured JSON tree of comments, timestamps, and upvotes.
3. Filter comments for sentiment indicators: `"workaround"`, `"VLOOKUP"`, `"nightmare"`, `"formula"`, `"broke"`.

---

## 3. Automated Complaint Ingestion Pipelines

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   AUTOMATED COMPLAINT INGESTION                        │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Real-Time Alerting (e.g., F5Bot / Webhooks)                         │
│    Monitors keywords: "hate [competitor]", "wish there was a script"   │
│                                                                        │
│ 2. Scraped Review Extraction (e.g., Apify Actors / Headless)           │
│    Extracts 1-star & 2-star reviews from G2, Capterra, Shopify Store   │
│                                                                        │
│ 3. LLM Cluster Deconstruction                                          │
│    Parses raw comment trees into 14-node workflow schemas              │
└────────────────────────────────────────────────────────────────────────┘
```

### Automated Query Generation Algorithm
For any investigated domain or software tool, generate structured discovery queries:

```typescript
export interface DomainQueryBundle {
  readonly domain: string;
  readonly communityQueries: readonly string[];
  readonly reviewGaps: readonly string[];
  readonly appStoreQueries: readonly string[];
}

export function generateDiscoveryQueries(domain: string): DomainQueryBundle {
  return {
    domain,
    communityQueries: [
      `site:reddit.com inurl:comments "${domain}" "hours every week"`,
      `site:reddit.com inurl:comments "${domain}" "spreadsheet workaround"`,
      `site:reddit.com inurl:comments "${domain}" "how do you guys track"`,
      `site:news.ycombinator.com "${domain}" "painful" OR "broken"`
    ],
    reviewGaps: [
      `site:g2.com/products "${domain}" "what do you dislike"`,
      `site:capterra.com "${domain}" "manual export" OR "clunky"`,
      `site:trustpilot.com/review "${domain}" "duplicate" OR "support"`
    ],
    appStoreQueries: [
      `site:apps.shopify.com/reviews "${domain}" "sync fails"`,
      `site:wordpress.org/plugins "${domain}" "data lost"`
    ]
  };
}
```
