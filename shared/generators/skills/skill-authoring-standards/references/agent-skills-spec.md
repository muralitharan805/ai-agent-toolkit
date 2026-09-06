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
| `name` | string | **Yes** | 1–64 chars. Lowercase alphanumeric and single hyphens (`^[a-z0-9]+(-[a-z0-9]+)*$`). Must match parent directory name. |
| `description` | string | **Yes** | 1–1024 chars. Non-empty. Imperative, third-person phrasing stating *what* the skill achieves and *when* to activate it. |
| `compatibility`| string | No | 1–500 chars. Environment prerequisites (e.g., `Requires Node.js 20+, Docker, and pnpm`). |
| `license` | string | No | License identifier (e.g., `Apache-2.0`, `MIT`). |
| `metadata` | object | No | Key-value map of string metadata (e.g., `author`, `version`). |
| `allowed-tools`| string | No | Space-separated pre-approved tool execution list. |

### Frontmatter Rules
- **Name Directory Match**: The `name` field in YAML frontmatter MUST exactly match the skill directory name.
- **Trigger-Rich Description**: The `description` field is the primary discovery mechanism for LLMs. It must include domain keywords and explicit activation cues:
  - Good: `Extracts tables and unstructured data from PDF files, fills PDF forms, and validates signatures. Use when parsing PDF invoices or when the user mentions document extraction.`
  - Bad: `Helps with PDFs.`

---

## The 3-Tier Progressive Disclosure Model

To optimize model context economy and prevent prompt bloating, skills must be architected into 3 tiers:

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
