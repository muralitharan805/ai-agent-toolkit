# Engineering Impact Bullet Playbook: Formulation & Metrics

## 1. The Canonical 4-Part Formula
Use the formula as a writing aid when it fits; do not invent technologies, ownership or outcomes:
$$\text{Action Verb} + \text{Technology / Architecture} + \text{Technical Challenge / Problem Solved} + \text{Verified Outcome}$$

```
[Action Verb] ─────────► "Architected"
[Technology] ──────────► "a centralized caching layer using Redis and NestJS Interceptors"
[Problem Solved] ──────► "to eliminate redundant MySQL read spikes on hot product catalogs"
[Measurable Outcome] ──► "improving latency [insert verified before/after measurement if available]."
```

---

## 2. Seniority Signals: Examples, Not Candidate Facts

The examples below are **illustrative only**. Do not transfer counts, technologies or percentages into a real resume without independent evidence.

| Dimension | Junior / Duty-Style Phrasing (Anti-Pattern) | Senior 5+ Year Engineering Framing (Recommended) |
| :--- | :--- | :--- |
| **API Development** | "Responsible for writing APIs in NestJS and connecting to database." | "Designed NestJS endpoints with validation and connection pooling, improving request reliability [cite an actual outcome]." |
| **Frontend State** | "Worked on Angular components and forms for client portal." | "Refactored Angular components to improve state isolation and reduce unnecessary change detection [if confirmed]." |
| **Database Tuning** | "Wrote SQL queries and updated MySQL tables for new features." | "Analyzed MySQL query plans and added verified indexes, reducing report generation time [add measured values if available]." |
| **Search / AI** | "Added AI search feature using semantic search and embeddings." | "Implemented semantic retrieval using [verified model/store], improving the relevance of [verified use case]." |
| **Code Quality** | "Helped junior developers and fixed bugs in testing." | "Introduced automated tests and review checks to catch regressions earlier [if verified]." |

---

## 3. High-Impact Action Verbs by Engineering Domain

- **Architecture & System Design**: *Architected, Engineered, Designed, Consolidated, Decoupled, Orchestrated, Refactored, Modularized.*
- **Performance & Optimization**: *Benchmarked, Tuned, Accelerated, Trimmed, Streamlined, Parallelized, Scaled, Eliminated.*
- **Reliability & Infrastructure**: *Hardened, Automated, Deployed, Monitored, Restored, Containerized, Provisioned, Isolated.*
- **Delivery & Leadership**: *Spearheaded, Championed, Standardized, Mentored, Established, Instituted, Accelerated.*

---

## 4. Metric Extraction Protocol (Without Hallucination)
When an engineer has strong work but lacks exact metrics, ask these targeted questions:
1. **Latency & Response Time**: Did API latency improve? (e.g. from X ms to Y ms?)
2. **Throughput & Scale**: How many requests per second, users, or records were processed? (e.g. 50k daily active users, 100k database records?)
3. **Efficiency & Cost**: Did your change reduce cloud costs, build times, or background job duration? (e.g. build time dropped by 40%?)
4. **Reliability & Bugs**: Did error rates or regression bugs decrease after refactoring? (e.g. 0 production rollbacks over 6 months?)
5. **Team Velocity**: Did reusable components or libraries speed up feature delivery for other teammates?
