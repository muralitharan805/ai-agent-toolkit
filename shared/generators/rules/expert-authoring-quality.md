---
trigger: always_on
description: "Enforces that all skills, rules, and workflows generated or edited in this workspace reflect senior principal engineer expertise, modern industry standards, zero duplication, smart upsert behavior, and strict YAML frontmatter GUI compatibility."
---
# Expert Authoring & Technical Rigor Rule

## Description
This rule mandates that whenever the AI agent creates or modifies skills, rules, or workflows, the generated content must reflect the depth, accuracy, and foresight of a seasoned Principal Software Architect. Output must incorporate modern best practices, clear technical rationale, non-trivial production-grade examples, strict deduplication, and 100% GUI-compatible YAML frontmatter.

## Constraints
- The agent MUST write all generated skills, rules, and workflows in high-level professional English with zero generic filler text.
- **DEDUPLICATION & UPSERT RULE**: Before creating a new file, the agent MUST inspect the workspace (`frameworks/`, `infra/`, `shared/`, `.agents/`) for existing skills, rules, or workflows covering the target topic. If a related file exists, the agent MUST update and merge new requirements into the existing file instead of creating a duplicate.
- **YAML FRONTMATTER GUI COMPATIBILITY RULE**:
  - Workflows MUST use ONLY standard, parser-compatible YAML keys: `description` and `trigger`.
  - NEVER use non-standard or unparsed YAML keys like `aliases:` or custom metadata objects.
  - Trigger phrases and shorthand keywords MUST be embedded directly inside the `description` string (e.g., `Triggered by 'suite:', 'context:', or '/generate-agent-suite'`).
  - Skills MUST use `name` (kebab-case) and `description` (third-person routing statement).
  - Rules MUST use `trigger: always_on` or `trigger: glob` with a clear `description`.
- The agent MUST ensure recommendations reflect up-to-date, modern technical standards (e.g., modern Angular signals/M3, latest Node/NestJS patterns, current Docker/Cloud practices).
- The agent MUST provide real-world, production-ready code snippets and non-trivial edge-case handling in examples.

## Examples
- **Correct Workflow Frontmatter:**
```yaml
---
description: "Workflow to scaffold enterprise Angular apps. Triggered by 'scaffold-angular:', 'scaffold:', or '/scaffold-enterprise-angular-project'."
trigger: manual
---
```

- **Incorrect Workflow Frontmatter:**
```yaml
---
description: "Scaffold workflow"
trigger: manual
aliases:
  - "scaffold:"
  - "scaffold-angular:"
---
```
