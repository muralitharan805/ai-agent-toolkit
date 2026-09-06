---
name: skill-authoring-standards
description: Comprehensive authoring standards for creating or updating enterprise Agent Skills, Rules, and Workflows. Enforces 3-tier progressive disclosure, directory bundling (references, scripts, assets, evals), PEP 723 self-contained tooling, and official Antigravity IDE specifications.
---

# Agent Context Authoring Standards

This skill guides the creation and maintenance of world-class AI agent context (Skills, Rules, Workflows) adhering to the Agent Skills Open Standard and Google Antigravity IDE architecture.

---

## 1. The 4-Pillar Skill Architecture

Every production-grade skill is organized as a directory bundle rather than a flat monolithic text file:

```
<skill-name>/
├── SKILL.md                 # Required: Core instructions + progressive disclosure links (< 500 lines)
├── references/              # Detailed technical documentation loaded on demand
├── scripts/                 # Self-contained executable scripts (stdout JSON, stderr diagnostics)
├── assets/ (or examples/)   # Schemas, templates, sample implementations
└── evals/                   # Test cases & assertions (evals.json) for quality verification
```

---

## 2. 3-Tier Progressive Disclosure Model

Context is loaded in three stages to prevent prompt bloating:

1. **Tier 1 (Startup ~100 tokens)**: `name` and `description` in YAML frontmatter. Must use imperative phrasing detailing *what* the skill achieves and *when* the agent should activate it.
2. **Tier 2 (Activation < 500 lines)**: `SKILL.md` body containing high-level procedures, decision trees, Gotchas, and relative links to Tier 3.
3. **Tier 3 (On-Demand)**: Granular files in `references/`, `scripts/`, or `assets/` loaded *only* when the agent encounters that specific task phase.

---

## 3. Sub-Documentation Routing Map

When authoring or updating context, inspect the specialized reference guides in `references/` on demand:

- **Format Specification & Frontmatter**: [references/agent-skills-spec.md](references/agent-skills-spec.md)
  - Name regex constraints, 1024-char description rules, frontmatter fields, and directory structure.
- **Best Practices & Gotchas Pattern**: [references/best-practices-and-gotchas.md](references/best-practices-and-gotchas.md)
  - Context economy ("add what agent lacks, omit what it knows"), defaults over menus, and Gotchas design.
- **Scripts & Tooling Design**: [references/script-and-tool-design.md](references/script-and-tool-design.md)
  - PEP 723 Python scripts, Deno imports, stdout/stderr separation, and black-box `--help` testing.
- **Skill Evaluations & Testing**: [references/evaluating-and-testing-skills.md](references/evaluating-and-testing-skills.md)
  - Test suites (`evals/evals.json`), verifiable assertions, trigger evaluation queries, and zero production token bloat.
- **Antigravity Customizations Guide**: [references/antigravity-customizations-guide.md](references/antigravity-customizations-guide.md)
  - Rules triggers (`model_decision`, `glob`, `always_on`), 12k char limits, `hooks.json` events, `mcp_config.json`, and Workflows deprecation.

---

## 4. Bundled Automation Tools & Reference Blueprints

- **Skill Validator Utility**:
  Run the bundled self-contained validator script against any skill:
  ```bash
  python3 scripts/validate_skill.py <path-to-skill-dir>
  ```
  Supports `--help` for synopsis and `--strict` for zero-warning enforcement.
- **Reference Implementation**:
  Inspect [examples/modular-skill-blueprint/](examples/modular-skill-blueprint/) for an end-to-end working blueprint.

---

## 5. Gotchas

- **Monolithic Trap**: Never dump comprehensive API references or entire schemas into `SKILL.md`. Always offload reference docs to `references/[topic].md` and link them.
- **Name Directory Parity**: The `name` frontmatter field MUST exactly match the parent folder name (`^[a-z0-9]+(-[a-z0-9]+)*$`).
- **Data on stdout, Diagnostics on stderr**: All helper scripts MUST emit structured data (JSON/CSV) to stdout so agents can parse it, and human logs/progress to stderr.
- **Rule Character Ceilings**: Rule files MUST target 6,000–8,000 characters and strictly never exceed 12,000 characters (IDE truncation limit).

---

## 6. Pre-Commit Quality Gate Checklist

Before committing or syncing any generated context:
1. `SKILL.md` is under 500 lines and contains a `## Gotchas` section.
2. Frontmatter `description` uses third-person imperative phrasing with explicit keywords.
3. Complex technical reference material lives in `references/*.md`.
4. Any bundled scripts support `--help` and separate stdout data from stderr diagnostics.
5. An `evals/evals.json` test suite is provided with 2–3 realistic test prompts and verifiable assertions.
