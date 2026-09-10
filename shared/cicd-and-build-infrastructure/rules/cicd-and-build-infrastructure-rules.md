---
trigger: model_decision
description: "Enforces 10-step mandatory CI pipeline gates, multi-stage Docker builds with non-root runtime users, frozen lockfile installations, Trivy image vulnerability scanning, and immutable git-SHA tagging."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# CI/CD & Build Infrastructure Standards

## Description
Enforces enterprise continuous integration (CI) quality gates, deterministic multi-stage container builds, non-root runtime container hardening, automated container vulnerability scanning, and immutable image versioning across all backend microservices. Mandates that every pull request passes a strict 10-step CI pipeline before merge eligibility, packages artifacts inside minimal multi-stage Docker images running as unprivileged system users (`USER appuser`), prohibits mutable container tags (`latest`) in production deployments, enforces deterministic frozen lockfile installations (`pnpm install --frozen-lockfile`), and blocks release images failing Trivy vulnerability scans.

## Constraints

### 1. 10-Step Mandatory CI Pull Request Pipeline
- Every pull request MUST trigger an automated CI pipeline that executes the following 10 steps sequentially or with safe parallelization:
  1. **Lint Check**: Rejects unlinted or warning-heavy code.
  2. **Format Check**: Enforces Prettier / language auto-formatter compliance.
  3. **Type Check**: Executes strict static type verification (`tsc --noEmit`, `mypy --strict`).
  4. **Unit Tests & Coverage**: Verifies isolated unit tests and enforces $\ge 80\%$ line and $\ge 75\%$ branch coverage gates.
  5. **Integration Tests**: Executes real containerized tests via Testcontainers.
  6. **SAST Security Scan**: Audits dependencies for known vulnerabilities (`pnpm audit --audit-level high`).
  7. **Secret Scan**: Inspects git diffs with GitLeaks to verify zero leaked credentials.
  8. **Docker Build**: Compiles multi-stage production container image.
  9. **Container Vulnerability Scan**: Scans built image via Trivy for OS and package CVEs.
  10. **Registry Push**: Pushes immutable image to artifact registry (executed on merge to main branch only).
- Pull requests failing ANY of these 10 steps MUST be automatically blocked from merging.

### 2. Multi-Stage Dockerfile & Minimal Attack Surface
- Container builds MUST employ multi-stage Dockerfiles:
  - **Stage 1 (Builder)**: Uses full developer SDK/compiler image to install dependencies with a frozen lockfile, compile assets, and generate distribution bundles (`dist/`).
  - **Stage 2 (Production Runtime)**: Uses minimal base runtime image (e.g. `node:20-alpine`, `distroless`, `alpine:3.19`).
- Production runtime images MUST NOT contain build tools (compilers, git, build-essential, full package managers), development dependencies (`devDependencies`), or source code repositories (`.git/`).
- The `.dockerignore` file MUST explicitly exclude `node_modules`, `.env*`, `.git`, `coverage`, `dist`, and test artifacts.

### 3. Non-Root Runtime Security Enforcement
- Containers running in production environments MUST NEVER execute as the `root` user (UID 0).
- Dockerfiles MUST create an explicit unprivileged system group and user (UID $\ge 1000$) and declare the `USER` instruction:
  ```dockerfile
  RUN addgroup --system --gid 1001 appgroup && \
      adduser --system --uid 1001 --ingroup appgroup appuser
  USER appuser
  ```
- Kubernetes manifests and Docker Compose configurations MUST enforce non-root execution (`securityContext.runAsNonRoot: true`, `securityContext.readOnlyRootFilesystem: true`).

### 4. Immutable Image Versioning & Prohibition of `latest`
- In production deployment manifests (Kubernetes Deployments, Helm charts, ECS task definitions), using mutable image tags such as `latest`, `master`, or `main` is STRICTLY FORBIDDEN.
- Container images MUST be tagged with immutable, traceable identifiers:
  - **Git Commit SHA**: `myapp:sha-7f3b1a2` (Required for continuous deployment and rollbacks).
  - **Semantic Versioning**: `myapp:v1.4.2` (Required for release milestones).
- Mutable tags cause unpredictable rolling deployment states where replica pods run disparate image digests.

### 5. Automated Container Vulnerability Scanning (Trivy)
- Built container images MUST be scanned for operating system and application vulnerabilities prior to deployment or registry pushing.
- CI pipelines MUST integrate automated vulnerability scanners (e.g. Aquasec Trivy, Snyk, or AWS ECR basic scanning).
- Pipeline runs MUST fail with non-zero exit codes if any **CRITICAL** or **HIGH** unpatched vulnerabilities are discovered in the base image or runtime dependencies.

### 6. Deterministic Dependency Installation Invariant
- CI/CD build scripts MUST NEVER use commands that resolve or mutate package lockfiles (`npm install`, `yarn install`, `pnpm install` without flags).
- CI/CD scripts MUST use frozen lockfile commands:
  - Node.js: `pnpm install --frozen-lockfile`
  - Python: `pip install --no-deps -r requirements.lock` or `uv sync --frozen`
  - Go: `go mod download` with verified `go.sum`
- Any build mutating the lockfile during CI execution MUST abort immediately.

## Examples

### 1. Multi-Stage Production Dockerfile (TypeScript / Node.js)
```dockerfile
# ✅ CORRECT: Hardened multi-stage build, frozen lockfile, minimal runtime, non-root user
# Stage 1: Build & compile
FROM node:20-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@11.1.3 --activate
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build && pnpm prune --prod

# Stage 2: Production runtime
FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs appuser
COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./package.json
USER appuser
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

### 2. GitHub Actions CI Quality Gate Workflow (`.github/workflows/ci.yml`)
```yaml
# ✅ CORRECT: 10-step mandatory CI pipeline with frozen install, Trivy scan, and SHA tag
name: CI Quality Gate
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 11.1.3
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - name: Install dependencies (frozen)
        run: pnpm install --frozen-lockfile

      - name: Lint & Format Check
        run: pnpm run lint && pnpm run format:check

      - name: Type Check
        run: pnpm run typecheck

      - name: Unit Tests
        run: pnpm run test:cov

      - name: SAST Dependency Audit
        run: pnpm audit --audit-level high

      - name: Build Docker Image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Trivy Vulnerability Scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:${{ github.sha }}'
          format: 'table'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'
```
