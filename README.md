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
- **Direct Physical Sync Utility**: Uses `bin/sync-skills.sh` to copy physical files directly into `.agents/` or `~/.gemini/` without symbolic link breaks.

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
[2. Sync to Target Scope]   ──► bin/sync-skills.sh
                                  ├── --global  ► ~/.gemini/antigravity/skills/, ~/.gemini/config/
                                  └── --target  ► <workspace-root>/.agents/
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
│   ├── docker/
│   ├── postgres/
│   ├── redis/
│   └── cloudflare/
│
├── shared/                # Cross-cutting, topic-based agent context
│   ├── ai-agent-toolkit/ # Toolkit architecture & frontmatter standards
│   ├── code-quality/      # Clean code, TSDoc & type safety standards
│   ├── generators/        # AI Skill, Rule, & Workflow authoring context (/generate-agent-suite)
│   ├── git/               # Git conventions, commit standards, Issue & PR automation
│   ├── google-suite/      # GA4 analytics, Search Console & AdSense monetization rules
│   ├── logging/           # Correlation ID tracing, JSON logs, secret masking
│   ├── package-management/# pnpm mandatory standards & Corepack rules
│   └── security/          # Secret masking & OWASP rules
│
├── domains/               # Private project-specific domain layer (Git-ignored for Open-Source Safety)
│   ├── nidhiflow/         # Double-entry finance & loan amortization rules
│   ├── seyalicraft/       # Main Portal ecosystem & branding rules
│   ├── civicpath/         # CivicPath GIS domain skills & state machines
│   ├── finance/           # Personal finance & double-entry math
│   └── docker-dev-infra/  # Dev Infra Compose microservices
│
└── bin/                    # Scripts to sync context into Workspace or Global targets
    └── sync-skills.sh
```

### skills/ vs rules/ vs workflows/

| Folder | Purpose | Example |
|---|---|---|
| `skills/` | "How to do X well" — reference patterns, best practices | `signal-state-management/SKILL.md` |
| `rules/` | Hard constraints the agent must always follow | "Never use `any` type", commit message format |
| `workflows/` | Step-by-step sequences for common multi-step tasks | "Add new feature module" → scaffold → route → test |

---

## Usage

### 1. Syncing Context to Workspace Level (`.agents/`)

Run `bin/sync-skills.sh` from the toolkit repo to automatically copy framework, shared, and infra skills/rules/workflows directly into a target project's `.agents/` directory:

```bash
# Sync Angular framework + Shared rules/skills + Docker/Postgres infra tools into target project
./bin/sync-skills.sh --framework angular --infra docker,postgres --target /path/to/my-angular-app

# Sync Shared rules/skills only into any repository
./bin/sync-skills.sh --shared --target /path/to/my-project
```

### 2. Syncing Context to Global Level (`~/.gemini/`)

Sync all or selected framework/infra skills into your personal system-wide environment:

```bash
# Sync ALL toolkit frameworks, infra, and shared contexts globally
./bin/sync-skills.sh --global --all

# Sync specific framework + infra globally
./bin/sync-skills.sh --global --framework nestjs --infra postgres,redis
```

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
