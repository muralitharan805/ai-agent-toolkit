# agent-toolkit

Central repository of reusable **skills**, **rules**, and **workflows** for AI coding agents (e.g. Google Antigravity IDE). Instead of writing agent context from scratch in every project, this toolkit lets you scaffold, generate, or sync consistent context into any project workspace (`.agents/`) or globally into your system (`~/.gemini/`) — Angular, Node, NestJS, Strapi, Docker, PostgreSQL, Redis, or otherwise.

## Why this exists

Every project's `.agents/` folder tends to be written once and then drift — different naming, inconsistent structure, no reuse across projects. This repo centralizes that knowledge so:

- New projects get a battle-tested `.agents/` setup on day one.
- Existing projects can pull in updates without hand-copying files.
- Personal global environments (`~/.gemini/`) can be synced with common rules, skills, and workflows.
- Framework-specific knowledge (Angular, NestJS, Strapi, Docker, Postgres, Redis...) lives in one place instead of being duplicated per repo.

## Google Antigravity IDE Compatibility ⚡

This repository is 100% natively compatible with **Google Antigravity IDE**:

- **Native `.agents/` & `~/.gemini/` Discovery**: Target directories map directly to `.agents/skills/`, `.agents/rules/`, `.agents/workflows/` (Workspace) and `~/.gemini/antigravity/skills/`, `~/.gemini/config/` (Global) for automatic IDE indexing.
- **Strict GUI-Compatible Frontmatter**: Follows exact YAML frontmatter schemas (`name`, `description`, `trigger: always_on`, `trigger: glob`, `trigger: manual`) to render cleanly in Antigravity's UI.
- **Slash Commands & Shorthand Triggers**: Designed to respond instantly to native slash commands (`/generate-agent-suite`, `/consolidate-agent-toolkit`) and prompt prefixes (`suite:`, `context:`).
- **Direct Physical Sync Utility**: Uses `bin/sync-context.sh` to copy physical files directly into `.agents/` or `~/.gemini/` without symbolic link breaks.

---

## Two-Stage Generation & Sync Paradigm

```text
[User Requirement / Scenario]
         │
         ▼
[1. Generate inside Toolkit] ──► /generate-agent-suite (or /generate-skill, /generate-rule)
                                  Creates or updates modular context under frameworks/, infra/, or shared/
         │
         ▼
[2. Sync to Target Scope]   ──► bin/sync-context.sh
                                  ├── --global  ► Skills/Workflows (~/.gemini/config/), Global Rules (~/.gemini/GEMINI.md)
                                  └── --target  ► Workspace Context (<workspace-root>/.agents/)
```

---

## Structure

```
agent-toolkit/
├── frameworks/           # Framework/language-specific agent context
│   ├── angular/
│   ├── nestjs/
│   └── strapi-v5/
│
├── infra/                 # Infrastructure & DevOps layer context
│   ├── cloudflare/
│   ├── docker/
│   ├── github-actions/    # Automated VPS deployment & CI/CD workflows
│   ├── postgres/
│   └── redis/
│
├── shared/                # Cross-cutting, topic-based agent context
│   ├── ai-agent-toolkit/ # Toolkit architecture & frontmatter standards
│   ├── code-quality/      # Clean code, TSDoc & type safety standards
│   ├── communication/     # Thanglish dual-language matching & mentorship rules
│   ├── generators/        # AI Skill, Rule, & Workflow authoring context (/generate-agent-suite)
│   ├── git/               # Git conventions, commit standards, Issue & PR automation
│   ├── google-suite/      # GA4 analytics, Search Console & AdSense monetization rules
│   ├── logging/           # Correlation ID tracing, JSON logs, secret masking
│   ├── package-management/# pnpm mandatory standards & Corepack rules
│   ├── problem-discovery/ # FOCUS 14-node discovery & evidence scoring rules
│   ├── security/          # Secret masking & OWASP rules
│   └── testing/           # Automated QA, unit/E2E test coverage standards
│
├── domains/               # Private project-specific domain layer (Git-ignored for Open-Source Safety)
│   ├── civicpath/         # CivicPath GIS domain skills & state machines
│   ├── docker-dev-infra/  # Dev Infra Compose microservices
│   ├── finance/           # Personal finance & double-entry math
│   ├── nidhiflow/         # Double-entry finance & loan amortization rules
│   └── seyalicraft/       # Main Portal ecosystem & branding rules
│
└── bin/                    # Scripts to sync context into Workspace or Global targets
    └── sync-context.sh
```

