---
description: "[Clear, descriptive third-person statement detailing what this rule governs, technologies affected, and when it applies.]"
trigger: model_decision # Options: model_decision | glob | always_on | manual
# globs: ["src/**/*.ts", "!src/**/*.spec.ts"] # Required only if trigger is 'glob'
---

# [Rule Title / Functional Identifier]

## Description
[Provide a clear, prescriptive explanation of what this rule governs and why it is active.]

## Constraints

### 1. [Mandatory Policy Name]
- The agent MUST [explicit positive requirement].
- The agent MUST NOT [explicit prohibited behavior or anti-pattern].

### 2. [Type Safety & Clean Code Invariant]
- Code MUST use strict typing with zero `any` types.
- Preconditions MUST use guard clauses (early return or throw).

## Examples

### Correct Implementation
```typescript
// Production-grade compliant snippet
export function processEntity(id: string): EntityState {
  if (!id) {
    throw new InvalidArgumentException("Entity ID cannot be empty");
  }
  return { id, status: "ACTIVE" };
}
```

### Incorrect Implementation (FORBIDDEN)
```typescript
// Anti-pattern snippet (FORBIDDEN)
export function processEntity(id: any): any {
  return { id, status: "ACTIVE" }; // Unvalidated, any type
}
```
