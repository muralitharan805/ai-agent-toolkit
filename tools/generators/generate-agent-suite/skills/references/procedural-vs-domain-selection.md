# Procedural vs Domain Skill Selection Guide

## 1. Overview
In the Google Antigravity ecosystem, workflows have officially retired, and all agent tasks are encapsulated as **Skills**. Within Skills, there are two distinct archetypes:
1. **Procedural Execution Skills** (The successor to Workflows)
2. **Domain Knowledge Skills** (API specs, patterns, and Gotchas)

The `generate-agent-suite` orchestrator must determine the exact archetype when a Skill is required.

---

## 2. Comparison Table

| Attribute | Archetype A: Domain Knowledge Skill | Archetype B: Procedural Execution Skill |
| :--- | :--- | :--- |
| **Primary Focus** | "How to write code according to patterns & APIs" | "How to execute a multi-step sequential operation" |
| **Typical Triggers** | Framework APIs, reactive models, state management, schema setup | Scaffolding, deployments, audits, test runs, migrations |
| **Core Structure in SKILL.md** | Core API patterns, decision trees, progressive disclosure pointers | Progress checklist (`- [ ] Step 1...`), Plan-Validate-Execute gates |
| **Key Bundled Assets** | `references/*.md` (deep specs), `evals/evals.json` | `scripts/*.sh|py` (CLI tools), `assets/*.json` (templates) |
| **Slash Command Invocation** | Invocable directly (`/skill-name`) or triggered by context | Invocable directly (`/skill-name`) as an interactive pipeline |

---

## 3. Checklist for Archetype B (Procedural Execution)
When generating a Procedural Skill, the orchestrator mandates the following components in `SKILL.md`:
1. **Pre-flight Check**: Validating CLI prerequisites (e.g. `docker`, `wrangler`, `node` versions).
2. **Sequential Checklist**:
   ```markdown
   - [ ] Step 1: Pre-flight Environment Validation
   - [ ] Step 2: Build & Asset Compilation
   - [ ] Step 3: Local Dry-Run Preview
   - [ ] Step 4: Production Deployment / Execution
   - [ ] Step 5: Post-Deployment Smoke Verification
   ```
3. **Plan-Validate-Execute Gates**: Stopping for critical verification before destructive actions.
4. **Rollback Runbook**: Explicit remediation if any step fails.
5. **Idempotency**: Ensuring running the skill multiple times does not corrupt state.

---

## 4. Checklist for Archetype A (Domain Knowledge)
When generating a Domain Skill:
1. Keep `SKILL.md` concise (< 500 lines).
2. Offload comprehensive API documentation to `references/[topic].md`.
3. Emphasize `## Gotchas` (edge cases, pitfalls, silent failure modes).
4. Provide zero-`any` production-grade code snippets.
5. Include `evals/evals.json` with verifiable assertions.
