# CI/CD Pipelines & Docker Build Infrastructure Reference

## Overview
This reference establishes the engineering principles and implementation runbook for **10-Step CI Pull Request Pipelines**, **Multi-Stage Production Dockerfiles**, **Non-Root Container Hardening**, **Trivy Image Vulnerability Scanning**, and **Immutable Git-SHA Image Versioning**.

---

## 1. The 10-Step Mandatory CI Pipeline Architecture

Every pull request opened against the codebase must execute the following 10 steps. A failure at any step immediately blocks merging:

```
[PR Opened / Commit Pushed]
        │
        ├─► 1. Lint Check             (ESLint / Ruff / golangci-lint)
        ├─► 2. Format Check           (Prettier --check / gofmt)
        ├─► 3. Type Check             (tsc --noEmit / mypy --strict)
        ├─► 4. Unit Tests             (Coverage >= 80% lines, 75% branches)
        ├─► 5. Integration Tests      (Real containers via Testcontainers)
        ├─► 6. SAST Security Scan     (pnpm audit --audit-level high)
        ├─► 7. Secret Scan            (GitLeaks staged diff scan)
        ├─► 8. Docker Build           (Multi-stage build with BuildKit)
        ├─► 9. Container Scan         (Trivy scan: 0 CRITICAL / 0 HIGH CVEs)
        │
        ▼
   [All 9 PR Gates Pass] ──► PR Approved & Merged
        │
        ▼
   [10. Registry Push]   ──► Push immutable myapp:sha-xyz to Registry
```

---

## 2. Multi-Stage Dockerfile Architecture

### Why Single-Stage Images Are Forbidden
Single-stage Docker images bundle the entire compiler SDK, package managers, development dependencies, shell utilities, and Git history into the production image:
- **Massive Image Size**: 800MB–1.5GB images slow down container registry pulls, autoscaling cold starts, and node provisioning.
- **Large Attack Surface**: Package managers (`npm`, `pip`, `apt`) and shells (`bash`, `sh`) allow attackers who exploit an RCE vulnerability to download malware and execute reverse shells.

### Multi-Stage Production Pattern
```dockerfile
# Stage 1: Dependency resolution & compilation
FROM node:20-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@11.1.3 --activate
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build
RUN pnpm prune --prod

# Stage 2: Minimal hardened runtime
FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production

# Create non-root system user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs appuser

# Copy only production artifacts with ownership
COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./package.json

USER appuser
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

---

## 3. Non-Root Runtime Security Enforcement

### Security Principles
- In Linux, container root (`UID 0`) maps directly to host root unless user namespaces (`userns-remap`) are enabled.
- If a container breakout vulnerability occurs while running as root, the attacker gains full control over the underlying Kubernetes worker node host.
- **Mandatory Requirements**:
  1. Define custom system UID and GID $\ge 1000$ (e.g. `1001:1001`).
  2. Grant ownership of required runtime directories to this user (`--chown=appuser:nodejs`).
  3. Declare `USER appuser` before the `CMD` instruction.
  4. In Kubernetes manifests, set `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, and `allowPrivilegeEscalation: false`.

---

## 4. Trivy Container Vulnerability Scanning

Trivy scans container images for vulnerabilities in both operating system packages (Alpine apk, Debian dpkg) and application dependencies.

### Local CLI Execution
```bash
# Scan built image locally
trivy image --exit-code 1 --severity CRITICAL,HIGH myapp:local-test
```

### GitHub Actions Step
```yaml
- name: Scan Docker Image with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'myapp:${{ github.sha }}'
    format: 'table'
    exit-code: '1'
    ignore-unfixed: true
    severity: 'CRITICAL,HIGH'
```

---

## 5. Immutable Versioning & Tagging Strategy

### The Danger of `latest`
- The `latest` tag is a mutable pointer that changes every time a new build is pushed.
- During rolling deployments, if node A pulls `latest` at 10:00 AM and node B pulls `latest` at 10:05 AM (after a hotfix build), the cluster runs two different versions simultaneously under the same label.
- Debugging production outages becomes impossible because there is no link between the running container and the Git commit.

### Production Tagging Rules
1. **Continuous Deployment Tag**: Tag every image with the short Git commit SHA:
   `registry.company.com/myapp:sha-8f2a1b9`
2. **Release Milestone Tag**: Tag formal semantic releases:
   `registry.company.com/myapp:v2.4.1`
3. **Immutability Invariant**: Enable image tag immutability in AWS ECR, GCP Artifact Registry, or Docker Hub to reject overwriting existing tags.
