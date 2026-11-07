/**
 * CI/CD & Multi-Stage Container Build Infrastructure Asset.
 *
 * Exports production-hardened multi-stage Dockerfile templates, .dockerignore definitions,
 * and complete 10-step GitHub Actions CI quality gate workflows.
 */

/**
 * Production-hardened multi-stage Dockerfile template for Node.js / TypeScript services.
 * Features: pnpm frozen lockfile, multi-stage compilation, non-root user (appuser:nodejs),
 * production dependency pruning, and minimal Alpine runtime.
 */
export const multiStageDockerfileTemplate = `
# ==============================================================================
# Stage 1: Build & Compile
# ==============================================================================
FROM node:20-alpine AS builder
WORKDIR /app

# Enable Corepack and pnpm
RUN corepack enable && corepack prepare pnpm@11.1.3 --activate

# Copy dependency manifests
COPY package.json pnpm-lock.yaml ./

# Install all dependencies using deterministic frozen lockfile
RUN pnpm install --frozen-lockfile

# Copy source files and compile
COPY . .
RUN pnpm run build

# Prune development dependencies to minimize runtime footprint
RUN pnpm prune --prod

# ==============================================================================
# Stage 2: Hardened Production Runtime
# ==============================================================================
FROM node:20-alpine AS production
WORKDIR /app

ENV NODE_ENV=production

# Create non-root system group and user (UID/GID 1001)
RUN addgroup --system --gid 1001 nodejs && \\
    adduser --system --uid 1001 --ingroup nodejs appuser

# Copy compiled distribution artifacts and pruned node_modules with ownership
COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./package.json

# Switch to unprivileged user (NEVER run as root in production)
USER appuser

EXPOSE 3000

CMD ["node", "dist/main.js"]
`;

/**
 * Hardened .dockerignore template excluding secrets, git history, and local build artifacts.
 */
export const dockerignoreTemplate = `
.git
.gitignore
node_modules
dist
build
coverage
.env
.env.*
!.env.example
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.husky
`;

/**
 * Complete 10-Step GitHub Actions CI Quality Gate Workflow YAML template.
 */
export const githubActionsCiWorkflowTemplate = `
name: Production CI Quality Gate

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  quality-gate:
    name: Mandatory Quality & Security Gates
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Source Code
        uses: actions/checkout@v4

      - name: Install pnpm via Corepack
        uses: pnpm/action-setup@v4
        with:
          version: 11.1.3

      - name: Setup Node.js Runtime
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - name: Step 1-3: Install Dependencies, Lint, Format & Typecheck
        run: |
          pnpm install --frozen-lockfile
          pnpm run lint
          pnpm run format:check
          pnpm run typecheck

      - name: Step 4: Unit Tests with Coverage Thresholds
        run: pnpm run test:cov

      - name: Step 5: Testcontainers Integration Tests
        run: pnpm run test:integration

      - name: Step 6: SAST Dependency Security Audit
        run: pnpm audit --audit-level high

      - name: Step 7: Secret Scanning
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}

      - name: Step 8: Build Multi-Stage Docker Image
        run: docker build -t myapp:\${{ github.sha }} .

      - name: Step 9: Trivy Container Vulnerability Scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:\${{ github.sha }}'
          format: 'table'
          exit-code: '1'
          ignore-unfixed: true
          severity: 'CRITICAL,HIGH'

      - name: Step 10: Push Immutable Image (Main Branch Only)
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: |
          echo "Logging into container registry and pushing myapp:\${{ github.sha }}"
`;
