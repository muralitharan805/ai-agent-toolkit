---
trigger: always_on
description: "Enforces that all skills, rules, and workflows generated or edited in this workspace reflect senior principal engineer expertise, modern industry standards, zero duplication, smart upsert behavior, modular directory bundling (references, scripts, assets, evals), progressive disclosure, and strict YAML frontmatter GUI compatibility."
---

# Expert Authoring & Technical Rigor Rule

## Description
This rule mandates that whenever the AI agent creates or modifies skills, rules, or workflows, the generated content must reflect the depth, accuracy, and foresight of a seasoned Principal Software Architect. Output must incorporate modern best practices, clear technical rationale, non-trivial production-grade examples, strict deduplication, modular directory bundling, and 100% GUI-compatible YAML frontmatter.

## Constraints

### 1. Linguistic & Technical Rigor
- The agent MUST write all generated skills, rules, and workflows in high-level professional English with zero generic filler text.
- Generated code snippets MUST be production-ready, strictly typed (zero `any` types), and reflect current framework versions (e.g., Angular signals/M3, NestJS Clean Architecture, latest Docker/Cloud standards).

### 2. Deduplication & Smart Upsert
- Before creating a new file, the agent MUST inspect the workspace (`frameworks/`, `infra/`, `shared/`, `domains/`, `.agents/`) for existing skills, rules, or workflows covering the target topic.
- If a related file exists, the agent MUST update and merge new requirements into the existing file instead of creating a duplicate.

### 3. Modular Skill Bundling & Progressive Disclosure
- **3-Tier Progressive Disclosure**: Skills MUST be structured so `name` and `description` act as Tier 1 metadata, `SKILL.md` body (< 500 lines) acts as Tier 2 core guidance, and deep documentation lives in Tier 3 on-demand files.
- **Directory Bundling**: When domain requirements are complex, the agent MUST scaffold a modular directory bundle:
  - `SKILL.md`: High-level procedures and relative links to sub-documents.
  - `references/[topic].md`: Granular technical guides and API specs.
  - `scripts/[tool].py|sh`: Self-contained automation tools.
  - `assets/[template].json`: Concrete output templates and schemas.
  - `evals/evals.json`: Quality verification test cases with objective assertions.
- **Mandatory Gotchas Section**: Every skill MUST include a `## Gotchas` section capturing non-obvious traps, soft deletes, schema quirks, and edge cases.
- **Agentic Scripts Standard**: Any script bundled in `scripts/` MUST emit structured data (JSON/CSV) to `stdout`, diagnostics to `stderr`, support `--help`, and enforce idempotency.

### 4. Rule Size & Modularity
- Rule files MUST target 6,000–8,000 characters (optimal for token economy).
- If content approaches 10,000 characters, the agent MUST split it into focused modular sub-rules. The absolute hard ceiling is 12,000 characters (IDE truncation limit).
- Rules MUST select the most token-efficient trigger: `model_decision` for situational logic, `glob` with `globs: [...]` for filetype/path patterns, or `manual`. Avoid blanket `always_on` defaults.

### 5. YAML Frontmatter GUI Compatibility
- **Workflows**: Use ONLY `description` (strictly `<= 250 characters` with embedded triggers for clean IDE menu rendering) and `trigger: manual`. NEVER use forbidden keys like `aliases:`.
- **Skills**: Must include `name` (kebab-case, matching directory name) and `description` (1–1024 characters, imperative phrasing detailing *what* it does and *when* to use it).
- **Rules**: Must include `description` and valid `trigger` (`model_decision`, `glob`, `always_on`, or `manual`).

## Examples

- **Correct Workflow Frontmatter:**
```yaml
---
description: "Workflow to scaffold enterprise Angular apps. Triggered by 'scaffold-angular:', 'scaffold:', or '/scaffold-enterprise-angular-project'."
trigger: manual
---
```

- **Incorrect Workflow Frontmatter (FORBIDDEN):**
```yaml
---
description: "Scaffold workflow"
trigger: manual
aliases:
  - "scaffold:"
  - "scaffold-angular:"
---
```
