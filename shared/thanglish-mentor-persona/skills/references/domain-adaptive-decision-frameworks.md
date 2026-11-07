# Domain-Adaptive Decision Frameworks & Systems Thinking Reference

## 1. The Reversibility Decision Model (Type 1 vs. Type 2 Decisions)

Popularized by Jeff Bezos, this mental model separates high-stakes, irreversible commitments from low-risk, reversible experiments.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   The Reversibility Matrix (Doors of Decision)                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
          High Risk / Irreversible                     Low Risk / Reversible
       ┌───────────────────────────────┐           ┌───────────────────────────────┐
       │   TYPE 1: ONE-WAY DOOR        │           │   TYPE 2: TWO-WAY DOOR        │
       │                               │           │                               │
       │ - Cannot walk back through    │           │ - Easy to undo or iterate     │
       │ - Catastrophic reversal cost  │           │ - Low blast radius            │
       │ - Requires deep analysis,     │           │ - Bias for rapid action,      │
       │   peer consensus, and proofs  │           │   experimentation & velocity  │
       └───────────────────────────────┘           └───────────────────────────────┘
```

### Key Failure Modes in Organizations
1. **Treating Type 2 as Type 1 (Analysis Paralysis)**:
   - Debating button colors, CSS frameworks, or internal helper interfaces in 2-hour meetings.
   - Antidote: Recognize that it's reversible; execute in hours, gather empirical feedback, and adjust.
2. **Treating Type 1 as Type 2 (Catastrophic Lock-In)**:
   - Hastily picking a core database schema or breaking public REST API contracts without migration paths.
   - Antidote: Slow down; build defensive abstractions, proof-of-concepts, and formal trade-off memos.

---

## 2. Systems Thinking & Second-Order Consequences

Systems thinking evaluates not just the immediate effect (first-order), but what happens as a result of that effect (second-order and beyond).

### Core Mental Models

| Mental Model | Core Principle | Architectural / Business Application |
| :--- | :--- | :--- |
| **Chesterton's Fence** | Do not remove a rule or component until you understand why it was put there. | Before refactoring legacy boilerplate or custom interceptors, discover the edge case it originally solved. |
| **Goodhart's Law** | When a measure becomes a target, it ceases to be a good measure. | Optimizing purely for line test coverage leads to assertions without behavioral validation. |
| **Conway's Law** | Organizations design systems that mirror their communication structures. | Cross-functional silos result in fractured APIs and disjointed microservice boundaries. |
| **Sunk Cost Fallacy** | Past unrecoverable investments should not dictate future resource allocation. | Continuing to patch a fundamentally broken architecture because "we spent 6 months on it." |

### Diagnostic Questions for the Mentor
- *"What happens when throughput or concurrency grows 10x?"*
- *"What incentives does this metric or architectural standard create for the team?"*
- *"Are we treating a visible symptom while making the underlying structural imbalance worse?"*
- *"Where is the hidden single point of failure or fragile transitive dependency?"*

---

## 3. The 8-Step Strategic Decision Ladder

When answering *"Which one should I choose?"*, execute this sequence:

```
[1. Goal] ──► What specific outcome must be achieved?
     │
[2. Constraints] ──► What are the hard boundaries (time, budget, latency, team skills)?
     │
[3. Evidence] ──► What verified data exists vs unverified assumptions?
     │
[4. Alternatives] ──► What are the realistic viable options?
     │
[5. Trade-offs] ──► What are we explicitly trading away for each option?
     │
[6. Risks & Failure Modes] ──► What happens under worst-case operational scenarios?
     │
[7. Reversibility] ──► Is this a Type 1 or Type 2 decision?
     │
[8. Recommendation] ──► Deliver actionable choice with transparent rationale.
```

---

## 4. Domain-Adaptive Perspectives

The mentor shifts mental models based on the domain:

### A. Senior Principal Software Architect
- **Focus**: Boundary isolation, lifecycle cleanup, deterministic state, concurrency safety, API backwards-compatibility, zero `any` types.
- **Key Question**: *"How does this system fail gracefully under network partitions or memory exhaustion?"*

### B. Product & Business Strategist
- **Focus**: Value proposition, time-to-market, distribution leverage, North Star metric, feature usage analytics.
- **Key Question**: *"Does this feature solve a hair-on-fire user pain point, or is it decorative complexity?"*

### C. Career & Leadership Mentor
- **Focus**: High-leverage problem selection, sponsorship vs mentorship, visible impact, autonomous ownership.
- **Key Question**: *"Does this project develop defensible, compounding skills or merely consume operational hours?"*

### D. Financial & Economic Thinker
- **Focus**: Opportunity cost, compounding interest, risk-adjusted returns, cash flow liquidity, risk mitigation.
- **Key Question**: *"What is the counterfactual return if these resources were invested elsewhere?"*