### skills/ vs rules/ vs workflows/

| Folder | Purpose | Example |
|---|---|---|
| `skills/` | "How to do X well" — reference patterns, best practices | `signal-state-management/SKILL.md` |
| `rules/` | Hard constraints the agent must always follow | "Never use `any` type", commit message format |
| `workflows/` | Step-by-step sequences for common multi-step tasks | "Add new feature module" → scaffold → route → test |

---

## Usage

`bin/sync-context.sh` is a **zero-hardcoding, dynamic universal sync engine**. You can pass any scope identifier (`-w, --workspace` or `-g, --global`) along with any path selector (from full categories down to single files).

```bash
./bin/sync-context.sh [scope] [options] [path-or-selector...]
```

### Scope Identifiers
* `-w, --workspace <path>` (or `-t, --target`): Syncs into project workspace (`<path>/.agents/`). Defaults to `./`.
* `-g, --global`: Syncs into user machine global environment (`~/.gemini/`).

### Non-Destructive In-Place Upsert Guarantee
* **Custom Context Preserved**: Any custom skills, rules, or workflows created manually in `.agents/` or `~/.gemini/` that are not part of the toolkit are **never touched or deleted**.
* **Same-Name Clean Replacement**: When an incoming toolkit item matches an existing file/folder name, it is cleanly replaced with the latest version (`🔄 Replacing existing...`).
* **Global `GEMINI.md` Tagged Envelope**: Global rules are refreshed strictly between `<!-- AGENT_TOOLKIT_START -->` and `<!-- AGENT_TOOLKIT_END -->`. Any personal guidelines outside this block are 100% preserved, with automatic safety backups created at `~/.gemini/GEMINI.md.bak`.

---

### Sync Scenarios & Examples

#### 1. Full Context Sync (`--all`)
Sync all categories (frameworks, infra, shared, domains) dynamically discovered across the toolkit:
```bash
# Sync entire toolkit to project workspace (.agents/)
./bin/sync-context.sh --all -w /path/to/my-project

# Sync entire toolkit globally (~/.gemini/)
./bin/sync-context.sh --all -g
```

#### 2. Category-Level Sync
Sync an entire top-level category folder by passing its name:
```bash
# Sync all shared engineering standards
./bin/sync-context.sh shared -w /path/to/my-project

# Sync all framework modules (Angular, NestJS, Strapi...)
./bin/sync-context.sh frameworks -w /path/to/my-project

# Sync all infra modules (Docker, Postgres, Redis...)
./bin/sync-context.sh infra -w /path/to/my-project
```

#### 3. Module-Level Sync
Sync a specific module sub-directory:
```bash
# Sync Angular framework context only
./bin/sync-context.sh frameworks/angular -w /path/to/my-app

# Sync Docker infra context only
./bin/sync-context.sh infra/docker -w /path/to/my-backend

# Sync NidhiFlow domain module only
./bin/sync-context.sh domains/nidhiflow -w /path/to/my-fintech-app
```

#### 4. Granular Single-Item Sync
Sync a single specific rule, skill, or workflow directly:
```bash
# Single Rule only:
./bin/sync-context.sh shared/code-quality/rules/no-any-type.md -w /path/to/my-project

# Single Skill directory only:
./bin/sync-context.sh frameworks/angular/skills/angular-signal-state-management -w /path/to/my-app

# Single Workflow only:
./bin/sync-context.sh shared/git/workflows/github-feature-workflow.md -w /path/to/my-project
```

