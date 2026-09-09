# Antigravity Customizations Architecture Guide

> Authoring specifications for Rules, Hooks, MCP Servers, Plugins, and Workflow-to-Skill migration in Google Antigravity.

## 1. Customization Scopes & Discovery Roots

Antigravity discovers customizations across two distinct scopes:

| Scope | Location | Primary Use Case |
| :--- | :--- | :--- |
| **Workspace Scope** | `<workspace-root>/.agents/` | Project-specific conventions, schemas, CI pipelines |
| **Global Scope** | `~/.gemini/config/` (and `~/.gemini/GEMINI.md`) | Universal rules, cross-project dev tools |

---

## 2. Rules Architecture (`rules/` & `GEMINI.md`)

Rules define non-negotiable constraints that guide the agent's behavior.

### Scope Locations
- **Workspace Rules**: Saved as `.agents/rules/<rule-name>.md`.
- **Global Rules**: Configured exclusively inside `~/.gemini/GEMINI.md` (applied across all workspaces).

### Activation Triggers
Specify the activation mechanism in the YAML frontmatter:
```yaml
---
description: "Enforces strict TypeScript typing across workspace files."
trigger: model_decision
---
```

1. **`model_decision`**: Default for specialized guidelines. The model dynamically evaluates the description and activates the rule only when relevant.
2. **`glob`**: Automatically applies whenever the agent reads/edits matching file paths:
   ```yaml
   trigger: glob
   globs: ["src/**/*.ts", "tests/**/*.ts"]
   ```
3. **`always_on`**: Loaded into every prompt. Reserve strictly for foundational standards (Clean Code, no secrets).
4. **`manual`**: Activated only when explicitly referenced by the user via `@rule-name`.

### Budget & Size Limits
- Target: **6,000–8,000 characters** per rule.
- Split threshold: Split modularly if approaching 10,000 characters.
- Hard limit: Never exceed **12,000 characters** (hard IDE truncation cutoff).

---

## 3. Workflows Deprecation & Migration to Skills

> [!WARNING]
> **Workflows Deprecation Notice**: Legacy standalone Workflows (`.agents/workflows/*.md`) are scheduled for retirement by **November 1, 2026**.

### Why Skills Replace Workflows
- **Progressive Loading**: Workflows load entire files upfront (bloating prompt); Skills load metadata upfront and pull instructions on demand.
- **Directory Bundling**: Skills support co-located `scripts/`, `references/`, and `assets/`.
- **Slash Commands**: Migrated skills natively support the exact same slash commands (`/<skill-name>`).

### Migration Pattern
Convert legacy `.agents/workflows/<name>.md` into:
```
.agents/skills/<name>/
├── SKILL.md
└── references/
```

---

## 4. Hooks Architecture (`hooks.json`)

Hooks execute custom scripts or shell commands at specific points during Antigravity's execution loop:
- Location: `.agents/hooks.json` or `~/.gemini/config/hooks.json`.

### Supported Lifecycle Events
1. **`PreToolUse`**: Fires before a tool runs. Matcher filters by tool name regex. Returns `decision`: `"allow"`, `"deny"`, `"ask"`, or `"force_ask"`.
2. **`PostToolUse`**: Fires after tool completion.
3. **`PreInvocation`**: Fires before Antigravity calls the model. Can inject context.
4. **`PostInvocation`**: Fires after tool calls finish.
5. **`Stop`**: Fires when execution loop terminates. Can return `decision: "continue"` with `reason` to prevent stopping.

---

## 5. Model Context Protocol (`mcp_config.json`)

MCP servers bridge external APIs, databases, and local developer tools:
- Location: `.agents/mcp_config.json` (workspace) or `~/.gemini/config/mcp_config.json` (global).
- Transport options: `command` + `args` for local `stdio` processes, or `serverUrl` for remote `Streamable HTTP` / `SSE`.

---

## 6. Plugins Architecture (`plugins/`)

Plugins bundle skills, rules, hooks, and MCP servers into an isolated, namespaced package:
```
plugins/<plugin-name>/
├── plugin.json       # Required manifest {"name": "my-plugin"}
├── mcp_config.json   # Optional MCP servers
├── hooks.json        # Optional hooks
├── skills/           # Optional skills
└── rules/            # Optional rules
```
Located in `.agents/plugins/` (workspace) or `~/.gemini/config/plugins/` (global).
