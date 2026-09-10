/**
 * Documentation Architecture & Runbook Bootstrap Asset.
 *
 * Exports production-standard Markdown templates for the 5-minute onboarding README,
 * six-pillar docs/ architecture runbooks, and Keep a Changelog templates.
 */

/**
 * Baseline 5-Minute Developer Quick Start README.md template.
 */
export const readmeTemplate = `
# Service Name

> Executive summary defining the service's primary business responsibilities and domain boundary.

## 📋 Prerequisites
- Node.js >= 20.11.0 (LTS)
- pnpm >= 11.1.3
- Docker & Docker Compose v2

## 🚀 5-Minute Quick Start

\`\`\`bash
# 1. Clone repository and initialize environment variables
git clone https://github.com/company/service-name.git && cd service-name
cp .env.example .env

# 2. Launch backing services (PostgreSQL & Redis)
docker compose up -d

# 3. Install dependencies deterministically
pnpm install --frozen-lockfile

# 4. Run database migrations
pnpm run db:migrate

# 5. Start development server
pnpm run dev
\`\`\`

Verify health:
\`\`\`bash
curl -f http://localhost:3000/api/v1/health/ready
\`\`\`

## 🧪 Testing
\`\`\`bash
pnpm test          # Run unit tests
pnpm test:cov      # Run coverage report (>=80% line, >=75% branch)
pnpm test:int      # Run Testcontainers integration tests
\`\`\`

## 📚 Technical Documentation Runbooks
- [System Architecture & Decisions](docs/architecture.md)
- [Local Development Guide](docs/development.md)
- [Testing Standards & Seed Data](docs/testing.md)
- [Deployment & Operational Runbooks](docs/deployment.md)
- [Database Schema & Migrations](docs/database.md)
- [Troubleshooting & Incident Playbooks](docs/troubleshooting.md)
`;

/**
 * Baseline docs/architecture.md template with declarative Mermaid diagrams and ADRs.
 */
export const architectureDocTemplate = `
# System Architecture & Technical Specifications

## 1. Clean Architecture Topology

\`\`\`mermaid
graph TD
    Client[Web, Mobile & Downstream Services] -->|HTTPS REST| Controller[HTTP Presentation Controllers]
    
    subgraph Application Core
        Controller -->|Invoke| UseCase[Application Use Cases]
        UseCase -->|Operate On| Entity[Domain Entities & Rules]
    end

    subgraph Infrastructure
        UseCase -->|Port Interface| Repo[Database Repositories]
        UseCase -->|Port Interface| Cache[Redis Cache Service]
        Repo -->|SQL Queries| DB[(PostgreSQL 16)]
        Cache -->|Key-Value| Redis[(Redis 7)]
    end
\`\`\`

## 2. Architectural Decision Records (ADRs)

### ADR-001: Modular Clean Architecture & Testcontainers
- **Status**: Accepted
- **Context**: Need independent domain logic testable without database locks or mock drift.
- **Decision**: Decouple domain entities from database ORMs. Use Testcontainers for integration tests.
- **Consequences**: Zero database dialect drift. Requires Docker in CI runner environments.
`;

/**
 * Baseline docs/troubleshooting.md template with incident remediation playbooks.
 */
export const troubleshootingDocTemplate = `
# Production Troubleshooting & Incident Response Playbooks

## Playbook 1: Database Connection Pool Exhaustion

- **Alert**: \`HighDatabaseConnectionUtilization\` (> 90% connection pool capacity for > 2m)
- **Symptoms**: Route latency spikes > 2000ms; HTTP 503 Service Unavailable errors returned.
- **Root Cause**: Unindexed slow queries holding active connections or unclosed transactions.
- **Immediate Mitigation**:
  1. Inspect active running queries:
     \`\`\`sql
     SELECT pid, now() - query_start AS duration, query 
     FROM pg_stat_activity 
     WHERE state != 'idle' 
     ORDER BY duration DESC LIMIT 5;
     \`\`\`
  2. Terminate rogue query blocking connection threads:
     \`\`\`sql
     SELECT pg_terminate_backend(pid);
     \`\`\`
  3. Temporarily restart deployment to flush hung pools:
     \`\`\`bash
     kubectl rollout restart deployment/service-name -n production
     \`\`\`
`;

/**
 * Baseline Keep a Changelog template for CHANGELOG.md.
 */
export const changelogTemplate = `
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project scaffolding with Clean Architecture and 5-minute onboarding README.
`;
