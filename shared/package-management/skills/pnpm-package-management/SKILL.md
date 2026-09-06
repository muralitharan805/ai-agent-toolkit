---
name: pnpm-package-management
description: Enforces pnpm as the exclusive package manager, monorepo workspace orchestration (pnpm-workspace.yaml), Corepack engine pinning, lockfile hygiene, and global store optimization. Triggered by 'pnpm:', 'package-manager:', or 'monorepo:'.
---

# `pnpm` Package Management & Monorepo Architecture Skill

## Overview

This skill establishes `pnpm` as the authoritative, exclusive package manager across all applications, libraries, and microservices. It guarantees ultra-fast dependency resolution, eliminates phantom dependency leakage via symlinked `node_modules`, enforces strict single-lockfile hygiene (`pnpm-lock.yaml`), and guides monorepo orchestration using `pnpm-workspace.yaml`.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                       5-Phase pnpm Management Pipeline                         │
└────────────────────────────────────────────────────────────────────────────────┘
  [Phase 1: Corepack Pinning]       ──► Declare `"packageManager": "pnpm@..."`
               │
  [Phase 2: Strict Command Mapping] ──► Zero `npm` or `yarn`; use `pnpm` equivalents
               │
  [Phase 3: Workspace Filtering]    ──► `--filter` and recursive `-r` execution
               │
  [Phase 4: Lockfile Hygiene]       ──► Prune stray `package-lock.json` & `yarn.lock`
               │
  [Phase 5: Store & CI Tuning]      ──► CI `--frozen-lockfile` & global store pruning
```

---

## 5-Phase Implementation Protocol

### Phase 1: Package Manager Verification & Corepack Pinning
1. **Root Engine Pinning**: Declare the authoritative pnpm version in root `package.json`:
   ```json
   {
     "packageManager": "pnpm@11.1.3"
   }
   ```
2. **Corepack Activation**:
   ```bash
   corepack enable
   corepack prepare pnpm@11.1.3 --activate
   ```

### Phase 2: Strict Command Mapping (Zero npm / yarn)
Never execute raw `npm` or `yarn` commands. Map all package operations to their `pnpm` counterparts:

| Operation | ❌ Forbidden Command | ✅ Mandatory `pnpm` Command |
| :--- | :--- | :--- |
| Install dependencies | `npm install` / `yarn install` | `pnpm install` |
| Add runtime dependency | `npm i <pkg>` / `yarn add <pkg>` | `pnpm add <pkg>` |
| Add dev dependency | `npm i -D <pkg>` / `yarn add -D <pkg>` | `pnpm add -D <pkg>` |
| Remove dependency | `npm uninstall <pkg>` / `yarn remove <pkg>` | `pnpm remove <pkg>` |
| Execute CLI binary | `npx <cmd>` / `yarn dlx <cmd>` | `pnpm dlx <cmd>` or `pnpm exec <cmd>` |
| Run package script | `npm run <script>` / `yarn <script>` | `pnpm <script>` or `pnpm run <script>` |

### Phase 3: Monorepo Workspace Filtering & Topological Execution
1. **Workspace Configuration**: Define packages in root `pnpm-workspace.yaml`:
   ```yaml
   packages:
     - 'apps/*'
     - 'packages/*'
     - 'frameworks/*'
     - 'shared/*'
   ```
2. **Filtered & Recursive Execution**:
   ```bash
   # Add dependency to specific package
   pnpm --filter @org/web-app add @angular/material

   # Build package and all internal dependencies
   pnpm --filter @org/web-app... build

   # Run build across all packages in topological dependency order
   pnpm -r run build
   ```

### Phase 4: Lockfile Hygiene & Stray Lockfile Pruning
1. **Single Lockfile Invariant**: Commit exclusively `pnpm-lock.yaml` to Git version control.
2. **Stray Lockfile Deletion**: Delete any accidental `package-lock.json` or `yarn.lock` files to prevent package manager conflicts.

### Phase 5: Content-Addressable Store Maintenance & CI Optimization
1. **CI/CD Frozen Lockfiles**: In automated pipelines, always install dependencies with `--frozen-lockfile`:
   ```bash
   pnpm install --frozen-lockfile
   ```
2. **Store Maintenance**: Periodically inspect or prune unreferenced packages:
   ```bash
   pnpm store status
   pnpm store prune
   ```

---

## Local References & Assets

- **Monorepo & Workspace Guide**: [references/pnpm-monorepo-and-workspace-guide.md](references/pnpm-monorepo-and-workspace-guide.md)
- **Store Mechanics & CI/CD Optimization**: [references/pnpm-store-and-ci-optimizations.md](references/pnpm-store-and-ci-optimizations.md)
- **Package Manager Hygiene CLI Auditor**: [scripts/audit_package_manager.py](scripts/audit_package_manager.py)
- **pnpm Workspace Starter Template**: [assets/pnpm-workspace-template.yaml](assets/pnpm-workspace-template.yaml)
- **Root package.json Template**: [assets/pnpm-package-template.json](assets/pnpm-package-template.json)

---

## Automated Verification Protocol

Audit repositories for stray lockfiles and package manager hygiene:
```bash
python3 scripts/audit_package_manager.py --path . --strict
```

---

## Gotchas & Anti-Patterns

| Anti-Pattern | Why It Fails | Modern `pnpm` Best Practice |
| :--- | :--- | :--- |
| **Phantom Dependencies** | Flat `node_modules` allows code to import unlisted transitive packages. | `pnpm` symlink isolation ensures only explicitly declared packages are importable. |
| **Running `npm install` in pnpm Project** | Creates duplicate `package-lock.json`, bloats disk, corrupts symlinked layout. | Strictly prohibit `npm`/`yarn`. Commit only `pnpm-lock.yaml`. |
| **Using `npx` for Tool Execution** | Bypasses local workspace binaries, slow, downloads untracked packages. | Use `pnpm dlx <cmd>` for one-off CLI tools or `pnpm exec <cmd>` for workspace binaries. |
| **Un-frozen Lockfiles in CI** | Allows subtle dependency drift between developers and production builds. | Always run `pnpm install --frozen-lockfile` in CI/CD pipelines. |
| **Manual `node_modules` Modifications** | Breaks content-addressable store checksums and hard-link integrity. | Update `package.json` and reinstall cleanly via `pnpm install`. |
| **Missing `workspace:*` Protocol** | Monorepo packages attempt to fetch unreleased local packages from public npm registry. | Use `workspace:*` or `workspace:^` for internal cross-package dependencies. |
