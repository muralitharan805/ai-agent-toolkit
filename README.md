# agent-toolkit

Central repository of reusable **skills**, **rules**, and **workflows** for AI coding agents (e.g. Google Antigravity IDE). Instead of writing agent context from scratch in every project, this toolkit lets you scaffold or sync a consistent `.agents/` directory into any repo — Angular, Node, NestJS, Strapi, Docker, or otherwise.

## Why this exists

Every project's `.agents/` folder tends to be written once and then drift — different naming, inconsistent structure, no reuse across projects. This repo centralizes that knowledge so:

- New projects get a battle-tested `.agents/` setup on day one.
- Existing projects can pull in updates without hand-copying files.
- Framework-specific knowledge (Angular, NestJS, Strapi, Docker, Postgres, Redis...) lives in one place instead of being duplicated per repo.

## Google Antigravity IDE Compatibility ⚡

This repository is 100% natively compatible with **Google Antigravity IDE**:

- **Native `.agents/` Discovery**: Target directories map directly to `.agents/skills/`, `.agents/rules/`, and `.agents/workflows/` for automatic IDE indexing.
- **Strict GUI-Compatible Frontmatter**: Follows exact YAML frontmatter schemas (`name`, `description`, `trigger: always_on`, `trigger: glob`, `trigger: manual`) to render cleanly in Antigravity's UI.
- **Slash Commands & Shorthand Triggers**: Designed to respond instantly to native slash commands (`/generate-agent-suite`, `/consolidate-agent-toolkit`) and prompt prefixes (`suite:`, `consolidate:`).
- **Direct Copy Sync**: Uses `bin/sync-skills.sh` to copy physical files directly into `.agents/` without symbolic links.

## Structure

```
agent-toolkit/
├── frameworks/           # Framework/language-specific agent context
│   ├── angular/
│   │   ├── skills/
│   │   ├── rules/
│   │   └── workflows/
│   ├── nestjs/
│   └── strapi-v5/
│
├── infra/                 # Infrastructure & DevOps layer context
│   ├── docker/
│   │   ├── skills/
│   │   ├── rules/
│   │   └── workflows/
│   ├── postgres/
│   │   ├── skills/
│   │   └── rules/
│   └── redis/
│       ├── skills/
│       ├── rules/
│       └── workflows/
│
├── shared/                # Cross-cutting, topic-based agent context
│   ├── finance/           # Double-entry personal accounting, EMI, pgvector
│   │   ├── skills/
│   │   ├── rules/
│   │   └── workflows/
│   ├── generators/       # AI Skill, Rule, & Workflow authoring context
│   │   ├── skills/
│   │   ├── rules/
│   │   └── workflows/
│   ├── git/              # Git conventions, commit standards, Issue & PR automation
│   │   ├── skills/
│   │   ├── rules/
│   │   └── workflows/
│   ├── security/         # Secret masking & OWASP rules
│   │   └── rules/
│   ├── logging/           # Correlation ID tracing, JSON logs, secret masking
│   │   ├── skills/
│   │   └── rules/
│   ├── seyalicraft/       # Seyalicraft Ecosystem, product suites (seyalicraft.com, NidhiFlow, CivicPath) & repo map
│   │   ├── skills/
│   │   ├── rules/
│   │   └── workflows/
│   ├── civicpath/         # CivicPath product domain: GIS GeoJSON, civic issue state machine, PII protection
│   │   ├── skills/
│   │   ├── rules/
│   │   └── workflows/
│   ├── docker-dev-infra/  # Dev Infra project domain: Postgres pgvector, Redis, modular Compose microservices
│   │   ├── skills/
│   │   ├── rules/
│   │   └── workflows/
│   └── code-quality/     # Clean code, JSDoc, & strict type safety standards
│       ├── skills/
│       └── rules/
│
└── bin/                    # Scripts to scaffold/sync skills into real projects
    ├── scaffold-angular.sh
    └── sync-skills.sh
```

### skills/ vs rules/ vs workflows/

