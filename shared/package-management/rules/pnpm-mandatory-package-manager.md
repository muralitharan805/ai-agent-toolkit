---
trigger: always_on
description: "Mandates that pnpm MUST be used as the exclusive package manager for installing dependencies, running scripts, and executing CLI binaries across all projects. Prohibits raw npm or yarn usage."
---
# Mandatory `pnpm` Package Manager Rule

## Description
Enforces `pnpm` as the single, authoritative package manager for all projects. Eliminates disk bloat, prevents phantom dependency leakage, and guarantees fast, deterministic builds via `pnpm-lock.yaml`.

## Strict Command Mappings & Restrictions

### 1. Package Installation Commands
- NEVER use `npm install`, `npm i`, `yarn add`, or `yarn install`.
- ALWAYS use `pnpm` equivalent commands:

| Action | Restricted Command (DO NOT USE) | Mandatory `pnpm` Command |
| :--- | :--- | :--- |
| **Install project dependencies** | `npm install` / `yarn install` | `pnpm install` |
| **Add runtime dependency** | `npm i <pkg>` / `yarn add <pkg>` | `pnpm add <pkg>` |
| **Add dev dependency** | `npm i -D <pkg>` / `yarn add -D <pkg>` | `pnpm add -D <pkg>` |
| **Remove dependency** | `npm uninstall <pkg>` / `yarn remove <pkg>` | `pnpm remove <pkg>` |
| **Execute CLI binary without install** | `npx <cmd>` / `yarn dlx <cmd>` | `pnpm dlx <cmd>` or `pnpm exec <cmd>` |
| **Run package script** | `npm run <script>` / `yarn <script>` | `pnpm <script>` or `pnpm run <script>` |

### 2. Lockfile Enforcement
- Commit ONLY `pnpm-lock.yaml` to Git version control.
- Delete any leftover `package-lock.json` or `yarn.lock` files to prevent package manager conflicts.

### 3. Corepack & Package Manager Engine Definition
- Every root `package.json` MUST specify the exact pnpm engine version using Corepack:
```json
{
  "packageManager": "pnpm@11.1.3"
}
```

### 4. CI/CD Pipeline Protocol
- CI/CD build scripts MUST use `pnpm install --frozen-lockfile` to ensure zero unexpected lockfile mutations.
