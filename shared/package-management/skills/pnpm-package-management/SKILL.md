---
name: pnpm-package-management
description: "Best practices, CLI commands, monorepo workspace configuration (pnpm-workspace.yaml), and global store optimization for pnpm."
---
# `pnpm` Package Management Skill

## Goal
Guide AI coding agents and developers to efficiently utilize `pnpm` for ultra-fast, disk-efficient dependency management and monorepo orchestration.

## Core Best Practices

### 1. Monorepo Workspace Configuration (`pnpm-workspace.yaml`)
When managing multi-package repositories or microservices, define a root `pnpm-workspace.yaml`:
```yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'frameworks/*'
```

To install dependencies across all workspace packages simultaneously:
```bash
# Install root and child workspace packages
pnpm install

# Add a package to a specific workspace child
pnpm --filter @my-org/web-app add @angular/material
```

### 2. Executing Commands Across Workspaces
- Run build script in all packages: `pnpm -r run build`
- Run test script only in modified packages: `pnpm --filter ...[HEAD] test`

### 3. Global Store Pruning & Verification
Periodically verify or clean unreferenced global store packages:
```bash
# Check integrity of hard-linked store
pnpm store status

# Prune unused packages from global store
pnpm store prune
```

## Constraints & Anti-Patterns
- Never mix `npm` or `yarn` commands in a `pnpm` managed project.
- Do NOT bypass `pnpm-lock.yaml` with direct `node_modules` manual edits.
