# Antigravity Rules Specification & Architecture Guide

## 1. Overview & Purpose
In Google Antigravity IDE, **Rules** are persistent markdown guidelines, constraints, and behavioral policies injected into the agent's context. While Skills provide on-demand procedures and deep workflows, Rules define boundaries, coding conventions, architectural invariants, and security mandates.

Rules can exist at two levels:
1. **Workspace Rules**: Stored in `.agents/rules/*.md` (or root `GEMINI.md` / `AGENTS.md`) affecting the active project.
2. **Global Rules**: Stored in `~/.gemini/config/rules/*.md` applied across all workspaces.

---

## 2. YAML Frontmatter Specification

Every rule file MUST begin with valid YAML frontmatter fenced by `---`.

```yaml
---
description: "Brief third-person description explaining what this rule governs and when it applies."
trigger: model_decision # or glob | always_on | manual
globs:                  # MANDATORY only when trigger is 'glob'
  - "**/*.ts"
  - "!**/*.spec.ts"
---
```

### Supported Frontmatter Fields

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `description` | string | **Yes** | 10–1024 characters. Clear imperative/declarative statement describing domain, technology, and purpose. |
| `trigger` | string | **Yes** | Must be one of: `model_decision`, `glob`, `always_on`, `manual`. |
| `globs` | array of strings | **Conditional** | **Mandatory** if `trigger: glob`. Defines file patterns that automatically activate the rule when opened or edited. |

---

## 3. Trigger Strategy & Token Economy

Rules occupy context window tokens. Selecting the proper trigger prevents context bloat and preserves attention bandwidth.

### 1. `model_decision` (Recommended Default)
- **Mechanism**: The model evaluates the task context and decides whether the rule is relevant.
- **Best For**: Domain-specific standards (e.g. NestJS Clean Architecture, Angular Signal State, Docker Containerization).
- **Advantage**: Zero token penalty when working on unrelated domains.

### 2. `glob` (Deterministic Path Matching)
- **Mechanism**: Automatically triggered when files matching `globs` patterns are read, created, or modified.
- **Best For**: Filetype-specific rules (e.g., `*.prisma`, `*.sql`, `*.component.ts`, `Dockerfile*`).
- **Advantage**: Guarantees compliance whenever specific file types are touched.

### 3. `always_on` (Universal Invariants Only)
- **Mechanism**: Always injected into every single interaction.
- **Best For**: Core workspace invariants that apply across every language and file (e.g. `Clean Code Standards`, `Mandatory pnpm Package Manager`, `No Hardcoded Secrets`).
- **Caution**: Use sparingly. Overloading `always_on` degrades model reasoning speed and wastes token budget.

### 4. `manual` (Explicit User Summon)
- **Mechanism**: Activated exclusively when the user or agent explicitly `@mentions` the rule file.
- **Best For**: Infrequently run audit checklists or specialized migration rubrics.

---

## 4. Size Limits & Modular Splitting Strategy

The Antigravity IDE enforces strict truncation boundaries:
- **Optimal Target**: 6,000 – 8,000 characters (~1,200 – 1,800 tokens).
- **Warning Threshold**: 8,000 – 10,000 characters.
- **Hard IDE Cutoff**: **12,000 characters**. Any content exceeding 12,000 characters is automatically truncated by the IDE, causing lost instructions and invalid syntax.

### How to Split Oversized Rules
When a domain's rules grow beyond 8,000 characters:
1. **Split by Subdomain**: E.g., split `database-rules.md` into:
   - `postgres-schema-migrations.md` (`globs: ["migrations/**", "schema.prisma"]`)
   - `postgres-indexing-and-queries.md` (`trigger: model_decision`)
2. **Extract Procedural Workflows to Skills**: If a rule contains multi-step commands, scripts, or deployment checklists, migrate that procedural logic into an Agent Skill (`skills/<name>/SKILL.md`) and keep the rule focused strictly on constraints and prohibitions.
3. **Trim Redundant Commentary**: Remove long theoretical essays. Focus directly on `MUST` and `MUST NOT` constraints with minimal, high-impact code snippets.

---

## 5. Canonical Rule Structure

A production-grade rule follows this 4-section taxonomy:

```markdown
---
description: "[Concise summary of rule scope]"
trigger: model_decision
---

# [Title]

## Description
[Clear, contextual explanation of the problem, standard, or regulation.]

## Constraints
### 1. [Category / Constraint Name]
- Explicit MUST requirement.
- Explicit MUST NOT / FORBIDDEN anti-pattern.

### 2. [Next Constraint Name]
- Preconditions, boundaries, and validation requirements.

## Examples
### Correct Implementation
```typescript
// Production-grade compliant snippet
```

### Incorrect Implementation (FORBIDDEN)
```typescript
// Anti-pattern snippet clearly marked as prohibited
```
```

---

## 6. Authoring Gotchas
1. **Never use generic placeholders**: Avoid `foo`, `bar`, or non-compiling pseudo-code in examples. Use realistic domain entities.
2. **Quote glob patterns**: Always quote glob entries in YAML (`"**/*.ts"`) to prevent YAML parser syntax errors with asterisks.
3. **Avoid negative constraints without positive alternatives**: If telling the agent what NOT to do, always specify what it MUST do instead.
4. **Enforce Clean Code**: All TypeScript/JavaScript examples in rules MUST have zero `any` types and adhere to strict typing.
