# pnpm Global Store Mechanics & CI/CD Optimization Reference

## 1. Content-Addressable Global Store & Hard Linking

Traditional package managers (npm, yarn classic) copy identical dependency files repeatedly into every local `node_modules` directory across all projects on disk. `pnpm` utilizes an operating-system-level **content-addressable store** coupled with **hard links**:

```
[~/.local/share/pnpm/store (Content-Addressable Global Store)]
        │                               │
        │ (Hard Link)                   │ (Hard Link)
        ▼                               ▼
[Project A: node_modules/.pnpm]   [Project B: node_modules/.pnpm]
        │                               │
        ▼ (Symlink)                     ▼ (Symlink)
[Project A: node_modules/express] [Project B: node_modules/express]
```

### Key Technical Advantages
1. **Single Disk Copy**: Even if 100 repositories require `lodash@4.17.21`, only one copy exists on the physical storage device.
2. **Instant Installation**: Adding an existing package is a simple hard-link filesystem pointer creation rather than a network download or disk copy.
3. **Immutability Protection**: If source files inside `node_modules` are inadvertently modified, `pnpm store status` detects checksum mismatches immediately.

---

## 2. Store Health & Maintenance

Periodically verify and prune unreferenced packages from the global store:

```bash
# Verify integrity of all hard-linked store files against checksums
pnpm store status

# Prune unreferenced packages that are no longer used by any project
pnpm store prune

# View store directory path
pnpm store path
```

---

## 3. Corepack Engine Pinning (`packageManager`)

To guarantee deterministic builds across development machines and CI/CD runners, pin the authoritative pnpm version in root `package.json`:

```json
{
  "name": "enterprise-monorepo",
  "private": true,
  "packageManager": "pnpm@11.1.3"
}
```

### Enabling Corepack
```bash
# Enable Node.js Corepack integration
corepack enable

# Automatically prepare the pinned pnpm version
corepack prepare pnpm@11.1.3 --activate
```

---

## 4. CI/CD Pipeline Invariants (`--frozen-lockfile`)

In CI/CD environments (GitHub Actions, GitLab CI, Jenkins), dependencies MUST be installed with the `--frozen-lockfile` flag:

```bash
# Strictly forbid unexpected lockfile mutations in automated pipelines
pnpm install --frozen-lockfile
```

### Pipeline Failure Guarantee
If a developer modifies dependencies in `package.json` without committing the updated `pnpm-lock.yaml`, `pnpm install --frozen-lockfile` fails immediately, preventing silent dependency drift between local development and production artifacts.