| Folder | Purpose | Example |
|---|---|---|
| `skills/` | "How to do X well" — reference patterns, best practices | `signal-state-management/SKILL.md` |
| `rules/` | Hard constraints the agent must always follow | "Never use `any` type", commit message format |
| `workflows/` | Step-by-step sequences for common multi-step tasks | "Add new feature module" → scaffold → route → test → barrel export |

## Usage

### Sync skills into an existing project (Direct Physical Copy Sync)

Run `bin/sync-skills.sh` from the toolkit repo to automatically copy framework, shared, and infra skills/rules/workflows directly as physical files into a target project's `.agents/` directory:

```bash
# Sync Angular framework + Shared rules/skills + Docker/Postgres infra tools into target project
./bin/sync-skills.sh --framework angular --infra docker,postgres --target /path/to/my-angular-app

# Sync Shared rules/skills only into any repository (framework optional)
./bin/sync-skills.sh --shared --target /path/to/my-project
```

### 3. Sync updates into a project that already has copied

this repo is continuosly updated with new skills, rules, workflows. Pull the latest framework + shared skills from the toolkit and overwrites the local copies.

### 4. Generating & Consolidating Agent Context with AI

This repository includes built-in AI generator & consolidation workflows (supporting prompts in English, Tamil, or Thanglish):
- **Consolidate & Group Toolkit**: `shared/generators/workflows/consolidate-agent-toolkit.md` → Audits workspace, groups related skills/rules/workflows by topic, merges duplicates without data loss, and auto-syncs README.
- **Generate Agent Suite (Smart Evaluation)**: `shared/generators/workflows/generate-agent-suite.md` → Evaluates a scenario, inspects workspace for existing files (upsert), and generates/updates the suite.
- **Generate Skill**: `shared/generators/workflows/generate-skill.md` → Creates or updates `[framework|infra|shared]/[topic]/skills/[skill-name]/SKILL.md`
- **Generate Rule**: `shared/generators/workflows/generate-rule.md` → Creates or updates `[framework|infra|shared]/[topic]/rules/[rule-name].md`
- **Generate Workflow**: `shared/generators/workflows/generate-workflow.md` → Creates or updates `[framework|infra|shared]/[topic]/workflows/[workflow-name].md`

#### ⚡ Shorthand Triggers (Fast Prompting)

Instead of typing out full requests, you can use these shorthand prefixes directly in your chat:
- `consolidate:` or `grouping:` → Triggers full workspace audit, semantic grouping, merging & cleanup.
- `suite: <topic>` (e.g., `suite: Angular Signals Form`) → Triggers smart evaluation & suite generation.
- `context: <topic>` (e.g., `context: NestJS JWT Auth`) → Triggers smart evaluation & suite generation.

- `/deploy-angular-cloudflare` — Deploy Angular SSR to Cloudflare Pages/Workers
- `/deploy-angular-spa-cloudflare` — Deploy Angular SPA (CSR) with _redirects fallback to Cloudflare Pages

- `/generate-agent-suite` — Smart evaluation & suite generation
- `/generate-skill` — Single Skill generation
- `/generate-rule` — Single Rule generation
- `/generate-workflow` — Single Workflow generation


## Adding a new framework

1. Create `frameworks/<framework-name>/{skills,rules,workflows}/`.
2. Add a `SKILL.md` per topic (frontmatter + content).
3. Add a corresponding `scaffold-<framework>.sh` in `bin/` if the framework needs its own project-init command.

## Conventions

- Directory is always `.agents/` (singular) inside consumer projects — not `.agentss/` — to match what agent IDEs (e.g. Antigravity) auto-discover.
- Each `SKILL.md` should be self-contained: one skill, one file, clear frontmatter (name, description, trigger conditions).
- Cross-cutting knowledge (git conventions, code review checklists, documentation standards) goes in `shared/`, not duplicated per framework.

## Roadmap / ideas

- [ ] Add `frameworks/nextjs/`
- [ ] Add `frameworks/java-spring-boot/`
- [ ] `bin/scaffold-nestjs.sh`
- [ ] CI check that validates every `SKILL.md` has required frontmatter
