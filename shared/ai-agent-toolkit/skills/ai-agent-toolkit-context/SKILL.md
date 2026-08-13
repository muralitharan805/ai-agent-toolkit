---
name: ai-agent-toolkit-context
description: Architecture, directory layout (frameworks, infra, shared, .agents), skill/rule/workflow authoring standards, synchronization utility (bin/sync-skills.sh), and GUI YAML frontmatter rules for Murali's ai-agent-toolkit repository (muralitharan805/ai-agent-toolkit).
---

# `ai-agent-toolkit` Product Architecture & Framework Specification

## Overview

**`ai-agent-toolkit`** ([`muralitharan805/ai-agent-toolkit`](https://github.com/muralitharan805/ai-agent-toolkit)) is Seyalicraft's central management repository for AI Agent capabilities, engineering rules, automated workflows, and domain context skills.

It provides a modular, deduplicated structure designed to sync context seamlessly into all Seyalicraft repositories (`seyalicraft-frontend`, `civicpath`, `nidhiflow`, `docker-dev-infra`) or globally into the user's system (`~/.gemini/`) via the `bin/sync-skills.sh` automation script.

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
                                  ├── --global  ► ~/.gemini/antigravity/skills/, ~/.gemini/config/
                                  └── --target  ► <workspace-root>/.agents/
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
├── shared/                    # Domain-level & cross-cutting shared context modules
│   ├── seyalicraft/           # Main Portal context & organizational rules
│   ├── civicpath/             # CivicPath 3-layer GIS & candidate domain skills
│   ├── nidhiflow/             # NidhiFlow double-entry accounting & finance skills
│   ├── docker-dev-infra/      # Docker dev infra compose template skills
│   ├── ai-agent-toolkit/      # Toolkit authoring & architectural skills
│   ├── code-quality/          # Clean code & maintainability standards
│   ├── generators/            # Skill/Rule/Workflow generator workflows (/generate-agent-suite)
│   ├── git/                   # Git conventional commits & PR automation
│   ├── logging/               # Structured logging & observability standards
│   └── security/              # Web security & auth guidelines
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

### 2. Workflow Frontmatter (`.md`)
```yaml
---
description: "Detailed description of the workflow process. Triggered by 'trigger1:', 'trigger2:', or '/slash-command'."
trigger: manual
---
```
*Note: Do NOT use non-standard keys like `aliases:` or custom metadata objects. Embed all trigger keywords directly inside the `description` string.*

### 3. Rule Frontmatter (`.md`)
```yaml
---
description: "Rule summary detailing constraints and conventions."
trigger: always_on
---
```

---

## Skill Synchronization Engine (`bin/sync-skills.sh`)

The toolkit provides a shell script to sync skills, rules, and workflows into workspace repositories or globally:

```bash
# 1. Sync ALL contexts globally to personal machine (~/.gemini/)
./bin/sync-skills.sh --global --all

# 2. Sync specific framework & infra globally
./bin/sync-skills.sh --global --framework nestjs --infra postgres,redis

# 3. Sync Angular framework + Docker infra + shared context into target workspace
./bin/sync-skills.sh --framework angular --infra docker --target /path/to/seyalicraft-frontend

# 4. Sync specific domain module into workspace
./bin/sync-skills.sh --domain nidhiflow --target /path/to/nidhiflow-backend
```

---

## Authoring Guidelines & Quality Mandates

1. **Deduplication First**: Before creating a new skill or rule, search existing directories (`frameworks/`, `infra/`, `shared/`). If a related file exists, update and merge requirements rather than creating duplicate files.
2. **Professional Rigor**: All instructions MUST be written in high-level, clear professional English with zero generic filler text.
3. **Executable Examples**: Code snippets inside skills MUST be copy-pasteable, type-safe TypeScript/SQL/HTML without placeholders.
