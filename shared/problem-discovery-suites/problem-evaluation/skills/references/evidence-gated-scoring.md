# Evidence-Gated 35-Point Scoring Model

## Overview
Defines the 7 evaluation dimensions, stop check triggers, and strict evidence-level scoring caps that prevent over-optimistic project initiation.

---

## 1. The 7 Scoring Dimensions (0–5 Points Each, Max 35)

| Dimension | 0 Points | 3 Points | 5 Points |
|---|---|---|---|
| **1. Frequency** | Rare (annual/one-off) | Weekly routine | Multiple times daily / continuous |
| **2. Severity** | Cosmetic inconvenience | Measurable time loss (hours/week) | Severe financial loss, legal liability, or stoppage |
| **3. Workaround** | No workaround needed | Informal ad-hoc notes | Maintained complex spreadsheet, dedicated staff, shadow tool |
| **4. WTP / Adoption** | Zero willingness to pay/adopt | Would use if free / low-friction | Actively paying for makeshift tools, consultancy, or overtime |
| **5. Decision Maker** | Diffuse, unclear buyer | Frontline manager with small budget | Direct budget owner suffering acute pain |
| **6. Feasibility** | Impossible / heavy regulatory barrier | Feasible with standard APIs | High feasibility; clean data boundaries |
| **7. Discrepancy** | High software saturation; solved | Partial gap in existing tools | Huge gap; zero tools support local/niche reality |

---

## 2. Evidence-Level Score Caps

To prevent unverified internet claims from generating inflated priorities, apply evidence at the dimension level. A single public post is not automatically L3; L3 requires independent corroboration of the same failure pattern.

| Highest Verified Evidence Level | Maximum Allowed Total Score | Permitted Candidate Lifecycle Status |
|---|---|---|
| **L1** (Primary behavioral/system evidence) | Full 0–5 dimension range | `RESEARCH_PRIORITY` at qualifying scores |
| **L2** (Direct authenticated practitioner testimony) | Full 0–5 dimension range | `RESEARCH_PRIORITY` at qualifying scores |
| **L3** (Independent corroboration across unconnected sources) | Full 0–5 dimension range | `RESEARCH_PRIORITY` at qualifying scores |
| **L4** (Secondary interpretation) | **Max 1 point per dimension (7/35 total)** | `PARKED` / gather primary evidence |
| **L5 / UNASSESSED** | **0 points** | `PARKED` until stronger evidence exists |

---

## 3. Stop Checks
If any of the following 6 stop checks are triggered, the candidate is automatically capped and recommended for `PARKED`:
1. `infrequent_low_impact`: Event occurs rarely with negligible consequences.
2. `no_meaningful_workaround`: Operators do not maintain any workaround.
3. `commercial_alternative_fits_well`: Existing tools fully satisfy the workflow.
4. `single_source_bias`: All reports trace back to a single vocal complainant.
5. `internal_training_issue`: Process breakdown is caused by operator error or lack of SOP training.
6. `unreachable_audience`: Target operators cannot be contacted for research or testing.
