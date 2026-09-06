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
├── shared/                 # Cross-Cutting Universal Engineering Standards
│   ├── ai-agent-toolkit/   # Repository architecture, authoring standards, and sync context (THIS SKILL)
│   ├── code-quality/       # Clean Code, TSDoc comments, and zero-any type enforcement
│   ├── communication/      # Thanglish language matching & senior mentorship persona
│   ├── generators/         # Built-in AI generators, evaluators, and automated Python validators
│   ├── git/                # Conventional Commits, GitHub Issue & PR automation
│   ├── google-suite/       # GA4 Analytics, SEO sitemaps, and AdSense monetization integration
│   ├── logging/            # Structured JSON logs, correlation ID propagation & secret masking
│   ├── package-management/ # Strict pnpm package manager and Corepack enforcement
│   └── security/           # OWASP Top 10 mitigation, secret scanning & pentest audits
│
├── domains/                # Private Project-Specific Domain Context (Git-Ignored)
│   ├── civicpath/          # CivicPath GIS boundary detection & map signals
│   ├── docker-dev-infra/   # Dev Infra Compose microservices
│   ├── finance/            # Personal finance & double-entry accounting math
│   └── seyalicraft/        # SeyaliCraft portal ecosystem & branding rules
│
└── bin/                    # Automation Scripts
    └── sync-context.sh     # Zero-hardcoding dynamic synchronization engine
```

---

## 3. Dynamic Sync Engine Protocol (`bin/sync-context.sh`)

The sync script is a zero-hardcoding bash engine. It dynamically resolves paths without hardcoded module lists and performs safe, physical file replacement (no symlinks).

### Key Execution Flags:
- `-w, --workspace <path>`: Syncs context into `<path>/.agents/` (defaults to `./`).
- `-g, --global`: Syncs context globally into `~/.gemini/`.
- `--all`: Syncs all categories (`frameworks`, `infra`, `shared`, `domains`).
- `--preset <name>`: Syncs predefined bundles (e.g., `fullstack-app`, `nestjs-api`).

### Synchronization Rules:
1. **In-Place Upsert**: Custom files in consumer `.agents/` are never deleted. Only files matching incoming toolkit items are cleanly refreshed.
2. **Tagged Envelope in `GEMINI.md`**: Global rules synced via `-g` are stripped of frontmatter and merged exclusively between `<!-- AGENT_TOOLKIT_START -->` and `<!-- AGENT_TOOLKIT_END -->` inside `~/.gemini/GEMINI.md`. Automatic backups are created at `~/.gemini/GEMINI.md.bak`.
3. **Token Budget Ceiling**: The script actively checks character counts to avoid exceeding Antigravity's 12,000-character limit.
