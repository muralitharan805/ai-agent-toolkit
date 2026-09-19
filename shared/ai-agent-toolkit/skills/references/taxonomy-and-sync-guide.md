# Toolkit Taxonomy & Dynamic Synchronization Reference Guide

## 1. Overview
The `ai-agent-toolkit` repository (`muralitharan805/ai-agent-toolkit`) is the single source of truth for agent customization across all engineering projects. It is organized into distinct categories designed for dynamic discovery and physical synchronization.

---

## 2. Directory Taxonomy & Organization

```text
ai-agent-toolkit/
├── frameworks/             # Language & Framework-Specific Context
│   ├── angular/            # Modern Angular 19+ (Signals, Standalone, Zoneless, M3, Reactive Forms)
│   ├── nestjs/             # NestJS Clean Architecture, DTOs, Functional Guards, Microservices
│   └── strapi-v5/          # Strapi Headless CMS schemas & dynamic binding rules
│
├── infra/                  # Cloud, Infrastructure & DevOps Context
│   ├── cloudflare/         # Cloudflare Pages (CSR) & Workers (SSR) edge runtime deployments
│   ├── docker/             # Multi-stage Dockerfiles, Compose v2 orchestrations, BuildKit, hardening
│   ├── github-actions/     # Automated VPS SSH deployment pipelines & CI/CD workflows
│   ├── postgres/           # PostgreSQL indexing, migrations, pgvector, and query optimization
│   └── redis/              # Distributed caching modules and cache invalidation strategies
│
├── shared/                 # Cross-Cutting Consumer Engineering Standards
│   ├── ai-agent-toolkit/   # Repository architecture, authoring standards, and sync context (THIS SKILL)
│   ├── code-quality/       # Clean Code, TSDoc comments, and zero-any type enforcement
│   ├── communication/      # Thanglish language matching & senior mentorship persona
│   ├── git/                # Conventional Commits, GitHub Issue & PR automation
│   ├── google-suite/       # GA4 Analytics, SEO sitemaps, and AdSense monetization integration
│   ├── logging/            # Structured JSON logs, correlation ID propagation & secret masking
│   ├── package-management/ # Strict pnpm package manager and Corepack enforcement
│   └── security/           # OWASP Top 10 mitigation, secret scanning & pentest audits
│
├── domains/                # Domain / project-specific context
│   ├── civicpath/          # CivicPath GIS boundary detection & map signals
│   ├── docker-dev-infra/   # Dev Infra Compose microservices
│   ├── finance/            # Personal finance & double-entry accounting math
│   └── seyalicraft/        # SeyaliCraft portal ecosystem & branding rules
│
├── tools/                  # Internal toolkit tools; dynamic family root
│   └── generators/         # Generator/evaluator/validator tool family
│       ├── generate-skill/
│       ├── generate-rule/
│       ├── generate-agent-suite/
│       └── ...
│
└── bin/                    # Runtime automation scripts
    └── context.sh          # Tool-aware sync and cleanup engine
```

---


---

## 3. Tools Taxonomy

`tools/` is separate from consumer context. It stores capabilities used to create or maintain the toolkit itself.

```text
tools/<family>/<tool-name>/
├── skills/
│   ├── SKILL.md
│   ├── references/
│   ├── scripts/
│   ├── assets/
│   └── evals/
└── rules/                  # optional
```

`generators/` is the current first family. Future families can be introduced without changing the resolver. New tools must be discovered by recursive directory structure, not by a hardcoded tool-name registry.

Placement examples:
- Angular application guidance → `frameworks/angular/...`
- reusable security standard → `shared/security-...`
- new context generator → `tools/generators/<name>/`
- future validator family → `tools/validators/<name>/`

`tools/` is never part of default consumer `--all` sync. It must be selected explicitly.

---

## 4. Dynamic Sync Engine Protocol (`bin/context.sh`)

The sync script is a zero-hardcoding bash engine. It dynamically resolves paths without hardcoded module lists and performs safe, physical file replacement (no symlinks).

### Key Execution Flags:
- `-w, --workspace`: Select workspace mode. Use `--target <path>` for the project root.
- `-g, --global`: Select global mode. Global support currently targets Antigravity only.
- `--all`: Syncs consumer roots (`frameworks`, `infra`, `shared`, `domains`) and excludes `tools/`.
- `--preset <name>`: Syncs predefined bundles (e.g., `fullstack-app`, `nestjs-api`).

### Synchronization Rules:
1. **Manifest Ownership**: Unmanaged destination content is preserved. Toolkit-managed content is tracked by source, target, kind, scope, tool, and installed hash.
2. **Tagged Envelope in `GEMINI.md`**: Global rules synced via `-g` are stripped of frontmatter and merged exclusively between `<!-- AGENT_TOOLKIT_START -->` and `<!-- AGENT_TOOLKIT_END -->` inside `~/.gemini/GEMINI.md`. Automatic backups are created at `~/.gemini/GEMINI.md.bak`.
3. **Token Budget Ceiling**: The script actively checks character counts to avoid exceeding Antigravity's 12,000-character limit.
