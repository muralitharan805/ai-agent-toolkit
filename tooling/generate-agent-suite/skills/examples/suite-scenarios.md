# Real-World Suite Scenarios & Architectural Blueprints

## Scenario 1: Enterprise Caching (Full Suite: Skill + Rule)

### User Prompt (Thanglish):
> "NestJS app-la Redis cache module add pannanum bro. Automatic cache hits/misses log aaganum, mutation actions (POST/PUT/DELETE) aana cache auto-invalidate aaganum."

### Architect Evaluation:
```text
=== AGENT SUITE ANALYSIS & DISCOVERY ===
Scenario: NestJS Redis Caching with logging interceptor and mutation invalidation.
Target Topic Directory: infra/redis
Action Plan:
  - Skill (Domain Knowledge): CREATE `infra/redis/skills/caching-strategies/` (Interceptors, @UseCache decorator, TTL configuration).
  - Rule (Antigravity Rule): CREATE `infra/redis/rules/cache-invariants.md` (Mandatory invalidation on mutations, prohibition of caching sensitive /auth endpoints).
  - Workflow: DEPRECATED (Not applicable).
Verification Command: python3 shared/generators/skills/generate-agent-suite/scripts/verify_suite.py infra/redis/
========================================
```

---

## Scenario 2: Cloud Deployment Pipeline (Procedural Skill Only)

### User Prompt (English):
> "Create an automated workflow to deploy our Angular 21 CSR application to Cloudflare Pages using Wrangler CLI."

### Architect Evaluation:
```text
=== AGENT SUITE ANALYSIS & DISCOVERY ===
Scenario: Automated deployment pipeline for Angular CSR to Cloudflare Pages.
Target Topic Directory: frameworks/angular
Action Plan:
  - Skill (Procedural Execution): CREATE `frameworks/angular/skills/cloudflare-angular-spa-deployment/` (Checklist, Wrangler preview, _redirects verification).
  - Rule: SKIPPED (Sequential deployment runbook; no global workspace constraints or glob triggers required).
  - Workflow: DEPRECATED (Routed into Procedural Skill).
Verification Command: python3 shared/generators/skills/generate-skill/scripts/validate_skill.py frameworks/angular/skills/cloudflare-angular-spa-deployment/
========================================
```

---

## Scenario 3: Security Prohibition (Rule Only)

### User Prompt (Thanglish):
> "Database password, JWT secret keys, API credentials code la hardcode panna koodadhu, kandipa .env la irundhu dhaan load aaganum."

### Architect Evaluation:
```text
=== AGENT SUITE ANALYSIS & DISCOVERY ===
Scenario: Zero hardcoded secrets and mandatory environment variable loading.
Target Topic Directory: shared/security
Action Plan:
  - Skill: SKIPPED (No multi-step procedural workflow or extensive API reference needed).
  - Rule: CREATE `shared/security/rules/zero-hardcoded-secrets.md` (trigger: always_on or glob, strict prohibition with Correct vs Forbidden examples).
  - Workflow: DEPRECATED (Not applicable).
Verification Command: python3 shared/generators/skills/generate-rule/scripts/validate_rule.py shared/security/rules/zero-hardcoded-secrets.md
========================================
```
