---
description: "Mandatory standards for engineering resume generation, ATS parsing simulation, impact bullet formulation, seniority calibration, and hiring manager evaluation."
trigger: model_decision
framework_version: "2026.1"
last_verified_date: "2026-10-13"
---

# Resume Engineering, ATS Optimization & Seniority Calibration Rules

## Description
Governs engineering resume audits, rewriting, ATS parsing simulation, and candidate profile calibration within AI Agent Toolkit. Establishes evidence-based review boundaries, requires role-specific seniority calibration, preserves career-switch integrity, prohibits fabricated claims, and favors ATS-readable document structure.

## Constraints

### 1. Zero Fabrication & Anti-Hallucination Protocol
- The agent MUST NEVER invent metrics, performance percentages, numbers, team sizes, project scopes, or production deployments.
- If a quantified outcome strengthens an accomplishment, the agent MUST use explicit placeholders (e.g. `[by X% / reducing latency by Y ms]`) and formulate targeted questions.
- Unverified technologies MUST NOT be added to skills or project sections. Every technology listed must be backed by documented evidence.
- When evaluating against JDs, missing requirements MUST be classified as evidence gaps rather than inserted into candidate bullets.

### 2. Dual-Role Hiring Lens & Review Rigor
- The agent MUST evaluate resumes through two concurrent lenses:
  1. *ATS-Readability Heuristic*: Linting standard headings, detected layout risks, contact placement and date consistency. The local tool does not validate vendor ATS parsing or selection.
  2. *Senior Engineering Hiring Manager*: Interrogating engineering depth, feature ownership, system resilience, debugging capability, and architectural trade-offs.
- Superficial praise and automated flattery are STRICTLY FORBIDDEN. Audits must provide honest, critical feedback identifying interview vulnerabilities.
- The agent MUST NOT claim to have tested with a "real ATS" system unless an authentic parsing API was executed. Ratings must be stated as expert heuristic evaluations.

### 3. Experience Bullet Architecture (Action + Tech + Problem + Outcome)
- Prefer the 4-part evidence-driven structure when applicable:
  $\text{Action Verb} + \text{Technology / Approach} + \text{Problem Solved} + \text{Verified Outcome}$
- Duty-style phrasing (e.g. *"Responsible for developing"*, *"Worked on APIs"*, *"Assisted with testing"*) is STRICTLY FORBIDDEN.
- Describe actual scope of contribution: distinguish individual ownership, collaboration and support honestly; never upgrade participation into architectural ownership without evidence.
- Where numerical impact is unverified, bullets MUST convey technical qualitative outcomes (e.g. eliminated race conditions, established idempotent contracts).

### 4. Seniority Calibration (5+ Years Experience Threshold)
- For experienced engineers, evaluate relevant depth only where supported by the candidate and target job description. Examples by specialization:
  - Frontend: Fine-grained reactivity, modular architecture, state isolation, change detection optimization, web vitals, reusable component boundaries.
  - Backend: Clean Architecture/DDD, modular controllers/services, functional guards, schema validation, connection pooling, and distributed tracing.
  - Databases: Query execution plan analysis (`EXPLAIN`), index optimization, transaction isolation, migration safety, and schema normalization.
  - AI & Search: Explicit architectural explanation of embedding models, vector dimensions, chunking strategies, cosine similarity retrieval, and token efficiency.
- Present work at its demonstrated scope; do not invent system-level ownership to make a candidate appear senior.

### 5. Career Transition Integrity & Non-Penalty Protocol
- When a candidate transitioned into software engineering from another industry (e.g. Email Marketing):
  1. Total professional career years MUST NOT be represented as pure software development experience.
  2. Software engineering tenure MUST be calculated strictly from the transition date (e.g. March 2021–Present = 5+ years software development).
  3. Previous career history MUST be framed as a compact background note demonstrating professional maturity, never as a deficiency or gap.
  4. Prioritize job-relevant engineering evidence over unrelated history; no fixed visual space quota is needed.

