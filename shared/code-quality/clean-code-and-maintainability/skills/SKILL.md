---
name: clean-code-and-maintainability
description: Enforces Robert C. Martin's Clean Code principles, mandatory TSDoc/JSDoc block comments, strict TypeScript typing (no any type), function length limits, parameter DTO encapsulation, and guard clauses. Triggered by 'clean-code:', 'refactor:', or 'code-quality:'.
---

# Clean Code & Maintainability Standards Skill

## Overview

This skill guides AI coding agents and software engineers in writing enterprise-grade, self-documenting, and scalable software adhering to Robert C. Martin's **Clean Code** principles, **SOLID design patterns**, and strict **TypeScript zero-`any` invariants**. It guarantees that any junior or fresher developer can understand and maintain the codebase with minimal cognitive load.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                          5-Phase Clean Code Lifecycle                          │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Naming & Constants]   ──► Intention-revealing names & Enums
               │
  [Phase 2: Scope & Parameters]   ──► Max 35 lines/func, <= 3 positional parameters
               │
  [Phase 3: Guard Clauses]        ──► Max 2 nesting levels, early return / throw
               │
  [Phase 4: Strict Zero-Any]      ──► Type narrowing with `unknown`, type guards
               │
  [Phase 5: Mandatory TSDoc]      ──► Public APIs documented with @param & @returns
```

---

## 5-Phase Execution Pipeline

### Phase 1: Intention-Revealing Naming & Magic Value Elimination
1. **Self-Documenting Identifiers**:
   - Variable, function, and class names must clearly communicate their purpose without requiring inline comments.
   - Single-letter variable names are strictly forbidden, except for basic loop indexes (`i`, `j`).
2. **Magic Value Elimination**:
   - Never embed numeric constants or raw status strings in business logic:
   ```typescript
   // Bad: Magic number
   if (status === 2) { ... }

   // Good: TypeScript Enum
   export enum OrderStatus {
     PENDING = 'PENDING',
     COMPLETED = 'COMPLETED',
   }
   if (status === OrderStatus.COMPLETED) { ... }
   ```

### Phase 2: Function Scope & Parameter Reduction
1. **Length Limit ($\le 35$ Lines)**:
   - Functions must not exceed 35 lines of executable logic. Extract secondary transformations into private helper methods.
2. **Positional Parameter Limit ($\le 3$ Parameters)**:
   - Functions requiring 4 or more inputs must encapsulate them into a typed DTO interface or options object:
   ```typescript
   // Bad: 5 positional parameters
   function createInvoice(user: string, total: number, tax: number, date: Date, ref: string)

   // Good: Encapsulated DTO
   function createInvoice(dto: CreateInvoiceDto): Invoice
   ```

### Phase 3: Guard Clauses & Deep Nesting Flattening
1. **Flattening Conditional Pyramids**:
   - Code must not contain nested `if/else` conditions deeper than 2 levels.
   - Validate preconditions at the top of the function and return or throw immediately:
   ```typescript
   // Good: Guard clause with early throw
   function activateAccount(user: User | null): void {
     if (!user) {
       throw new NotFoundException('User entity not found');
     }
     if (user.isSuspended) {
       throw new ForbiddenException('Suspended accounts cannot be activated');
     }
     user.isActive = true;
   }
   ```

### Phase 4: Strict Zero-`any` Typing & Type Narrowing
1. **Zero `any` Invariant**:
   - Explicit `any` type annotations (`: any`, `as any`, `<any>`) are strictly forbidden across application and test code.
2. **Safe Narrowing with `unknown`**:
   - Validate un-trusted external inputs (HTTP bodies, message queues) using user-defined type guard predicates (`value is TargetType`) before accessing properties.

### Phase 5: Mandatory TSDoc / JSDoc Block Comments
1. **Public API Documentation**:
   - Every exported class, interface, service method, controller endpoint, and public utility MUST include a TSDoc block comment (`/** ... */`).
2. **Required Tags**:
   - Document domain purpose, all `@param` inputs, `@returns` payload, and `@throws` exceptions. Include `@example` blocks for complex utilities.

---

## Local References & Assets

- **Clean Code & SOLID Patterns Guide**: [references/clean-code-and-solid-patterns.md](references/clean-code-and-solid-patterns.md)
- **TypeScript Strict Typing & Narrowing**: [references/typescript-strict-typing-and-narrowing.md](references/typescript-strict-typing-and-narrowing.md)
- **Automated Clean Code CLI Auditor**: [scripts/audit_clean_code.py](scripts/audit_clean_code.py)
- **Enterprise Clean Code Checklist**: [assets/clean-code-checklist.json](assets/clean-code-checklist.json)
- **TSDoc Starter Templates Collection**: [assets/tsdoc-starter-templates.json](assets/tsdoc-starter-templates.json)

---

## Automated Verification Protocol

Run the bundled CLI tool to audit source directories for clean code compliance:
```bash
python3 scripts/audit_clean_code.py --path src/ --strict
```

---

## Gotchas & Anti-Patterns

| Anti-Pattern | Why It Fails | Modern Clean Code Replacement |
| :--- | :--- | :--- |
| **Using Explicit `any`** | Silently turns off TypeScript compiler, allowing runtime bugs to escape to production. | Use `unknown` with user-defined type guards or specific interfaces. |
| **Monolithic 100-Line Functions** | Violates Single Responsibility, impossible to unit test effectively, overwhelms juniors. | Decompose into focused private helpers with single responsibilities ($\le 35$ lines). |
| **4+ Positional Parameters** | Easily causes transposed arguments at call sites (e.g. swapping `tax` and `discount`). | Wrap multiple parameters into a typed DTO options object. |
| **Deeply Nested `if/else` (3+ Levels)** | Creates cognitive overload and cyclomatic complexity explosions. | Flatten execution paths using early return or early throw guard clauses. |
| **Undocumented Public APIs** | Forces consumers and new developers to reverse-engineer implementation details. | Mandatory TSDoc block comments with `@param`, `@returns`, and `@throws`. |
| **Magic Numbers in Conditionals** | Obscures domain intent (`status === 3` is meaningless without external lookup). | Define explicit TypeScript `enum`s or `readonly` constant dictionaries. |
