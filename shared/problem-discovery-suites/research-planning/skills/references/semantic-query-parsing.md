# Semantic Query Parsing & Attribution Protocol

## Overview
The Semantic Query Parsing stage ingests raw, colloquial, messy, or unstructured user prompts and extracts operational entities while preserving strict epistemic provenance. It strips conversational noise without losing attribution markers.

---

## 1. Extraction Slots
The parser extracts the following primary operational slots:
- `original_request`: The verbatim user input string.
- `domain`: High-level operational industry or sector (e.g. `logistics`, `healthcare`, `ecommerce`).
- `geography`: Explicit country, state, or municipality. If absent, MUST be set to `UNKNOWN`.
- `operators`: Real human workers performing the tasks (e.g., `merchandiser`, `billing clerk`, `warehouse picker`).
- `tasks`: Concrete activities performed by operators.
- `frictions`: Reported difficulties, bottlenecks, latency, or errors.
- `current_tools`: Software, spreadsheets, or physical artifacts currently utilized.
- `user_preferences`: Desired form factors (e.g., "build SaaS", "Chrome extension"), treated strictly as unverified preferences.

---

## 2. Epistemic Quad-Classification Matrix

Every extracted claim is mapped into one of four distinct epistemic states:

| Classification | Definition | Evidence Requirement | Example |
|---|---|---|---|
| `EXPLICIT_REPORTED` | Directly stated by the user. Attribution MUST be preserved. | None (recorded as subjective statement). | "My friend said orders take 3 days to confirm." |
| `INFERRED` | Deduced by the agent based on workflow standards. | Must be explicitly labeled as model deduction. | "Inferred: Invoicing requires cross-checking purchase orders." |
| `HYPOTHESIS` | Suspected failure mode or problem candidate to investigate. | Requires verification by downstream research. | "Hypothesis: Discrepancies between warehouse logs and portal cause delayed billing." |
| `UNKNOWN` | Missing from prompt and not safely inferable. | Must be carried forward explicitly. | "Target geography: UNKNOWN" |

---

## 3. Attribution Preservation Protocol
Users frequently convey information through indirect channels. Stripping attribution causes epistemic drift where hearsay is treated as ground truth.

### Attribution Rules:
1. **Never Promote Hearsay to Fact**: If the prompt states *"A supplier told me they lose 10 hours a week on customs portals"*, record:
   - Claim: Loss of 10 hours weekly on customs portals.
   - Provenance: `SECONDHAND_REPORT` (supplier report via user).
   - Epistemic Status: `EXPLICIT_REPORTED` (unverified claim).
2. **Preserve User Voice Nuances**: Preserve domain jargon, local acronyms, and operational phrases (e.g., "challan", "e-way bill", "gate pass", "tally sync").
3. **Separate Complaint from Root Cause**: A complaint is an emotional or operational symptom. The root cause remains an `UNKNOWN` or `HYPOTHESIS` until verified.

---

## 4. Flipped Interaction Gate
If the user prompt is completely empty or so ambiguous that no domain or task can be identified:
- **Do NOT hallucinate a domain.**
- Formulate 1 to 3 targeted clarifying questions using bullet points.
- Pause and await user clarification before proceeding to workflow decomposition.
