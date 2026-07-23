---
trigger: always_on
description: "Enforces that all skills, rules, and workflows generated or edited in this workspace reflect senior principal engineer expertise, modern industry standards, zero duplication, and smart upsert behavior."
---
# Expert Authoring & Technical Rigor Rule

## Description
This rule mandates that whenever the AI agent creates or modifies skills, rules, or workflows, the generated content must reflect the depth, accuracy, and foresight of a seasoned Principal Software Architect. Output must incorporate modern best practices, clear technical rationale, non-trivial production-grade examples, and strict deduplication.

## Constraints
- The agent MUST write all generated skills, rules, and workflows in high-level professional English with zero generic filler text.
- **DEDUPLICATION & UPSERT RULE**: Before creating a new file, the agent MUST inspect the workspace (`frameworks/`, `infra/`, `shared/`, `.agents/`) for existing skills, rules, or workflows covering the target topic. If a related file exists, the agent MUST update and merge new requirements into the existing file instead of creating a duplicate.
- The agent MUST ensure recommendations reflect up-to-date, modern technical standards (e.g., modern Angular signals/M3, latest Node/NestJS patterns, current Docker/Cloud practices).
- The agent MUST provide real-world, production-ready code snippets and non-trivial edge-case handling in examples.
- The agent MUST write `description` fields in third-person with precise semantic keywords to optimize AI agent routing.

## Examples
- **Correct implementation (Upserting existing file):**
  - Scenario: Add dark mode tokens to Angular Material skill.
  - Action: Update `frameworks/angular/skills/angular-material-styling/SKILL.md` by appending dark mode instructions and examples, preserving existing content.

- **Incorrect implementation (Duplicate file creation):**
  - Action: Creating `frameworks/angular/skills/angular-material-dark-mode/SKILL.md` when `angular-material-styling/SKILL.md` already exists.
