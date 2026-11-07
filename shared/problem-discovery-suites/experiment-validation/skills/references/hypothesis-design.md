# Hypothesis Design & Validation Target Types

## Overview
Guides the formulation of single-focus, testable hypotheses classified by validation target type.

---

## 1. The 10 Reusable Validation Target Types

Every experiment must declare exactly one validation target type:

| Target Type | Core Question Being Tested | Example Metric |
|---|---|---|
| `BEHAVIOR_FREQUENCY` | Does the manual friction occur repeatedly? | Count of manual sync events / week |
| `TIME_COST` | How much operator time is actually lost? | Minutes spent on manual data entry / day |
| `ERROR_RATE` | How often does the manual process fail? | Percentage of orders with mismatched stock |
| `WORKAROUND_USE` | Are operators maintaining active makeshift tools? | Presence of active shadow spreadsheet updates |
| `ADOPTION` | Will operators adopt an initial manual intervention? | Percentage of cohort agreeing to concierge trial |
| `USAGE` | Do operators repeatedly use the intervention? | Number of runs / week during observation |
| `WILLINGNESS_TO_PAY` | Will the operator commit real financial payment? | Paid deposit, signed LOI, or checkout transaction |
| `RETENTION` | Do operators continue using after week 2? | 14-day or 30-day active repeat rate |
| `CONVERSION` | Does the intervention convert targeted traffic? | Conversion percentage on landing page test |
| `PROCESS_IMPROVEMENT` | Does the intervention reduce errors or latency? | Measurable reduction in dispute tickets |

---

## 2. Hypothesis Formulation Formula

Every hypothesis statement must be single-scoped and falsifiable:

$$\text{Hypothesis} = \text{[Target Population]} + \text{repeatedly / measurably exhibits} + \text{[Observable Action]} + \text{under} + \text{[Condition]}$$

*Example*: *"Ecommerce sellers managing 2+ sales channels perform manual inventory count adjustments at least 3 times every 7 days when orders are fulfilled."*
