---
name: environment-configuration
description: "Enforces fail-fast startup configuration validation, strongly-typed central config services, secrets hygiene, and .env.example parity. Triggered by 'config:', 'env-config:', or '/environment-configuration'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-09"
---

# Central Environment Configuration & Secrets Management Skill

## Overview

This skill establishes the production engineering protocol for **fail-fast application configuration**, **secrets hygiene**, and **centralized config management** across language-agnostic backend systems. It eliminates runtime crashes caused by missing environment variables, prohibits scattering raw `process.env` / `os.environ` access across business logic, mandates strongly-typed configuration services, enforces zero hardcoded operational settings, and guarantees 1:1 parity with junior-friendly documented `.env.example` templates.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           5-Phase Execution Pipeline                           │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Schema Definition]      ──► Declare Zod / Pydantic / Viper schema
               │
  [Phase 2: Typed Config Service]   ──► Wrap validated values in central service
               │
  [Phase 3: Fail-Fast Boot Gate]    ──► Validate on startup; exit(1) if invalid
               │
  [Phase 4: Secrets Hygiene]        ──► Verify .gitignore & mask sensitive keys
               │
  [Phase 5: Automated Audit]        ──► Run audit_environment_config.py --strict
```

---

## 5-Phase Execution Guide

### Phase 1: Environment Variable Schema Definition
1. **Declare Type-Safe Schema**:
   Define an explicit validation schema using your language's standard schema engine (Zod for Node.js, Pydantic for Python, CleanEnv for Go):
   - Coerce numeric and boolean types (e.g. `z.coerce.number()`).
   - Validate URL formats and minimum string lengths (e.g. `min(32)` for JWT secrets).
   - Use strict enumerations for environment stages (`development`, `test`, `staging`, `production`).

### Phase 2: Centralized Strongly-Typed Config Service
1. **Encapsulate Behind Injected Service**:
   - Never access raw environment arrays (`process.env.DB_URL`) directly in controllers or services.
   - Inject a frozen, immutable `ConfigService` or configuration DTO:
   ```typescript
   export class UserService {
     constructor(private readonly config: AppConfig) {}

     public getWebhookUrl(): string {
       return this.config.PAYMENT_WEBHOOK_URL;
     }
   }
   ```

### Phase 3: Bootstrap Validation Gate & Fail-Fast Trigger
1. **Execute Prior to Network Binding**:
   - Load and validate configuration as the very first step in the `main` application entry point.
   - If validation fails, log structured errors identifying the invalid fields and terminate immediately with `process.exit(1)`.
   - Never defer validation until an endpoint or worker is invoked.

### Phase 4: Secrets Hygiene & Gitignore Verification
1. **Zero `.env` in Version Control**:
   - Ensure `.gitignore` contains rules for `.env`, `.env.*`, and `*.pem`.
   - In production, inject secrets via orchestrator environment variables (Kubernetes Secrets, AWS Secrets Manager, Vault) instead of disk-mounted `.env` files.
2. **Log Sanitization**:
   - Mask sensitive values (`password`, `secret`, `token`, `authorization`) when emitting startup configurations or debugging logs.

### Phase 5: Automated Config & Parity Audit
1. **Run Automated Audit CLI**:
   - Execute the bundled configuration auditor to verify `.env.example` parity and detect scattered raw env access:
   ```bash
   python3 scripts/audit_environment_config.py . --strict
   ```
2. **Ensure Junior-Friendly Documentation**:
   - Every variable in `.env.example` must have descriptive header comments stating purpose, format, and local source.

---

## Working Checklist

- [ ] **Startup Schema Validation**: All required environment variables validated against schema on boot.
- [ ] **Fail-Fast Crash**: Application halts with exit code 1 if any required configuration is missing or malformed.
- [ ] **Centralized Service**: Zero raw `process.env` or `os.environ` references in business logic or controllers.
- [ ] **Zero Hardcoding**: Ports, URLs, timeouts, retry limits, and cache TTLs driven exclusively by configuration.
- [ ] **Gitignore Compliance**: `.env` and local credential files strictly excluded from Git tracking.
- [ ] **Production Cloud Secrets**: Production environments use runtime secret injection, not static `.env` files.
- [ ] **.env.example Parity**: Every required variable documented in `.env.example` with junior-friendly setup notes.

---

## Authoritative References & Bundled Assets

- **Fail-Fast Architecture Guide**: [references/fail-fast-config-architecture.md](references/fail-fast-config-architecture.md)
- **Configuration Audit CLI Tool**: [scripts/audit_environment_config.py](scripts/audit_environment_config.py)
- **Documented .env.example Template**: [assets/env-example-template.env](assets/env-example-template.env)
- **Empirical Quality Evals**: [evals/evals.json](evals/evals.json)

---

## Gotchas (Legacy vs. Modern Configuration)

| Legacy Antipattern | Modern Configuration Standard | Impact & Rationale |
| :--- | :--- | :--- |
| **Unvalidated Boot** (Accessing `process.env` during request execution) | **Fail-Fast Schema Gate** (Validate 100% on application startup) | Prevents delayed midnight production outages when rare webhooks invoke missing secrets. |
| **Scattered `process.env` Access** (Scattered across 50 files) | **Centralized Injected ConfigService** | Eliminates typo-induced bugs (`process.env.DB_PASSWROD`); enables trivial unit testing. |
| **Inline Magic Numbers** (`timeout: 5000`, `port: 8080`) | **Config-Driven Operations** | Allows changing timeouts and limits across environments without code modifications. |
| **Committing `.env` to Git** | **`.env.example` + Secrets Manager** | Eliminates security breaches from credential scrapers monitoring source repositories. |
| **Undocumented `.env.example`** (Raw list without comments) | **Junior-Friendly 3-Point Comments** | Reduces developer onboarding time from days to minutes with zero ambiguity. |
| **Plaintext Secret Logging** (`logger.info(config)`) | **Recursive Secret Masking** | Prevents credentials and API keys from leaking into log monitoring dashboards (Datadog/ELK). |
