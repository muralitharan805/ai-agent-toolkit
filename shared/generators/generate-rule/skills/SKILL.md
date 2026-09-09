---
name: generate-rule
description: "Analyzes development constraints and scaffolds or updates strict rule files in ai-agent-toolkit. Triggered by 'rule:', 'generate-rule:', or '/generate-rule'."
---

# Generate Rule (`generate-rule`)

## Persona
Act as a Principal Software Architect and expert Google Antigravity Rule Architect. You specialize in analyzing development constraints, team conventions, compliance policies, and coding standards (provided in English, Tamil, or Thanglish) and transforming them into strict, production-ready rule files (`.md`) inside `ai-agent-toolkit`.

---

## Authoritative Reference Grounding & Bundled Assets
Consult the bundled reference guides and tools in this skill:
- **Rule Architecture & Spec**: [references/antigravity-rules-spec.md](references/antigravity-rules-spec.md) (Triggers, tokens, character limits).
- **Rule Validation Tool**: `python3 scripts/validate_rule.py <path-to-rule>`
- **Canonical Rule Scaffold Asset**: [assets/rule-template.md](assets/rule-template.md)
- **Quality Verification Suite**: [evals/evals.json](evals/evals.json)

---

## Decision Gate: Rule vs Skill

Before creating a rule, verify that a Rule is the appropriate customization element:
- **Use a Rule (`.md`)** when defining:
  - Invariants, constraints, and negative boundaries (what the agent MUST or MUST NOT do).
  - Coding standards (Clean Code, zero `any` types, naming rules).
  - Architectural restrictions (zero raw SQL, mandatory parameterized queries, zero hardcoded secrets).
  - Triggers on filetypes via glob patterns (`**/*.prisma`, `**/*.component.ts`).
- **Use an Agent Skill (`skills/<name>/SKILL.md`)** when defining:
  - Multi-step procedural workflows (deployments, scaffolding pipelines, refactoring runbooks).
  - Reusable scripts, schemas, or extensive API documentation requiring progressive disclosure.

---

## Task Protocol

### 1. Existing Rule Discovery & Upsert
Search `ai-agent-toolkit` (`frameworks/`, `infra/`, `shared/`, `domains/`) for an existing rule related to the target topic:
- **If found**: Mark action as **UPDATE** (merge new constraints, rules, and examples into the existing rule file).
- **If not found**: Mark action as **CREATE** (scaffold under `[frameworks|infra|shared|domains]/[topic]/rules/[rule-name].md`).

### 2. Trigger Strategy & Context Budget
Select the optimal YAML frontmatter trigger:
1. `trigger: model_decision` (Default for domain-specific guidelines loaded on demand).
2. `trigger: glob` with `globs: ["<pattern>"]` (For filetype-specific invariants, e.g. `**/*.ts`, `Dockerfile*`).
3. `trigger: always_on` (Reserved ONLY for universal workspace invariants).
4. `trigger: manual` (For explicit `@mention` audit checklists).

Enforce character limits strictly:
- **Target**: 6,000–8,000 characters.
- **Split Warning**: Approaching 10,000 characters.
- **Hard Ceiling**: 12,000 characters (Antigravity IDE truncation limit).

### 3. File Generation Protocol
Output the target file path followed by the markdown block wrapped in 4-backticks (````markdown ... ````):
- Use canonical sections: `# Title`, `## Description`, `## Constraints`, and `## Examples`.
- Examples MUST contrast **Correct Implementation** with **Incorrect Implementation (FORBIDDEN)**.
- Code blocks MUST be strictly typed (zero `any` types).

### 4. Validation
Run the bundled validator to ensure compliance:
```bash
python3 shared/generators/generate-rule/skills/scripts/validate_rule.py [determined-toolkit-path]/rules/[rule-name].md
```

---

## Format Template

**Target File Location:** `[determined-toolkit-path]/rules/[rule-name].md`

````markdown
---
description: "[Clear, descriptive third-person statement detailing what this rule governs and when it applies.]"
trigger: model_decision # or glob | always_on | manual
# globs: ["pattern/**"] # Required if trigger is glob
---

# [Rule Title]

## Description
[Provide a clear, prescriptive explanation of what this rule governs and why it is active.]

## Constraints

### 1. [Mandatory Policy Name]
- The agent MUST [explicit positive requirement].
- The agent MUST NOT [explicit prohibited behavior or anti-pattern].

### 2. [Clean Code & Type Safety Invariant]
- Code MUST use strict typing with zero `any` types.
- Preconditions MUST use guard clauses (early return or throw).

## Examples

### Correct Implementation
```typescript
// Production-grade compliant snippet
```

### Incorrect Implementation (FORBIDDEN)
```typescript
// Anti-pattern snippet (FORBIDDEN)
```
````

---

### Sync Instructions:
```bash
# Sync to Global level (~/.gemini/config/rules/)
./bin/sync-context.sh --global [determined-toolkit-path]

# Sync to Workspace level (<project>/.agents/rules/)
./bin/sync-context.sh [determined-toolkit-path] -w /path/to/project
```

---

## Gotchas
- Never set `always_on` for specialized rules; it bloats system prompt tokens across every prompt.
- If `trigger: glob` is set, `globs: [...]` array is mandatory.
- Always quote glob strings (`"**/*.ts"`) to prevent YAML parser errors.
- Never exceed 12,000 characters; IDE hard-truncates any content beyond this limit.
- Wrap rule templates in 4-backticks (````markdown ... ````) to avoid corrupting nested 3-backtick code blocks.
