---
name: cicd-and-build-infrastructure
description: "Enforces 10-step mandatory CI pipeline gates, multi-stage Docker builds with non-root runtime users, frozen lockfile installations, Trivy image vulnerability scanning, and immutable git-SHA tagging. Triggered by 'cicd:', 'dockerfile:', 'trivy:', 'build-pipeline:', or '/cicd-and-build-infrastructure'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# CI/CD & Build Infrastructure Skill

## Overview

This skill establishes the production engineering standards for **10-Step CI Pull Request Quality Gates**, **Multi-Stage Production Dockerfiles**, **Non-Root Runtime Hardening (`USER appuser`)**, **Trivy Container Vulnerability Scanning**, and **Immutable Git-SHA Image Tagging**. It prevents unverified or vulnerable artifacts from reaching staging and production environments, minimizes container attack surfaces, and guarantees deterministic, reproducible builds.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                    10-Step Mandatory CI Pull Request Pipeline                  │
│                                                                                │
│   [Phase 1: Static Analysis Gates] ──► Lint, Format & Strict Typecheck         │
│                 │                                                              │
│   [Phase 2: Test & Coverage Gates] ──► Unit (80%/75%) & Testcontainers        │
│                 │                                                              │
│   [Phase 3: Security & Secret Scan]──► SAST dependency audit & GitLeaks diff   │
│                 │                                                              │
│   [Phase 4: Multi-Stage Build]     ──► Frozen lockfile & non-root user image   │
│                 │                                                              │
│   [Phase 5: Vulnerability & Push]  ──► Trivy container scan & Git SHA tag push │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Phase Execution Guide

### Phase 1: Static Analysis & Code Quality Gates
1. **Enforce Static Verification in CI**:
   - Execute `pnpm run lint` and `pnpm run format:check` to reject style inconsistencies.
   - Run strict static type checking via `pnpm run typecheck` (`tsc --noEmit`).
2. **Deterministic Installs**:
   - Always run `pnpm install --frozen-lockfile` to prevent unexpected dependency mutations.

### Phase 2: Testing Verification & Coverage Thresholds
1. **Execute Unit Tests**:
   - Run `pnpm run test:cov` enforcing $\ge 80\%$ line and $\ge 75\%$ branch coverage.
2. **Execute Containerized Integration Tests**:
   - Launch ephemeral PostgreSQL and Redis instances via Testcontainers to validate real database contracts.

### Phase 3: Security Audits & Secret Leak Prevention
1. **SAST Dependency Vulnerability Scanning**:
   - Execute `pnpm audit --audit-level high` to fail the build if high or critical CVEs exist in dependencies.
2. **Pre-Merge Secret Scanning**:
   - Execute GitLeaks against the pull request commit range to block any committed API keys or passwords.

### Phase 4: Multi-Stage Container Build & Non-Root Hardening
1. **Multi-Stage Dockerfile**:
   - Utilize a builder stage for compilation and prune devDependencies using `pnpm prune --prod`.
   - Copy only compiled `dist/` and production `node_modules/` into a minimal Alpine/Distroless base image.
2. **Non-Root Runtime Hardening**:
   - Create an explicit system user `appuser` (UID $\ge 1000$).
   - Declare `USER appuser` to ensure the container never runs as root (UID 0).

### Phase 5: Container Vulnerability Scanning & Immutable Promotion
1. **Scan Container with Trivy**:
   - Scan the compiled Docker image using Trivy (`--exit-code 1 --severity CRITICAL,HIGH`).
2. **Immutable Versioning**:
   - Tag the final image using the short Git commit SHA: `myapp:${{ github.sha }}`.
   - Prohibit the mutable `latest` tag in production deployment manifests.
   - Push to container registry strictly on merge to the default branch (`main`).

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [references/cicd-pipelines-and-docker-builds.md](references/cicd-pipelines-and-docker-builds.md) for detailed multi-stage Dockerfile patterns, Trivy configuration, and immutable tagging runbooks.
- **Production Asset**: Inspect [assets/cicd-build-infrastructure-bootstrap.template.ts](assets/cicd-build-infrastructure-bootstrap.template.ts) for multi-stage Dockerfile, .dockerignore, and 10-step GitHub Actions workflows.
- **CLI Auditor Tool**: Run [scripts/audit_cicd_infrastructure.py](scripts/audit_cicd_infrastructure.py) to audit multi-stage builds, non-root users, frozen lockfile usage, and Trivy scans.
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## Gotchas & Pitfalls

| Category | ❌ Anti-Pattern (Legacy / Brittle) | ✅ Production-Grade (Modern Standard) | Architectural Risk |
| :--- | :--- | :--- | :--- |
| **Container User** | Running container as default `root` (UID 0) | Explicit system **`USER appuser` (UID 1001)** | Container breakout grants attacker root privileges on host node. |
| **Build Architecture** | Single-stage Dockerfile packaging build tools | **Multi-stage build** copying only `dist/` | 1GB+ image sizes and compilers exposed in runtime environment. |
| **Image Tagging** | Deploying images tagged as `:latest` | Tagging with **immutable `${{ github.sha }}`** | Unpredictable replica digests, non-reproducible rollbacks. |
| **Dependency Install** | Running `pnpm install` without flags in CI | **`pnpm install --frozen-lockfile`** | Silent lockfile mutation and non-deterministic production builds. |
| **Vulnerability Gate** | Pushing container to registry without image scan | **Trivy vulnerability scan** blocking on CRITICAL/HIGH | Known remote code execution CVEs deployed to production clusters. |
| **Artifact Pruning** | Leaving `devDependencies` inside production container | **`pnpm prune --prod`** before copying to runtime | Unnecessary test runners and dev tools expanding the attack surface. |
