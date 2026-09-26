# Validation Scope Boundaries & Non-Extrapolation Rules

## Overview
Establishes hard boundaries between 5 decoupled validation scopes, preventing local trial passes from being exaggerated into global business validation.

---

## 1. The 5 Decoupled Validation Scopes

| Scope Flag | What It Strictly Confirms | What It Does NOT Confirm |
|---|---|---|
| `problem_behavior_observed` | The reported task/friction occurred in the tested cohort. | Market size, willingness to pay, software adoption. |
| `market_demand_validated` | Widespread frequency observed across multiple statistical segments. | Pricing acceptance, software retention. |
| `willingness_to_pay_validated` | Target buyer committed real money (pre-order, deposit, fee). | Long-term retention, customer lifetime value. |
| `solution_adoption_validated` | Target operators used the intervention during the trial. | Continued usage after week 4 (retention). |
| `retention_validated` | Operators repeatedly used intervention over an extended horizon. | Organic referral, multi-segment expansion. |

---

## 2. Supported vs. Unsupported Claims Matrix

When publishing a `ValidationAssessment`, the agent must explicitly itemize what was demonstrated versus what remains unproven:

```json
{
  "supported_claims": [
    "3 of 5 tested sellers in Coimbatore performed manual inventory updates daily."
  ],
  "unsupported_claims": [
    "All ecommerce sellers suffer from inventory sync issues.",
    "Merchants are willing to pay $49/month for an automated sync SaaS.",
    "The market size in Tamil Nadu exceeds 10,000 sellers."
  ]
}
```
