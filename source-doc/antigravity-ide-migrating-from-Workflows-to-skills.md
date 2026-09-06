# Migrating from Workflows to Skills

Learn how to migrate your legacy Antigravity workflows to modern, standard [Agent Skills](/docs/skills).

Deprecation Notice

**Workflows are deprecated and will be retired on November 1, 2026.** Existing workflows will continue to work until this date, but we recommend migrating to **[Agent Skills](/docs/skills)** to take advantage of progressive disclosure, directory-based asset bundling, and open ecosystem interoperability.

## Why Migrate to Skills?

Workflows were originally introduced in the Antigravity IDE as single Markdown files designed for repeatable prompt sequences. While effective for simple instructions, monolithic files presented challenges as tasks grew in complexity.

In May 2026, Antigravity adopted the open industry standard for [Agent Skills](https://agentskills.io/home). Migrating to skills provides significant architectural and operational improvements:

Progressive Context Loading

Skills load only essential metadata (name and description) into the agent’s context upfront. Full instructions and reference materials are loaded on demand, preventing prompt bloat.

Multi-File Directory Bundling

Unlike single-file workflows, a skill is a directory bundle. You can co-locate executable helper scripts, documentation, sample schemas, and reference assets directly alongside `SKILL.md`.

Open Ecosystem Standard

Skills adhere to the cross-platform agent specification, enabling you to share and reuse skills across Antigravity IDE, Antigravity CLI, and other compliant agent tools.

Subagent Integration

Skills can define specialized system prompts, tool requirements, and delegate sub-tasks to custom subagents directly from the skill bundle.

* * *

## Comparison: Workflows vs. Skills

| Feature | Legacy Workflows (`.md`) | Agent Skills (`SKILL.md`) |
| :-- | :-- | :-- |
| **Specification** | Proprietary Antigravity format | Open Agent Skills Standard ([agentskills.io](https://agentskills.io/home)) |
| **Structure** | Single standalone `.md` file | Directory bundle (`<skill-name>/SKILL.md` + assets) |
| **Workspace Path** | `.agents/workflows/<name>.md` | `.agents/skills/<name>/SKILL.md` |
| **Global Path** | `~/.gemini/config/workflows/<name>.md` | `~/.gemini/config/skills/<name>/SKILL.md` |
| **Context Loading** | Entire file loaded into prompt | **Progressive**: Metadata indexed upfront; body loaded on demand |
| **Bundled Assets** | Not supported (everything must fit in 1 prompt) | Supported (`scripts/`, `references/`, `examples/`) |
| **Slash Commands** | Supported (`/<workflow-name>`) | Supported (`/<skill-name>`) |
| **Autonomous Discovery** | Supported | Supported (enhanced semantic matching via description) |
| **File Size Limit** | 12,000 characters | Unrestricted bundle; modular multi-file architecture |

* * *

## Automatic Migration

Antigravity provides an automated migration command that discovers your existing workflows and converts them to skill directory bundles.

### Using `/migrate-workflows`

1.  Open Antigravity 2.0.
2.  Run the migration command:
    
    ```
    /migrate-workflows
    ```
    
3.  The agent will:
    *   Scan both global (`~/.gemini/config/workflows/`) and workspace-level (`.agents/workflows/`) directories.
    *   Parse each workflow’s YAML frontmatter and body.
    *   Scaffold `.agents/skills/<workflow-name>/SKILL.md` with compliant metadata.
    *   Archive original workflow files by appending `.bak` (e.g., `deploy.md` → `deploy.md.bak`).
    *   Immediately activate the new skills for slash commands and autonomous agent usage.

* * *

## Manual Migration Guide

If you prefer to migrate your workflows manually or want to refactor monolithic prompts into modular skill packages, follow these steps.

1.  ### Create the Skill Directory
    
    In your workspace or global configuration directory, create a new folder named after your workflow under `skills/`:
    
    *   [Workspace Skill](#tab-panel-0)
    *   [Global Skill](#tab-panel-1)
    
    ```
    mkdir -p .agents/skills/deploy-staging
    ```
    
    ```
    mkdir -p ~/.gemini/config/skills/deploy-staging
    ```
    
2.  ### Create and Populate `SKILL.md`
    
    Move your existing workflow markdown file to `SKILL.md` inside the new folder:
    
    ```
    mv .agents/workflows/deploy-staging.md .agents/skills/deploy-staging/SKILL.md
    ```
    
3.  ### Standardize the YAML Frontmatter
    
    Ensure your `SKILL.md` begins with the standard `name` and `description` frontmatter fields. The description should clearly explain **what** the skill does and **when** the agent should use it:
    
    ```
    ---
    name: deploy-staging
    description: Deploys the current project build to the staging preview environment on App Engine. Use when testing staging releases or verifying PR previews.
    ---
    
    # Deploy Staging
    
    Follow these instructions to deploy the current build to staging...
    ```
    
4.  ### (Optional) Extract Scripts and Resources
    
    If your workflow contains embedded scripts, code snippets, or lengthy reference documentation, extract them into dedicated subdirectories to keep `SKILL.md` lean:
    
    ```
    .agents/skills/deploy-staging/
    ├── SKILL.md
    ├── scripts/
    │   └── deploy.sh
    └── references/
        └── staging-endpoints.json
    ```
    
    In `SKILL.md`, instruct the agent to run or inspect those files when needed rather than duplicating them in the prompt.
    
5.  ### Verify the Migrated Skill
    
    Invoke the skill directly in Antigravity 2.0:
    
    ```
    /deploy-staging
    ```
    
    You should see the agent load the skill metadata and execute the steps.
    

* * *

## Before & After Migration Example

### Before: Legacy Monolithic Workflow

```
---
name: build-and-test
description: Run test suites and verify build
---

Run the following checks sequentially:
1. First run `npm run check` to verify TypeScript and template integrity.
2. Next execute `npm run test` for unit tests.
3. If tests pass, run `npm run build` and report the generated bundle size.
```

### After: Modular Agent Skill Package

```
.agents/skills/build-and-test/
├── SKILL.md
└── scripts/
    └── verify-bundle.js
```

```
---
name: build-and-test
description: Runs full validation suite including TypeScript checks, unit tests, and production build verification. Use before submitting changes.
---

# Build and Test Suite

Execute the project verification pipeline:

1. **Type & Template Diagnostics**:
   ```bash
   npm run check
   ```

2. **Unit Tests**:
   ```bash
   npm run test
   ```

3. **Production Build & Bundle Size Analysis**:
   ```bash
   npm run build
   node scripts/verify-bundle.js
   ```
```

## Frequently Asked Questions

### Will my workflows stop working immediately?

No. Workflows will remain operational in Antigravity until **November 1, 2026**. After this date, workflow directories will no longer be indexed or executable via slash commands.

### Can I still invoke my migrated skills via slash commands?

Yes. Any skill located in `.agents/skills/<name>/` or `~/.gemini/config/skills/<name>/` can be invoked via `/<name>` in chat, just like legacy workflows.

### What happens if I have both a workflow and a skill with the same name?

Skills take precedence over legacy workflows. If both `.agents/skills/deploy/` and `.agents/workflows/deploy.md` exist, Antigravity will execute the skill.

### Where should I put global skills?

Global skills can be placed in `~/.gemini/config/skills/<skill-name>/SKILL.md`. They will be accessible across all your workspaces.

## Related Documentation

*   [Agent Skills Overview](/docs/skills) – Full guide on creating, configuring, and organizing skills.
*   [Customizing Agent Rules](/docs/ide/rules) – Learn how to define persistent workspace and global rules.
*   [Antigravity CLI Plugins & Skills](/docs/cli/plugins) – Managing skills in the Antigravity CLI.