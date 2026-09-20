# Semantic Query Parsing, Scope Sensing & Adaptive Domain Decomposition

## Overview

Real-world users rarely submit clean, perfectly bounded research scopes. Requests typically arrive as either **ultra-broad domains** (e.g. `"India real estate"`, `"healthcare logistics"`), **messy emotional brain-dumps** with mixed signals, or **over-constrained single-feature ideas**.

This reference defines the **3-Step Parsing Engine** and the **Adaptive 5-Stream Research Lenses** used by the `problem-discovery` skill to ingest any raw prompt, preserve critical source provenance, classify scope, and decompose the domain into balanced operational workflows before generating candidate search queries.

---

## 1. The 3-Step Parsing Engine

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        THE 3-STEP PARSING ENGINE                       │
├────────────────────────────────────────────────────────────────────────┤
│ Step 1: Slot Filling & Provenance Preservation                         │
│         Extract: Domain, Geography, Operator, Task, Friction, Tools.   │
│         Preserve: Source provenance (first-hand vs second-hand report). │
│         Strip: Pure conversational greetings and filler.               │
├────────────────────────────────────────────────────────────────────────┤
│ Step 2: Scope Sensing & Adaptive Stream Allocation                     │
│         Classify: Broad vs Messy vs Narrow.                            │
│         Map into: Frontline, Handoffs, Reconciliation, Compliance,     │
│                   and Dispute default lenses (adaptable, not rigid).   │
├────────────────────────────────────────────────────────────────────────┤
│ Step 3: Atomic Search Unit & Candidate Query Formulation               │
│         Formula: Person + Task + Workaround + Consequence.             │
│         Emit: Balanced candidate search queries (hypotheses, not proof)│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step 1: Slot Filling & Provenance Preservation

Extract core operational slots from raw prompt text while distinguishing factual observations from conversational filler:

| Slot | Description | Example Extraction |
| :--- | :--- | :--- |
| `Domain` | Target industry or vertical | Real Estate, Logistics, FinTech, Healthcare |
| `Geography` | Spatial, regulatory, or regional boundary | India (Tamil Nadu / Pollachi), UK, US, Global |
| `Operator` | The specific human actor executing the work | Local broker, Sub-registrar document writer, Sales progressor |
| `Task` | The concrete business activity being performed | Token advance tracking, EC verification, Lead scheduling |
| `Friction` | Reported operational breakdown or delay | WhatsApp media disorder, advance payment delay, office queues |
| `Tools` | Software or physical artifacts currently used | WhatsApp, Excel, Paper notebook, Physical tokens |
| `Provenance` | **Source authenticity & evidence tier** | Second-hand report (*"uncle said"*), Direct operator, Online rumor |

### The Provenance Preservation Rule:
- **Discard pure conversational filler:** Strip greetings (`"hi murali"`, `"can you build an AI app that..."`).
- **PRESERVE source attribution:** Never discard phrases like `"my uncle said"`, `"a client told me"`, or `"I saw on Twitter"`. These indicate whether the input is a **first-hand direct observation (Level 1/2)** or a **second-hand / hearsay report (Level 4/5)**. Preserving provenance prevents unverified second-hand claims from masquerading as direct operational evidence.

---

## 3. Step 2: Scope Sensing & Adaptive Stream Allocation

Categorize the incoming prompt into one of three archetypes and route accordingly:

### The 3 Prompt Archetypes:

1. **Type 1: Ultra-Broad Prompt (1–3 Words)**
   - *Example:* `"India Real Estate"` or `"E-commerce logistics"`
   - *Protocol:* Decompose across the **default research lenses** to ensure balanced coverage without single-topic bias.
2. **Type 2: Messy / Emotional Brain-Dump (Paragraph of mixed issues)**
   - *Example:* `"My uncle does real estate in Pollachi, WhatsApp is messy with photos, buyers delay token advance, and sub-registrar office has huge queues for EC."`
   - *Protocol:* Extract reported frictions and map them directly into their matching streams. **Do not invent or force unrelated streams** unless the user explicitly requested broad discovery across the wider domain.
3. **Type 3: Narrow / Bounded Workflow (Specific task + actor)**
   - *Example:* `"UK conveyancing sales progression milestone chasing for estate agents"`
   - *Protocol:* **Execute existing CSV preflight first.** Check available evidence; map supported details into the 14 nodes and leave missing details explicitly as `UNKNOWN`. Do not expand into unrelated streams.

---

### The Adaptive 5-Stream Research Lenses:

