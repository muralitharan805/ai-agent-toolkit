# 35-Point Evidence Scoring Matrix & Willingness to Pay (WTP) Guide

## Overview

The 35-Point Evidence Scoring Matrix provides a rigorous, mathematical boundary to qualify problem candidates before writing code. Scoring must be calculated strictly from source-backed discovery logs, never from hypothetical assumptions.

---

## The 7 Scoring Dimensions (1–3–5 Scale)

### 1. Frequency
- **1 Point**: Rare or ad-hoc (once a quarter or annually).
- **3 Points**: Monthly routine (e.g. monthly billing reconciliation).
- **5 Points**: Daily or weekly operational bottleneck (e.g. daily shipment dispatch, daily invoice clearing).

### 2. Consequence & Willingness to Pay (WTP)
- **1 Point**: Minor nuisance; zero budget allocated; users shrug off the problem.
- **3 Points**: Noticeable operational friction; modest ad-hoc software spend ($10–$30/mo); occasional overtime.
- **5 Points**: Direct financial loss, regulatory compliance penalty, customer churn, or acute **Active WTP Signals**:
  * Paying \$50–\$200/month for multi-step Zapier or Make.com automations.
  * Paying monthly fees to Virtual Assistants or freelancers for manual data entry.
  * Allocating $\ge 5$ internal developer or ops hours per month maintaining custom glue scripts.

### 3. Workaround Strength & Economic Friction
- **1 Point**: No workaround attempted; task is ignored or accepted as-is.
- **3 Points**: Basic manual checklist or standard notepad notes.
- **5 Points**: Maintained multi-tab spreadsheet with macros/VLOOKUPs, dedicated internal scripts, or paying for multiple disconnected SaaS tools just to bridge a single data gap.

### 4. Evidence Quality (5-Level Ladder)
- **1 Point**: Anecdote, personal opinion, or Level 4/5 secondary interpretation.
- **3 Points**: Level 2/3 independent corroboration (multiple unconnected G2/Capterra/Reddit reviews).
- **5 Points**: Level 1/2 primary behavioral/verbal evidence (direct screen recordings, real invoices, SOP spreadsheets, JSON comment trees).

### 5. Segment Reach
- **1 Point**: Isolated problem unique to a single company or person.
- **3 Points**: Observed across several similar companies or roles.
- **5 Points**: Clear, repeatable pattern across an entire recognized industry vertical or role.

### 6. Alternative Gap
- **1 Point**: Strong, affordable modern SaaS alternatives fit the workflow well.
- **3 Points**: Partial fit; existing tools solve 70% but miss key edge cases.
- **5 Points**: Alternatives are prohibitively expensive enterprise suites ($500+/mo), deprecated legacy systems, or completely bypassed due to complexity.

### 7. Access to Validation
- **1 Point**: Target users are inaccessible (e.g. C-suite executives behind corporate gatekeepers).
- **3 Points**: Moderate access via LinkedIn outreach, specialized forums, or secondary connections.
- **5 Points**: Direct, immediate access to several active practitioners willing to review workflows.

---

## Decision Thresholds

| Score Range | Classification | Action Required |
|---|---|---|
| **0 – 14 PTS** | **REJECT / PARK** | Cease research immediately. Do not design or code solutions. |
| **15 – 22 PTS** | **INVESTIGATE** | Gather stronger primary evidence; do NOT jump to solution design. |
| **23 – 28 PTS** | **EVIDENCE-BACKED HYPOTHESIS** | Conduct focused expert interviews and thorough alternative audits. |
| **29 – 35 PTS** | **STRONG VALIDATION CANDIDATE** | Validate workflow with independent users and begin prototype scoping. |

---

## Commercial "Already Solved" Audit Guard

Before confirming any candidate $\ge 23$ points, execute two search queries:
1. `best software for [extracted workflow]`
2. `alternative to [workaround tool] for [niche]`

### Stop Check Trigger:
If $\ge 3$ dedicated modern SaaS products exist under \$50/month with active positive reviews solving this exact workflow, **immediately trigger Stop Check #3 and park/archive the candidate**.

A problem is considered **Underserved** only if alternatives are:
1. Bloated enterprise suites requiring $500+/mo commitments and sales demo calls.
2. Unmaintained or deprecated software with broken integrations.
3. Missing essential niche localization, tax, or legal compliance mandates.

---

## The 6 Mandatory Stop Checks

Immediately reject or park a problem candidate if ANY condition is met:
1. **Infrequent & Low Impact**: Pain occurs rarely and carries no financial or operational cost.
2. **No Real Workaround**: Users do not modify their daily behavior or spend resources to fix it.
3. **Alternative Fits Well**: An affordable SaaS (< \$50/mo) already solves the problem effectively.
4. **Single-Source Bias**: Evidence originates from only one individual or a copied marketing blog.
5. **Internal Training Issue**: Friction is caused by poor employee onboarding rather than software gaps.
6. **Unreachable Audience**: The target decision-makers cannot realistically be contacted for feedback.