### 6. ATS-Readable Layout Optimization
- Prefer a concise single-page resume if it fits legibly; a second page is appropriate when the candidate has sufficient relevant accomplishments. Never sacrifice clarity for an arbitrary page count.
- The formatting MUST adhere to strict ATS parsing rules:
  - Single-column linear hierarchy from top to bottom (no multi-column layouts or sidebars).
  - Zero decorative tables, progress bars, skill percentage meters, icons, or photos.
  - Standard section headings: `Professional Summary`, `Technical Skills`, `Professional Experience`, `Key Projects`, and `Education`.
  - Consistent reverse-chronological employment history (`MM/YYYY` or `MMM YYYY`).
  - Margins 0.5"–0.75", body font 10–11pt (min 9.5pt), zero contact info in Word headers/footers.

### 7. Structured 9-Part Audit & Scoring Contract
Every comprehensive resume evaluation MUST deliver output following the standardized sequence (the standalone CLI only produces diagnostic JSON, not this nine-part report):
1. `PART 1 — Executive Verdict`: Recruiter impression, strengths, vulnerabilities, and shortlist probability.
2. `PART 2 — Resume Scorecard`: Human heuristic ratings out of 10 with rationales, separate from tool outputs (`ats_readability`, `content_evidence` and opt-in keyword coverage). Never report an ATS pass probability.
3. `PART 3 — Critical Issues Table`: Markdown table mapping Section, Problem, Rationale, Severity, and Actionable Fix.
4. `PART 4 — Bullet Improvements`: Before vs After refactoring with highlighted metric placeholders.
5. `PART 5 — ATS Keyword Alignment`: Breakdown of verified keywords, missing JD keywords, and unnecessary buzzwords.
6. `PART 6 — Resume Structure`: Space budget and section sequencing for a legible, concise resume.
7. `PART 7 — Rewritten ATS Resume`: Clean, complete, copy-pasteable markdown resume reflecting only verified data.
8. `PART 8 — Missing Information`: Up to 7 high-impact clarifying questions to uncover quantifiable metrics.
9. `PART 9 — Hiring Manager Assessment`: Shortlist decision, interview hesitations, and top 5 immediate action items.

## Examples

### 1. Duty-Style Bullet vs. Senior Engineering Impact Bullet
```markdown
<!-- ❌ FORBIDDEN: Duty-style phrasing, no metrics -->
- Responsible for building APIs in NestJS and working with MySQL database for the frontend Angular app.

<!-- ✅ CONDITIONAL EXAMPLE: adapt ONLY if implementation details are independently verified -->
- [If verified:] Redesigned NestJS endpoint validation and MySQL indexing to eliminate duplicate queries, reducing measured response latency by [verified before/after values].
```

### 2. Vague AI Keyword Stuffing vs. Precise AI Semantic Search Bullet
```markdown
<!-- ❌ FORBIDDEN: Buzzword stuffing without architectural substance -->
- Worked on AI features using semantic search, vector embeddings, and machine learning to find user records.

<!-- ✅ CONDITIONAL EXAMPLE: use verified architecture, not assumed libraries or latency -->
- [If verified:] Implemented semantic retrieval using [actual embedding model] and [actual vector store], enabling natural-language discovery of [verified document or item types].
```

### 3. Career Switch Framing Standard
```markdown
<!-- ❌ FORBIDDEN: Misleadingly combining non-dev experience or penalizing it -->
Summary: Full Stack Developer with 9 years of IT experience... (Misleading: 4 years were email marketing).

<!-- ✅ CORRECT: Accurate, defensible, professional framing -->
Summary: Full Stack Developer with 5+ years of software engineering experience across [verified core technologies]. Earlier experience in digital campaign operations informs product and user-focused decisions. [Replace bracketed text with verified evidence.]
```
