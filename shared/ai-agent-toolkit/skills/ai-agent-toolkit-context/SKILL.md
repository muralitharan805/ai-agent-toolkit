---
name: ai-agent-toolkit-context
description: Architecture, directory layout (frameworks, infra, shared, .agents), skill/rule/workflow authoring standards, synchronization utility (bin/sync-skills.sh), and GUI YAML frontmatter rules for Murali's ai-agent-toolkit repository (muralitharan805/ai-agent-toolkit).
---

# `ai-agent-toolkit` Product Architecture & Framework Specification

## Overview

**`ai-agent-toolkit`** ([`muralitharan805/ai-agent-toolkit`](https://github.com/muralitharan805/ai-agent-toolkit)) is my-company's central management repository for AI Agent capabilities, engineering rules, automated workflows, and domain context skills.

It provides a modular, deduplicated structure designed to sync context seamlessly into all my-company repositories (`my-company-frontend`, `gis-app`, `example-app`, `docker-dev-infra`) or globally into the user's system (`~/.gemini/`) via the `bin/sync-skills.sh` automation script.

---

## Two-Stage Context Generation & Deployment Paradigm

```
[User Request / Scenario]
         │
         ▼
[1. Generate inside Toolkit] ──► /generate-agent-suite creates/updates files under
                                  frameworks/, infra/, or shared/
         │
         ▼
[2. Sync & Deploy via Script] ──► bin/sync-skills.sh
                                  ├── --global  ► Skills/Workflows (~/.gemini/config/), Global Rules (~/.gemini/GEMINI.md)
                                  └── --target  ► Workspace Context (<workspace-root>/.agents/)
```

---

## Directory & Modular Layout

```
ai-agent-toolkit/
├── frameworks/                # Framework-specific engineering skills & standards
│   ├── angular/               # Angular 21 (Signals, Standalone, SSR, Material 3)
│   ├── nestjs/                # NestJS (Enterprise Scaffolding, Modules, Audit)
│   └── strapi-v5/             # Strapi CMS v5 Architecture
│
├── infra/                     # Infrastructure & DevOps skills & standards
│   ├── cloudflare/            # Cloudflare Pages / SSR Workers deployment
│   ├── docker/                # Docker containerization & Dockerfile best practices
│   ├── postgres/              # PostgreSQL schema, migrations & pgvector indexing
│   └── redis/                 # Redis caching strategies & TTL rules
│
├── shared/                    # Cross-cutting topic-based shared context modules
│   ├── ai-agent-toolkit/      # Toolkit authoring & architectural skills
│   ├── chrome-devtools/       # Browser automation & DOM auditing
│   ├── code-quality/          # Clean code & maintainability standards
│   ├── communication/         # Thanglish dual-language matching & junior mentorship rules
│   ├── generators/            # Skill/Rule/Workflow generator workflows (/generate-agent-suite)
│   ├── git/                   # Git conventional commits & PR automation
│   ├── google-suite/          # GA4 analytics, Search Console & AdSense monetization
│   ├── logging/               # Structured logging & observability standards
│   ├── package-management/    # pnpm package management standards
│   ├── problem-discovery/     # B2B FOCUS problem discovery & evidence scoring
│   ├── security/              # Web security & auth guidelines
│   └── testing/               # Automated testing & QA standards
│
├── domains/                   # Project domain layer (Private domain logic & rules)
│   ├── civicpath/             # CivicPath GIS domain skills & state machines
│   ├── docker-dev-infra/      # Dev Infra Compose microservices
│   ├── finance/               # Personal finance & double-entry math
│   ├── nidhiflow/             # Double-entry finance & loan amortization rules
│   └── seyalicraft/           # SeyaliCraft Main Portal ecosystem & branding rules
│
├── bin/                       # Automation CLI scripts
│   └── sync-skills.sh         # Syncs context to Workspace (.agents/) or Global (~/.gemini/)
│
└── .agents/                   # Local workspace rules & active workflows
```

---

## YAML Frontmatter GUI Compatibility Standards

All AI artifacts in the toolkit MUST conform to strict 100% GUI-compatible YAML frontmatter definitions:

### 1. Skill Frontmatter (`SKILL.md`)
```yaml
---
name: [kebab-case-identifier]
description: [Third-person routing statement describing domain capabilities, triggers, and technologies]
---
```
*Note: Keep main `SKILL.md` under 500 lines; place bulky manuals and code under `examples/`, `scripts/`, or `references/`.*

### 2. Workflow Frontmatter (`.md`)
```yaml
---
description: "Detailed description of the workflow process. Triggered by 'trigger1:', 'trigger2:', or '/slash-command'."
trigger: manual
---
```
*Note: Do NOT use non-standard keys like `aliases:`. Embed all trigger keywords directly inside the `description` string. Files must not exceed 12,000 characters.*

### 3. Rule Frontmatter (`.md`)
```yaml
---
description: "Rule summary detailing constraints and conventions."
trigger: [model_decision | glob | always_on | manual]
globs: ["src/**/*.ts"] # Only include when trigger is glob
---
```
*Note: Rules are strictly limited to 12,000 characters per file (hard Antigravity IDE limit).*

---

## Skill Synchronization Engine (`bin/sync-skills.sh`)

The toolkit provides a shell script to sync skills, rules, and workflows into workspace repositories or globally:

### Scope Execution Architecture:
- **Workspace Level (`--target <path>`)**: Copies skills, individual rules (`.agents/rules/*.md`), and workflows directly into `<target>/.agents/`.
- **Global Level (`--global`)**:
  - Skills are synced to `~/.gemini/antigravity/skills/` and `~/.gemini/config/skills/`.
  - Workflows are synced to `~/.gemini/config/workflows/` and `~/.gemini/config/global_workflows/`.
  - Global Rules are exclusively synced into `~/.gemini/GEMINI.md` (tagged as `user_global` in Antigravity IDE). Matching directories are configured via `GEMINI_RULE_DIRS` in `bin/sync-skills.sh`, and their YAML frontmatter headers are automatically stripped.
  - Character limit validation ensures `GEMINI.md` stays safely within the recommended token budget (< 40% IDE ceiling).

```bash
# 1. Sync Universal Shared rules/skills globally
./bin/sync-skills.sh --global --shared

# 2. Sync specific framework & infra globally
./bin/sync-skills.sh --global --framework nestjs --infra postgres,redis

# 3. Sync Angular framework + Docker infra + shared context into target workspace
./bin/sync-skills.sh --framework angular --infra docker --target /path/to/my-company-frontend

# 4. Sync specific domain module into workspace
./bin/sync-skills.sh --domain example-app --target /path/to/example-app-backend
```

---

## Authoring Guidelines & Quality Mandates

1. **Deduplication First**: Before creating a new skill or rule, search existing directories (`frameworks/`, `infra/`, `shared/`). If a related file exists, update and merge requirements rather than creating duplicate files.
2. **Professional Rigor**: All instructions MUST be written in high-level, clear professional English with zero generic filler text.
3. **Executable Examples**: Code snippets inside skills MUST be copy-pasteable, type-safe TypeScript/SQL/HTML without placeholders.
