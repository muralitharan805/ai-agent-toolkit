# Dockerfile Layer Caching & Security Hardening

## Overview
Docker builds images by executing instructions in order and caching each intermediate layer. Optimizing instruction order minimizes rebuild times, while explicit user constraints prevent security privileges from leaking into production runtimes.

---

## 1. Instruction Ordering & Layer Invalidation
- **Slowest-changing instructions first**: Base images, system package installs (`apk add`, `apt-get install`), and user creations should be declared at the top of the stage.
- **Dependency manifests before source code**: Always `COPY package.json pnpm-lock.yaml ./` before copying application source files. When source files change, Docker reuses the installed dependency layer.
- **Chain RUN commands**: Combine updates and installs into single commands followed by package cache purges (`rm -rf /var/lib/apt/lists/*`) to prevent intermediate bloat.

---

## 2. Non-Root USER Enforcement
- **Default Risk**: Containers without an explicit `USER` instruction execute as `root`. If a containerized process is compromised, the attacker inherits root capabilities.
- **Implementation**:
  - In Alpine: `USER node` (built-in) or `RUN adduser -D -u 10001 appuser && USER appuser`.
  - In Debian/Ubuntu: `RUN useradd -m -u 10001 appuser && USER appuser`.
- **Pre-assign Permissions**: Use `COPY --chown=user:group ...` to ensure runtime user ownership without requiring root permissions during startup.

---

## 3. Mandatory `.dockerignore` Hygiene
Prevent leaking local developer artifacts and secrets into Docker contexts:
```text
.git
.gitignore
.env
.env.*
node_modules
dist
coverage
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.DS_Store
*.md
```