Treat these streams as **default coverage lenses**, not a rigid universal taxonomy or a mandatory quota to produce five problems. Streams may overlap, and domain-specific streams may be added:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   ADAPTIVE 5-STREAM RESEARCH LENSES                    │
├───────────────────────────────┬────────────────────────────────────────┤
│ 1. Frontline / Intake Lens    │ Customer acquisition, requirements     │
│                               │ gathering, site visits, initial booking│
├───────────────────────────────┼────────────────────────────────────────┤
│ 2. Multi-Party Handoff Lens   │ Inter-entity workflows, co-broker      │
│                               │ splits, solicitor-to-agent updates     │
├───────────────────────────────┼────────────────────────────────────────┤
│ 3. Back-Office Reconciliation │ Manual Excel glue, token advances,     │
│                               │ contractor bills, bank disbursements   │
├───────────────────────────────┼────────────────────────────────────────┤
│ 4. Regulatory & Portal Lens   │ Government portals, licensing, RERA,   │
│                               │ Patta/EC, taxes, statutory filings     │
├───────────────────────────────┼────────────────────────────────────────┤
│ 5. Exception & Dispute Lens   │ Cancellations, deposit deductions,     │
│                               │ delayed handovers, tenant disputes     │
└───────────────────────────────┴────────────────────────────────────────┘
```

> **Adaptive decomposition and evidence boundary:**  
> Treat the five streams as default coverage lenses, not a universal MECE taxonomy or a requirement to produce five problems. Decompose only within the user's requested scope. Preserve user-reported facts, second-hand claims, inferred possibilities, and unknowns as separate categories. For broad discovery, generate an initial actor–task–workflow plan and adapt it when sources reveal missing or overlapping workflows. For narrow requests, do not expand into unrelated streams. A planned search topic, generated query, or plausible workaround is a hypothesis—not an observed problem.

---

## 4. Step 3: Atomic Search Unit & Candidate Query Formulation

Convert each identified workflow into an **Atomic Search Unit**:

$$\textbf{Search Unit} = \textbf{Specific Person} + \textbf{Specific Task} + \textbf{Current Workaround} + \textbf{Consequence}$$

*Critical Distinction:* Generated queries are **candidate search queries / hypotheses**, not "verified dorks". Finding a search result does not mean the operational friction is verified.

---

## 5. Case Study: Epistemic Parsing of a Messy Regional Prompt

### Raw User Prompt:
> *"My uncle does real estate in Pollachi, WhatsApp is messy with photos, buyers delay token advance, and sub-registrar office has huge queues for EC."*

### Rigorous Epistemic Parsing:

1. **User-Supplied Context & Provenance:**
   - Geography: Pollachi, Tamil Nadu, India.
   - Provenance: **Second-hand report** (*"uncle does real estate"*; not user's direct observation).
2. **Reported Frictions:**
   - WhatsApp photo organization & media clutter.
   - Token-advance payment delays.
   - Sub-registrar office queues for Encumbrance Certificate (EC).
3. **Explicit Unknowns (Do NOT Invent):**
   - *Uncle's exact role:* Is he an independent broker, layout promoter/builder, or document writer?
   - *WhatsApp photo task:* Are photos for buyer marketing, co-broker sharing, or survey boundary proof?
   - *Token advance tracking:* Who tracks advances (uncle or property owner), and what tool (paper diary, Excel, memory)?
   - *EC queue nature:* Is the queue caused by physical counter staffing, manual book searches, or online portal (TNeGA/Reginet) downtime?
4. **Formulating Separate Candidate Query Hypotheses:**
   - *Hypothesis 1 (Broker WhatsApp Media):*  
     `"real estate broker" "WhatsApp" "photos" "catalogue" India`
   - *Hypothesis 2 (Token Advance Delays):*  
     `site:reddit.com/r/IndiaInvestments "plot" "advance" "token" "dispute"`
   - *Hypothesis 3A (Physical Office Queues for EC):*  
     `"sub-registrar office" "Pollachi" OR "Coimbatore" "queue" "EC"`
   - *Hypothesis 3B (Digital Portal Downtime for EC):*  
     `"TNeGA" OR "reginet" "server down" "EC" "patta" delay`

*(Note: Never replace reported physical queues with digital portal timeouts without evidence; treat them as two distinct hypotheses to investigate).*

---

## 6. Multilingual & Vernacular Invariants

1. **Preserve regional regulatory terms:** Vernacular words (*Patta*, *Chitta*, *EC*, *Khata*, *Challan*, *Udhar*, *Varavu Selavu*) identify exact legal and financial artifacts. Never translate them into generic US/UK terminology.
2. **Local jurisdiction fidelity:** A problem reported in Pollachi operates under Tamil Nadu state revenue rules (TNeGA/TN Reginet). Do not substitute central Indian or foreign procedures.
