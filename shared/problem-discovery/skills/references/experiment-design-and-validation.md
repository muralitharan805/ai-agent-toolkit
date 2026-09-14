# Experiment Design, Empirical Validation & Distribution Gates

## Overview

A high research priority score ($\ge 28$ PTS) is **not validation**—it is simply a green light to design a rapid, low-cost experiment. True validation requires **observed operational usage, repeated retention, or verified economic commitment**.

Before writing backend code, provisioning databases, or deploying infrastructure, builders must pass through the **7 Decision Gates**, define the **Micro-SaaS Wedge**, execute the **smallest trial experiment**, and let the workflow dictate the technical format.

---

## 1. The 7 Decision Gates Before Building Software

Before writing a single line of production code, every candidate must have documented evidence addressing all 7 gates:

| Decision Gate | What Must Be Proven by Evidence | Why It Matters |
|---|---|---|
| **1. Real Need** | Recent concrete incidents with measurable financial, time, or regulatory consequence | Eliminates theoretical complaints and cosmetic preferences |
| **2. Repeatability** | The identical task and failure mechanism occurring across independent operators | Prevents building custom software for a single user's quirk |
| **3. Existing Solution Gap** | Documented, specific reasons why current tools don't fit (price, language, devices, workflow) | Prevents competing against entrenched software users already love |
| **4. Software Suitability** | Structured inputs, clear business rules/outputs, and manageable edge cases | Ensures software actually solves the root cause rather than an internal human policy issue |
| **5. Reachability** | Target operators can be directly accessed for live testing within 48 hours | If you cannot talk to the first 5 users, you cannot distribute the product |
| **6. Adoption Viability & Wedge** | Clear competitive wedge (cheaper, simpler, local language, offline, specific format) | *"Same product but I code better"* is NOT viable differentiation |
| **7. Data & Legal Safety** | Safe from fragile scraping, unstable portal dependencies, or catastrophic liabilities | Avoids building on quicksand or facing regulatory bans |

### Gate 6: The 10 Valid Competitive Wedges:
Existing tools may exist, but fail for a specific segment. Your entry wedge must possess at least one of these 10 advantages:
1. **Cheaper**: 5x–10x more affordable for solo operators.
2. **Simpler**: 1-click single-purpose utility vs bloated 50-feature enterprise ERP.
3. **Local Language**: Vernacular language interface (Tamil, Hindi) vs English-only.
4. **Country-Specific Compliance**: Aligned with local statutory forms (e.g. GST, e-Way bill).
5. **Mobile-First**: Designed for 6-inch smartphones vs desktop Chrome.
6. **Offline / Low-Bandwidth**: Operates without continuous Wi-Fi.
7. **Specific File Format**: Direct parser for an obscure industry export format.
8. **One-Click Integration**: Pre-built bridge between two specific popular tools.
9. **Privacy / Self-Hosted**: Client-side parsing without storing sensitive data on cloud servers.
10. **Zero-Setup Speed**: Solves the task in 30 seconds without mandatory registration.

### Gate 7: Data & Legal Dependency Traps to Avoid:
Reject or re-scope candidates that rely on:
- Unauthorized scraping of hostile platforms (subject to DOM breaks or IP bans).
- Unofficial automation of government portals without stable APIs.
- Automated legal or medical decisions with catastrophic personal liability.
- Commercial redistribution of third-party data violating platform terms.

---

## 2. Micro-SaaS Wedge Scoping: Never Solve the Whole Workflow

When entering a problem space, **do not build an all-in-one platform on Day 1**.

- **Large Problem**: Complete export documentation and compliance management.
- **Bad MVP**: Building an accounting + invoicing + GST + banking + customs filing suite.
- **Good Micro-SaaS Wedge**:
  $$\textbf{e-FIRC PDF Upload} \longrightarrow \textbf{Auto-Match with Invoices} \longrightarrow \textbf{Identify Missing Remittances} \longrightarrow \textbf{CA-Ready Export}$$

*The wedge solves 100% of the acute bottleneck while requiring only 5% of the codebase.*

---

## 3. The Core Transformation Model

For a full-stack solo builder, the fastest path to shipping a working tool is the **Single Transformation Pipeline**:

$$\textbf{Input} \quad\longrightarrow\quad \textbf{Core Value} \quad\longrightarrow\quad \textbf{Output}$$

- **Input**: Raw unstandardized PDF, CSV, Excel, or manual form values.
- **Core Value**: Clean, compare, calculate, validate, or reconcile data across rules.
- **Output**: Clean discrepancy report, statutory filing format, or actionable checklist.

---

## 4. Check Non-Software Solutions First

