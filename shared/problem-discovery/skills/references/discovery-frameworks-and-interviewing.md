# Operational Discovery Frameworks & Field Interviewing Protocols

## Overview

High-conviction software opportunities are discovered by observing operators in their natural working environments, not by soliciting feature wishlists. When people describe their problems in interviews, they frequently request local optimizations to visible symptoms while concealing root operational bottlenecks.

This guide outlines structured discovery frameworks (The PAIN Model, Jobs to Be Done, The Mom Test, Service Blueprints, Desirability-Feasibility-Viability) and field interview protocols applicable to any domain.

---

## 1. The PAIN Discovery Framework

When analyzing any reported complaint or friction, extract 4 precise operational dimensions:

$$\textbf{P} \text{erson} \quad+\quad \textbf{A} \text{ctivity} \quad+\quad \textbf{I} \text{ncident} \quad+\quad \textbf{N} \text{umber}$$

- **Person**: Exactly who faces the friction? (Job title, role, company/fleet size, literacy).
- **Activity**: What specific operational outcome are they attempting to complete?
- **Incident**: Where precisely does the breakdown occur? (Which handoff, format mismatch, or portal cutoff?).
- **Number**: What is the verifiable recurrence and measurable consequence? (Hours wasted, money lost, penalty rate).

### Concrete Example:
- **Person**: Small fleet bookkeeper (managing 15 transport trucks)
- **Activity**: Quarterly fuel tax reconciliation
- **Incident**: Cross-referencing physical paper fuel receipts against telematics GPS mileage logs
- **Number**: Occurs every quarter; consumes 2–3 full workdays of manual Excel transcription
> *"Accounting is difficult"* is an unbuildable abstraction. The specific statement above is an actionable, high-conviction product opportunity.

---

## 2. Unified Frameworks: Different Tools for Different Questions

Different stages of discovery require different analytical lenses:

| Framework | Core Purpose | Key Inquiry |
|---|---|---|
| **The PAIN Model** | Extract person, task, failure incident, and measurable consequence | *"Who suffers, during what activity, at what incident, with what numbers?"* |
| **Jobs to Be Done (JTBD)** | Understand the underlying outcome the user wants to achieve | *"What progress is the user trying to make when this task arises?"* |
| **Customer Discovery / Mom Test** | Collect historical factual behavior rather than speculative opinions | *"What did you actually do the last time this broke?"* |
| **Workflow Mapping / Service Blueprint** | Locate steps, people, handoffs, delays, and failure points | *"Where does data pause, wait for approval, or require manual re-entry?"* |
| **Desirability–Feasibility–Viability** ([Strategyzer](https://www.strategyzer.com/library/how-to-systematically-reduce-the-risk-uncertainty-of-new-ideas)) | Systematically reduce risk across demand, technical delivery, and sustainability | *"Is there authentic demand? Can we build it? Can we sustain it without heavy overhead?"* |

### The Master Discovery Sequence:
$$\textbf{Observe} \longrightarrow \textbf{Map} \longrightarrow \textbf{Corroborate} \longrightarrow \textbf{Check Alternatives} \longrightarrow \textbf{Test Smallest Intervention} \longrightarrow \textbf{Measure Behavior}$$

---

## 3. Large Workflow Deconstruction & Isolating the Break Point

Large operational workflows look complex from the outside:
$$\text{Request arrives} \rightarrow \text{Checks details} \rightarrow \text{Copies into tool} \rightarrow \text{Asks for approval} \rightarrow \text{Waits} \rightarrow \text{Corrects missing data} \rightarrow \text{Produces output} \rightarrow \text{Confirms}$$

A large workflow by itself is not an opportunity. You must isolate the **repeated small failure point**. At every step of the chain, ask these **5 Diagnostic Questions**:

1. **Who is doing this step?** (Job title, vernacular literacy, device used).
2. **What exact information is required?** (Format, schema, completeness).
3. **Why does it pass to the next person or tool?** (Policy, technical limitation, sign-off).
4. **Where does idle waiting or rework occur?** (Bottlenecks, back-and-forth messaging).
5. **What is the consequence if this step fails?** (Financial loss, delay, wrong print/shipment, compliance fine).

---

## 4. Field Interviewing: The Mom Test Protocol

> **The Cardinal Axiom**: Never ask customers what they think of an idea. Ask them what they did the last time they faced the problem.

People are naturally polite and encouraging. If you ask *"Would you use or pay for an app that does X?"*, respondents routinely answer affirmatively out of courtesy. Polite encouragement is easily misread as validated commercial demand.

### The 7 Grounded Behavioral Field Questions:
During field interviews, use these grounded behavioral prompts:

1. *"When was the last time you performed this task?"* (Anchors to a specific recent date).
2. *"Can you walk me through the step-by-step actions you took?"* (Surfaces actual workflows).
3. *"What exact files, tools, or registers did you touch?"* (Identifies real software/paper touchpoints).
4. *"Where in that sequence did you spend the most time or feel the most frustration?"* (Isolates the bottleneck).
5. *"When was the last time a mistake slipped through? What was the financial or operational consequence?"* (Measures severity).
6. *"How much are you currently paying for tools, freelancers, or services to manage this today?"* (Uncovers active budgets).
7. *"Can you show me an anonymized screenshot, spreadsheet, or sample report?"* (Produces primary artifacts).

### The Golden Pilot Commitment Question:
At the conclusion of an interview, the single most revealing question that separates real demand from polite conversation is:

> **"If I prepare a simple working version of this tool, are you ready to pilot test it with your real data during your next work cycle?"**

- If they say *"Send me an email whenever it's live"*, interest is weak.
- If they immediately offer their next schedule date and agree to provide sample test data, **authentic validation is confirmed**.

---

## 5. Inaction Root Cause Analysis

When an operator reveals they maintain no active software tool or spreadsheet, **do not automatically reject the problem**. Distinguish between two completely different operational states:

1. **Inaction with Low Consequence**:
   - The user doesn't bother doing anything because ignoring the task causes zero measurable loss.
   - $\longrightarrow$ **REJECT / PARK**. No adoption or budget will ever materialize.
2. **Inaction under Severe Consequence (Task Abandonment)**:
   - The user attempted to find tools, found only complex English enterprise ERPs costing $5,000+/year requiring desktop PCs, and gave up under duress.
   - The operational consequence remains severe (e.g. repeated inventory shortage, tax penalties, absorbed rework costs).
   - $\longrightarrow$ **HIGH-CONVICTION LATENT OPPORTUNITY**. Accessible, simple micro-tools thrive in this exact vacuum.

---

## 6. Counter Shadowing Protocol (Local & Retail Field Work)

To observe authentic operational behavior without prompting:
1. **Visit During Peak Transition Hours**: Morning inventory arrivals (8:00–10:00 AM) or daily closing (7:00–9:00 PM).
2. **Silent Observation**: Note tab-switching, copying numbers from paper receipts to phones, and customer interruptions.
3. **The "Show Me Your Register" Inquiry**: Ask to see the dog-eared register or WhatsApp message group where orders were tracked yesterday.
4. **Shadow Systems**: Identify personal cheat sheets, desktop folders named `FINAL_v2_USE_THIS.xlsx`, or margin scribbles in physical notebooks.