#### 5. Global Scope Sync with Custom Selection
Selectively sync specific modules or rules globally into `~/.gemini/` (rules are automatically stripped of YAML frontmatter and appended to `~/.gemini/GEMINI.md`):
```bash
# Sync curated core rules and skills globally:
./bin/sync-context.sh shared/code-quality shared/communication -g

# Sync default universal shared context globally:
./bin/sync-context.sh -g
```

#### 6. Presets & Shorthands
Convenient bundles for common fullstack setups:
```bash
# Fullstack app bundle (Angular + NestJS + Docker + Postgres + Redis + Shared)
./bin/sync-context.sh --preset fullstack-app -w /path/to/fullstack-repo

# NestJS API bundle (NestJS + Postgres + Redis + Shared)
./bin/sync-context.sh --preset nestjs-api -w /path/to/my-backend
```

---

### Global Sync Architecture:
- **Skills**: Synced to `~/.gemini/antigravity/skills/` and `~/.gemini/config/skills/`.
- **Workflows**: Synced to `~/.gemini/config/workflows/` and `~/.gemini/config/global_workflows/`.
- **Global Rules (`~/.gemini/GEMINI.md`)**: Antigravity IDE natively discovers global rules exclusively from `~/.gemini/GEMINI.md` (tagged as `user_global`). Rules synced globally are automatically stripped of YAML frontmatter and cleanly appended into `~/.gemini/GEMINI.md`.
- **Token Budget Guard**: `bin/sync-context.sh` validates the total character count of `GEMINI.md` to prevent approaching Antigravity's 40% (8,000 tokens) global rule truncation limit.

> **Zero-Hardcoding Guarantee**: Any new category (e.g. `platforms/`, `tools/`) or sub-module created in the toolkit is dynamically discovered by `bin/sync-context.sh` without requiring script updates.

### 3. Generating & Updating Agent Context with AI

This repository includes built-in AI generator & consolidation workflows (supporting prompts in English, Tamil, or Thanglish):
- **Generate Agent Suite (Smart Evaluation)**: `shared/generators/workflows/generate-agent-suite.md` → Evaluates a scenario, inspects toolkit for existing files (upsert), and generates/updates the suite under `frameworks/`, `infra/`, or `shared/`.
- **Consolidate & Group Toolkit**: `shared/generators/workflows/consolidate-agent-toolkit.md` → Audits workspace, groups related skills/rules/workflows by topic, merges duplicates without data loss.
- **Generate Skill**: `shared/generators/workflows/generate-skill.md` → Creates or updates `[framework|infra|shared]/[topic]/skills/[skill-name]/SKILL.md`
- **Generate Rule**: `shared/generators/workflows/generate-rule.md` → Creates or updates `[framework|infra|shared]/[topic]/rules/[rule-name].md`
- **Generate Workflow**: `shared/generators/workflows/generate-workflow.md` → Creates or updates `[framework|infra|shared]/[topic]/workflows/[workflow-name].md`

#### ⚡ Shorthand Triggers & Commands

- `/generate-agent-suite` or `suite: <topic>` → Smart evaluation & suite generation inside `ai-agent-toolkit`.
- `/generate-skill` or `skill: <topic>` → Single Skill generation.
- `/generate-rule` or `rule: <topic>` → Single Rule generation.
- `/generate-workflow` or `workflow: <topic>` → Single Workflow generation.

---

## Conventions

- Directory is always `.agents/` inside consumer projects — not `.agent/` — to match what agent IDEs (e.g. Antigravity) auto-discover.
- Each `SKILL.md` should be self-contained: one skill, one file, clear YAML frontmatter (`name`, `description`).
- Cross-cutting knowledge (git conventions, code review checklists, documentation standards) goes in `shared/`, not duplicated per framework.
