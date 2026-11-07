# Agent Skills Format Specification

> Grounded in the official open standard for Agent Skills (agentskills.io) and Google Antigravity IDE.

## Directory Structure

An Agent Skill is a directory bundle containing, at minimum, a `SKILL.md` file:

```
<skill-name>/
├── SKILL.md          # Required: metadata + instructions (< 500 lines)
├── references/       # Optional: granular documentation loaded on demand
├── scripts/          # Optional: executable tools and automations
├── assets/           # Optional: templates, schemas, and static resources
└── evals/            # Optional: test cases and assertions (evals.json)
```

**Platform format vs toolkit convention:** `SKILL.md` is the required file. The supporting directories are optional, not mandatory parts of the Antigravity skill format. Antigravity's examples also use `examples/` for implementations and `resources/` for templates or other resources. This toolkit prefers the more specific `references/`, `scripts/`, `assets/`, and `evals/` organization for consistent authoring and validation. Add only folders that the skill actually needs.

---

## `SKILL.md` Frontmatter Specification

Every `SKILL.md` must begin with YAML frontmatter bounded by `---`:

```yaml
---
name: skill-name
description: A third-person imperative description detailing what the skill does and when the agent should activate it.
---
```

### Frontmatter Schema

| Field | Type | Required | Constraints & Description |
| :--- | :--- | :---: | :--- |
| `name` | string | **Toolkit: Yes**; Antigravity: No | Antigravity can infer the name from the skill folder when omitted. This toolkit requires an explicit name for deterministic validation, using 1–64 lowercase alphanumeric characters and single hyphens (`^[a-z0-9]+(-[a-z0-9]+)*# Agent Skills Format Specification

> Grounded in the official open standard for Agent Skills (agentskills.io) and Google Antigravity IDE.

## Directory Structure

An Agent Skill is a directory bundle containing, at minimum, a `SKILL.md` file:

```
<skill-name>/
├── SKILL.md          # Required: metadata + instructions (< 500 lines)
├── references/       # Optional: granular documentation loaded on demand
├── scripts/          # Optional: executable tools and automations
├── assets/           # Optional: templates, schemas, and static resources
└── evals/            # Optional: test cases and assertions (evals.json)
```

**Platform format vs toolkit convention:** `SKILL.md` is the required file. The supporting directories are optional, not mandatory parts of the Antigravity skill format. Antigravity's examples also use `examples/` for implementations and `resources/` for templates or other resources. This toolkit prefers the more specific `references/`, `scripts/`, `assets/`, and `evals/` organization for consistent authoring and validation. Add only folders that the skill actually needs.

---

## `SKILL.md` Frontmatter Specification

Every `SKILL.md` must begin with YAML frontmatter bounded by `---`:

```yaml
---
name: skill-name
description: A third-person imperative description detailing what the skill does and when the agent should activate it.
---
```

### Frontmatter Schema

| Field | Type | Required | Constraints & Description |
| :--- | :--- | :---: | :--- |
), matching the folder name. |
| `description` | string | **Yes** | Required for skill discovery. This toolkit additionally enforces a non-empty 1–1024 character description, preferably third-person phrasing stating *what* the skill achieves and *when* to activate it. |
| `compatibility`| string | No | 1–500 chars. Environment prerequisites (e.g., `Requires Node.js 20+, Docker, and pnpm`). |
| `license` | string | No | License identifier (e.g., `Apache-2.0`, `MIT`). |
| `metadata` | object | No | Key-value map of string metadata (e.g., `author`, `version`). |
| `allowed-tools`| string | No | Space-separated pre-approved tool execution list. |

### Frontmatter Rules

These are **toolkit authoring and validation requirements**, which can be stricter than Antigravity's accepted skill format. In the Antigravity documentation supplied for this review, `name` is optional and defaults to the folder name; `description` is required. The existing `validate_skill.py` intentionally requires `name`, so do not remove it from toolkit-authored skills.

- **Name Directory Match (toolkit policy)**: The `name` field in YAML frontmatter MUST be present and exactly match the skill directory name.
- **Trigger-Rich Description**: The `description` field is the primary discovery mechanism for LLMs. It must include domain keywords and explicit activation cues:
  - Good: `Extracts tables and unstructured data from PDF files, fills PDF forms, and validates signatures. Use when parsing PDF invoices or when the user mentions document extraction.`
  - Bad: `Helps with PDFs.`

---

## The 3-Tier Progressive Disclosure Model

To optimize model context economy and prevent prompt bloating, this toolkit **recommends** a 3-tier authoring model. The 500-line target and supporting-folder organization below are toolkit conventions, not minimum requirements for an Antigravity skill:

1. **Tier 1: Metadata (~100 tokens)**:
   - Only `name` and `description` are loaded into system context at conversation startup.
   - Used exclusively by the agent to evaluate whether a user's prompt warrants activating the skill.

2. **Tier 2: Core Instructions (< 500 lines / < 5,000 tokens)**:
   - The body of `SKILL.md` is loaded ONLY when the skill is activated.
   - Contains high-level procedures, decision trees, Gotchas, and pointers to Tier 3.

3. **Tier 3: Specialized Resources (Loaded on Demand)**:
   - Granular technical files under `references/`, executable scripts in `scripts/`, or schemas in `assets/`.
   - The agent reads these files ONLY when the task reaches that specific branch or sub-step.
   - Instruction pattern in `SKILL.md`: `If configuring OAuth2 providers, read references/oauth-providers.md`.

---

## File Reference Conventions
- Always use relative markdown links from the skill root: `[OAuth Guide](references/oauth-providers.md)`.
- Never use machine-specific absolute paths in skill instructions.