Before building custom code, evaluate whether the bottleneck can be eliminated through non-software interventions:
- **A Pre-Formatted Template**: An Excel / Google Sheet with pre-built formulas or conditional formatting.
- **A Configuration Fix**: Enabling a hidden setting or built-in filter in existing software.
- **A Structured Guide / SOP**: A 1-page printable checklist for employees or customers.
- **An Existing Integration**: A basic Zapier / Make webhook connecting two native tools.

*Architectural Principle*: If a 1-page guide or pre-formatted template solves 80% of the friction at zero engineering cost, **that guide IS the solution**.

---

## 5. The Evidence Strength Hierarchy

When evaluating user interest during research and trials, classify feedback according to the **Evidence Strength Hierarchy**:

$$\textbf{Compliment} < \textbf{Signup / Email} < \textbf{Actual Use} < \textbf{Repeat Use} < \textbf{Paid Use}$$

- **Compliment** *(Weakest)*: *"Great idea, I would totally use this!"* $\rightarrow$ Meaningless courtesy; zero behavioral commitment.
- **Signup / Email**: Entering an email on a landing page $\rightarrow$ Mild curiosity, but 90%+ drop off at installation.
- **Actual Use**: Uploading a real business file or processing a live order $\rightarrow$ Moderate evidence of utility.
- **Repeat Use** *(High-conviction)*: Returning in the next work cycle without prompting or reminders $\rightarrow$ Proof of authentic operational habituation.
- **Paid Use** *(Strongest Commercial Signal)*: Swiping a card or paying via UPI $\rightarrow$ Concrete budget commitment (note: a single payment is validation of a transaction, while repeat retention proves a sustainable business).

---

## 6. Letting the Workflow Dictate the Solution Format

Never default to a multi-tenant cloud SaaS. Choose the starting format strictly based on the operational mechanism:

| Operational Need | Suitable Technical Format | Architecture & Infrastructure |
|---|---|---|
| **Instructions / reference information** | **Static Documentation Site** | Static HTML / Markdown on Cloudflare Pages ($0 cost) |
| **Input file $\rightarrow$ Transformed output** | **Browser-Side Utility** | Standalone Angular / Vanilla JS (Client-Side WASM/Worker) |
| **Interactive local counter workflow** | **Standalone SPA / PWA** | Offline-First Angular Standalone PWA (IndexedDB) |
| **Action inside an existing web portal** | **Browser Extension** | Chrome Extension (Manifest V3 DOM injection) |
| **Shared multi-user state & cron sync** | **Backend App / Micro-SaaS** | NestJS + PostgreSQL + Stripe (Only when strictly needed) |

### SeyaliCraft & Fast-Release Strategy:
In environments like `seyalicraft.com` or lightweight VPS deployments, releasing a narrow, client-side utility on a clean public URL is the fastest way to test real organic usage:
- If users return weekly and request background cloud automation, recurring subscription billing is justified.
- **Never invent recurring workflows simply to justify a recurring subscription model.**

---

## 7. The 30-Day Practical Discovery Plan

Follow this disciplined 4-week execution calendar to discover, qualify, and validate a problem candidate:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   THE 30-DAY PRACTICAL DISCOVERY PLAN                  │
├────────┬─────────────────────────┬─────────────────────────────────────┤
│ Week 1 │ One Domain Selection    │ Choose 1 non-developer vertical:    │
│        │                         │ small logistics, construction subs, │
│        │                         │ export docs, clinics, schools, etc. │
├────────┼─────────────────────────┼─────────────────────────────────────┤
│ Week 2 │ 100 Pain Signals Logged │ Mine 100 raw signals across forums, │
│        │                         │ job postings, reviews, SOPs.        │
├────────┼─────────────────────────┼─────────────────────────────────────┤
│ Week 3 │ Cluster & Shortlist     │ 100 signals → 20 repeated patterns  │
│        │                         │ → 5 validated problems → 3 user     │
│        │                         │ interviews each → 1 pilot candidate.│
├────────┼─────────────────────────┼─────────────────────────────────────┤
│ Week 4 │ Concierge MVP Trial     │ Perform workflow manually for 3–5   │
│        │                         │ operators using real sample data.   │
└────────┴─────────────────────────┴─────────────────────────────────────┘
```

> [!IMPORTANT]
> **The Final Guiding Principle**
> - Do NOT start from: *"What can I build?"*
> - Start from: *"What are people repeatedly doing the hard way?"*
> - Then ask: *"Which smallest part can I remove completely?"*
>
> Your first milestone is **never "App Deployed to Production."**  
> Your true milestone is:
> > *"A real person used my solution in their actual work, received measurable benefit, and came back to use it again."*
