---
name: dockerfile-builder
description: "Expert skill for authoring, refactoring, and optimizing production multi-stage Dockerfiles across runtimes with non-root security and layer caching."
---

# Dockerfile Builder & Multi-Stage Optimization Skill

## Purpose
Establishes production-grade Dockerfile authoring standards, multi-stage compilation architectures, BuildKit package caching, non-root user privilege drops, and deterministic base image pinning across Node.js, Python, Go, and Java runtimes.

## Architecture & Tooling Matrix
- **Multi-Stage Build Guide**: [references/multi-stage-build-patterns.md](references/multi-stage-build-patterns.md)
- **Layer Caching & Security Guide**: [references/layer-caching-and-security-hardening.md](references/layer-caching-and-security-hardening.md)
- **Automated CLI Validator**: [scripts/audit_dockerfile.py](scripts/audit_dockerfile.py)
- **Starter Templates**:
  - Node/NestJS Dockerfile: [assets/dockerfile-node-template.dockerfile](assets/dockerfile-node-template.dockerfile)
  - Production Dockerignore: [assets/dockerignore-template.dockerignore](assets/dockerignore-template.dockerignore)
- **Verification Suite**: [evals/evals.json](evals/evals.json)

---

## Execution Workflow

### Phase 1: Runtime Stack & Dependency Manifest Inspection
1. Inspect project root to detect runtime and package manager (`package.json`, `requirements.txt`, `go.mod`).
2. Pin the exact semantic base image version (`node:22-alpine`, `python:3.11-slim`, `golang:1.22-alpine`). Avoid `:latest` tags.
3. Determine internal application port (`PORT=3000`) and entrypoint commands.

### Phase 2: Layer Caching & Dependency Isolation
1. Define an initial dependency caching stage (`FROM <base> AS deps`).
2. Copy manifest files (`package.json`, `pnpm-lock.yaml`) *before* copying application source code.
3. Leverage BuildKit cache mounts (`RUN --mount=type=cache,target=/root/.cache/pnpm pnpm install --frozen-lockfile`) for sub-second rebuilds.

### Phase 3: Compilation & Asset Pruning
1. In the compilation stage (`FROM <base> AS builder`), copy dependencies from the `deps` stage.
2. Compile application source code (`pnpm build`).
3. Prune development dependencies (`pnpm prune --prod`) so only production runtime modules remain.

### Phase 4: Production Runner Hardening & Non-Root Execution
1. Create a minimal production execution stage (`FROM <base> AS runner`).
2. Copy only compiled binaries/artifacts and pruned runtime dependencies from the `builder` stage.
3. Switch execution to an unprivileged user (`USER node` or `USER 10001`).
4. Set explicit file ownership using `COPY --chown=node:node ...`.
5. Embed a native `HEALTHCHECK` directive verifying application HTTP responsiveness.

### Phase 5: Build Context Hygiene & Automated CLI Audit
1. Verify `.dockerignore` excludes `node_modules`, `.env`, `.git`, and local test coverage directories.
2. Execute the automated CLI audit tool:
   ```bash
   python3 infra/docker/skills/dockerfile-builder/scripts/audit_dockerfile.py --path . --strict
   ```
3. Test container image compilation:
   ```bash
   docker build --target runner -t my-app:test .
   ```

---

## Gotchas & Common Pitfalls

| Faulty / Anti-Pattern | Production Replacement | Why it Matters |
| :--- | :--- | :--- |
| **Missing `USER` in Runner Stage** | Explicit `USER node` or `USER appuser` | Defaults to `root`, allowing compromised processes full container breakout privileges. |
| **Copying Source Code Before Manifests** (`COPY . .` before `install`) | `COPY package*.json ./` then `install`, then `COPY . .` | Invalidates dependency cache on every single source code edit, bloating build times. |
| **Using `:latest` Base Images** (`FROM node:latest`) | Exact semantic pinning (`FROM node:22-alpine`) | Upstream base image updates introduce unexpected breaking changes and non-deterministic builds. |
| **Missing `.dockerignore`** | Scaffolding comprehensive `.dockerignore` | Injects host `node_modules` and local `.env` secrets into the build context, risking severe credential leaks. |
| **Shipping Compilers in Final Image** | Multi-stage build discarding compilers in Stage 2 | Leaves compilers and build toolchains in production, drastically increasing CVE attack surface. |
| **Static `EXPOSE 3000` without Env Var** | `ENV PORT=3000` and `EXPOSE ${PORT}` | Breaks flexible runtime port configuration on custom cloud platforms. |
