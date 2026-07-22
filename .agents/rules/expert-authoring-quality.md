---
trigger: always_on
description: "Enforces that all skills, rules, and workflows generated or edited in this workspace reflect senior principal engineer expertise, modern industry standards, and deep technical rigor."
---
# Expert Authoring & Technical Rigor Rule

## Description
This rule mandates that whenever the AI agent creates or modifies skills, rules, or workflows, the generated content must reflect the depth, accuracy, and foresight of a seasoned Principal Software Architect. Output must incorporate modern best practices, clear technical rationale, and non-trivial production-grade examples.

## Constraints
- The agent MUST write all generated skills, rules, and workflows in high-level professional English with zero generic filler text.
- The agent MUST ensure recommendations reflect up-to-date, modern technical standards (e.g., modern Angular signals/M3, latest Node/NestJS patterns, current Docker/Cloud practices).
- The agent MUST provide real-world, production-ready code snippets and non-trivial edge-case handling in examples.
- The agent MUST write `description` fields in third-person with precise semantic keywords to optimize AI agent routing.

## Examples
- **Correct implementation:**
```markdown
# Instructions
1. Implement granular reactive state using Angular Signals (`signal()`, `computed()`) instead of legacy RxJS `BehaviorSubject` for local component state.
2. Wrap external asynchronous streams with `toSignal()` supplying explicit `initialValue` to maintain type safety.
```

- **Incorrect implementation:**
```markdown
# Instructions
1. Write good Angular code.
2. Use variables properly.
```
