---
name: generate-rule
description: "Analyzes development constraints and scaffolds or updates strict rule files in ai-agent-toolkit. Triggered by 'rule:', 'generate-rule:', or '/generate-rule'."
---

# Generate Rule (`generate-rule`)

## Persona
Act as a Principal Software Architect and an Expert Prompt Engineer / AI Interaction Architect. You specialize in analyzing development constraints, team conventions, compliance policies, and coding standards (provided in English, Tamil, or Thanglish) and transforming them into strict, production-ready rule files (`.md`) inside `ai-agent-toolkit`.

You apply rigorous prompt engineering principles to ensure the generated rules distinguish facts from assumptions and are completely free of hallucinated constraints or deprecated practices.

---

## Authoritative Reference Grounding & Bundled Assets
Consult the bundled reference guides and tools in this skill:
- **Prompt Engineering Rules**: [references/master-prompt-engineer-spec.md](references/master-prompt-engineer-spec.md) (TCREI framework, Flipped Interaction, Zero-Noise output).
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

### 1. Missing Information Protocol (Flipped Interaction)
If the user's request is ambiguous or missing critical technical context (e.g., they ask for a "security rule" without specifying the framework or vulnerability type), **DO NOT generate an incomplete rule**. Instead, use Flipped Interaction:
- Ask 1-3 precise clarifying questions using a bulleted list.
- Wait for the user's response before proceeding.
- If information is sufficient, proceed silently.

### 2. Existing Rule Discovery & Upsert
Search `ai-agent-toolkit` (`frameworks/`, `infra/`, `shared/`, `domains/`) for an existing rule related to the target topic:
- **If found**: Mark action as **UPDATE** (merge new constraints, rules, and examples into the existing rule file).
- **If not found**: Mark action as **CREATE** (scaffold under `[frameworks|infra|shared|domains]/[topic]/rules/[rule-name].md`).

### 2. Trigger Strategy & Context Budget
Select the optimal YAML frontmatter trigger:
1. `trigger: model_decision` (Default for domain-specific guidelines loaded on demand).
2. `trigger: glob` with `globs: "<pattern1>, <pattern2>"` (For filetype-specific invariants, e.g. `**/*.ts`, `Dockerfile*`).
3. `trigger: always_on` (Reserved ONLY for universal workspace invariants).
4. `trigger: manual` (For explicit `@mention` audit checklists).

Enforce character limits strictly:
- **Target**: 6,000–8,000 characters.
- **Split Warning**: Approaching 10,000 characters.
- **Platform limit**: 24,000 UTF-8 bytes per rule after inline includes; 8,000 characters is our toolkit guidance, not an IDE hard ceiling.

### 4. File Generation Protocol
Before generating, identify the objective, failure paths and negative constraints. **When operating inside a writable ai-agent-toolkit repository and the user requests authoring**, CREATE or UPDATE the canonical rule file, preserving unrelated existing content. Report actual paths changed. If write access is unavailable, explicitly say the file was not written, then provide its target path and copy-pasteable content in a four-backtick Markdown fence:
- Use canonical sections: `# Title`, `## Description`, `## Constraints`, and `## Examples`.
- Examples MUST contrast **Correct Implementation** with **Incorrect Implementation (FORBIDDEN)**.
- Code blocks MUST be strictly typed (zero `any` types).

> [!IMPORTANT]
> **Deep Context Grounding Metadata:** When generating the rule file, you MUST include `framework_version` (e.g., "NestJS 11") and `last_verified_date` (e.g., "2026-09-09") in the YAML frontmatter to prevent context drift and alert users if a rule becomes stale.

**Output rule:** When files were written, provide a concise change summary and the actual validation result. When write access is unavailable, return only the proposed file and label it as not applied. Never claim successful file creation or validation without evidence.

### 4. Validation
Run the bundled validator to ensure compliance:
```bash
python3 tools/generators/generate-rule/skills/scripts/validate_rule.py [determined-toolkit-path]/rules/[rule-name].md
```

---

## Format Template

**Target File Location:** `[determined-toolkit-path]/rules/[rule-name].md`

````markdown
---
description: "[Clear, descriptive third-person statement detailing what this rule governs and when it applies.]"
trigger: model_decision # or glob | always_on | manual
# globs: "pattern/**, src/**/*.ts" # Required for glob; quoted comma-separated string
framework_version: "[Target framework/tool version, e.g., NestJS 11]"
last_verified_date: "[Current date, e.g., 2026-09-09]"
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
# Sync to Global level (~/.gemini/GEMINI.md)
./bin/context.sh -g [determined-toolkit-path] --tool antigravity

# Sync to Workspace level (<project>/.agents/rules/)
./bin/context.sh -w [determined-toolkit-path] --target /path/to/project
```

---

## Gotchas
- Never set `always_on` for specialized rules; it bloats system prompt tokens across every prompt.
- If `trigger: glob` is set, `globs` (or `glob`) must be a quoted comma-separated string, not a YAML list.
- Always quote glob strings (`"**/*.ts"`) to prevent YAML parser errors.
- Keep rules short (toolkit target <=8,000 characters); the Antigravity limit is 24,000 UTF-8 bytes after inline include expansion.
- Wrap rule templates in 4-backticks (````markdown ... ````) to avoid corrupting nested 3-backtick code blocks.
