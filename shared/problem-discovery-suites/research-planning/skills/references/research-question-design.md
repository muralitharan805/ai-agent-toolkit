# Research Question & Hypothesis Design

## Overview
Guides the creation of concrete, empirical, and answerable research questions and unverified hypotheses for each operational research stream.

---

## 1. Principles of Empirical Research Questions
Research questions must guide the downstream search agent to collect observable behavioral evidence rather than subjective opinions.

### Rules for Question Formulation:
1. **Focus on Behavior & Operations, Not Sentiment**:
   - ❌ Bad: *"Do warehouse managers hate their ERP?"* (Subjective sentiment)
   - ✅ Good: *"What manual workarounds do warehouse clerks use to reconcile stock mismatches between physical racks and the ERP?"*
2. **Target Observable Artifacts**:
   - Focus on physical or digital paper trails: spreadsheets, printed checklists, WhatsApp message screenshots, error codes, PDF reports.
3. **Inspect the Non-Software Alternative**:
   - Always formulate questions that uncover how the workflow is handled without specialized software (e.g., pen-and-paper registers, batch Excel macros, phone calls).

---

## 2. Core Question Categories per Stream
For each identified workflow, author 2 to 4 questions covering:

- **Cadence & Operator Context**: Who executes the step, how frequently, and with what initial inputs?
- **Friction Points & Failure Modes**: Where do handoff delays, transcription errors, or system dropouts occur?
- **Current Workaround**: What interim patchwork (spreadsheet, manual glue-work, temporary hire) is maintained?
- **Economic & Operational Cost**: What are the quantifiable costs of failure (wasted hours, penalty fees, lost inventory)?

---

## 3. Formulating Unverified Hypotheses
Hypotheses represent plausible explanations or specific frictions that downstream research must attempt to confirm or falsify.

### Hypothesis Framing Standards:
- Must be explicitly flagged as `UNVERIFIED`.
- Must specify the alleged condition, the mechanism, and the observable impact.
- Avoid loaded language or presumed customer willingness to buy software.

```json
{
  "claim": "Textile merchandisers lose 4-6 hours weekly re-entering supplier dispatch dates into buyer tracking portals.",
  "status": "UNVERIFIED",
  "verification_target": "Practitioner forum threads, job description requirements, or buyer penalty guidelines."
}
```
