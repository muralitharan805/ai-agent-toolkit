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

To prevent unverified internet claims from generating inflated priorities, hard caps are applied based on the highest verified evidence level:

| Highest Verified Evidence Level | Maximum Allowed Total Score | Permitted Candidate Lifecycle Status |
|---|---|---|
| **L1** (Primary system / financial logs) | **35 / 35** | `READY_TO_BUILD` (if experiment also passes) |
| **L2** (Direct authenticated interview) | **28 / 35** | `RESEARCH_PRIORITY` |
| **L3** (Public forum post / Reddit / HN) | **20 / 35** | `RESEARCH_PRIORITY` (Capped) |
| **L4** (Vendor blog / marketing) | **15 / 35** | `PARKED` (Requires primary evidence) |
| **L5** (Speculative opinion) | **10 / 35** | `ARCHIVED` |

---

## 3. Stop Checks
If any of the following 6 stop checks are triggered, the candidate is automatically capped and recommended for `PARKED`:
1. `infrequent_low_impact`: Event occurs rarely with negligible consequences.
2. `no_meaningful_workaround`: Operators do not maintain any workaround.
3. `commercial_alternative_fits_well`: Existing tools fully satisfy the workflow.
4. `single_source_bias`: All reports trace back to a single vocal complainant.
5. `internal_training_issue`: Process breakdown is caused by operator error or lack of SOP training.
6. `unreachable_audience`: Target operators cannot be contacted for research or testing.
