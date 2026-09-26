# Contradictory Evidence & Nuance Preservation

## Overview
Mandates the preservation and objective analysis of conflicting, dissenting, or limiting evidence in problem evaluation.

---

## 1. Handling Conflicting Signals

Real markets are rarely uniform. Often, one operator experiences severe friction while another finds the same process effortless.

### Protocol:
- Maintain two distinct signal arrays per candidate:
  - `supporting_signal_ids`: Signals verifying the friction or workaround.
  - `contradicting_signal_ids`: Signals reporting that the problem does not exist, that existing tools work fine, or that the process is trivial.
- **Do not average out or discard contradictions**: Instead, explain the discrepancy in the candidate interpretation (e.g., *"Large sellers using enterprise ERPs report no sync issues, whereas mid-tier merchants using native dashboards experience manual bottleneck"*).

---

## 2. Interpreting Contradictions
When opposing signals emerge, classify the conflict into one of three structural types:

1. **Segment Divergence**: Enterprise vs SMB scale; domestic vs international jurisdiction.
2. **Tooling Maturity**: High-tech operators automating via scripts vs non-technical operators relying on manual entry.
3. **Volume Threshold**: Workflow works smoothly up to 50 orders/day; breaks down above 200 orders/day.
