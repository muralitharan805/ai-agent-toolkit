---
name: seyalicraft-ecosystem-context
description: Guidelines, repository architecture, domain mapping (seyalicraft.com), product suite breakdown (Seyalicraft Portal, NidhiFlow, CivicPath, DevOps Infra), tech stacks, and API protocols for building and maintaining Seyalicraft enterprise software projects.
---

# Seyalicraft Ecosystem & Technical Architecture

## Overview

**Seyalicraft** (`seyalicraft.com`) is an enterprise software engineering ecosystem dedicated to delivering high-performance web portals, personal finance applications, civic infrastructure software, and automated developer infrastructure.

This skill provides AI Agents and software engineers with complete architectural visibility across all Seyalicraft product suites, repository mappings, framework standards, and inter-service communication standards.

---

## Domain Architecture & Ecosystem Mapping

All Seyalicraft production applications operate under the primary root domain **`seyalicraft.com`** and its dedicated subdomains:

- **Root Domain**: `https://seyalicraft.com` (Main Web Portal)
- **Finance Suite**: `https://nidhiflow.seyalicraft.com` (Personal Finance SPA)
- **Finance API**: `https://api.nidhiflow.seyalicraft.com` (NestJS Double-Entry Engine)
- **Civic Suite**: `https://civicpath.seyalicraft.com` (Civic Platform)
- **Developer Toolkit**: `https://toolkit.seyalicraft.com` (AI Agent Toolkit & Docs)

---

## Product Suite & Project Catalog

Projects in Seyalicraft are grouped by **Product Domain** to promote Domain-Driven Design (DDD). Each domain encapsulates its specific **Frontend SPA** and **Backend API** microservices.

```
Seyalicraft Ecosystem (seyalicraft.com)
├── 1. Seyalicraft Portal Domain
│   └── seyalicraft-frontend (Angular Enterprise Web Portal)
│
├── 2. NidhiFlow Product Suite (Personal Finance & Net Worth)
│   ├── nidhiflow-frontend (Angular 21 Signal-driven SPA)
│   └── nidhiflow-backend (NestJS Double-Entry & Amortization API)
│
├── 3. CivicPath Product Suite (Civic Platform)
│   ├── civicpath-frontend (Angular / Web SPA)
│   └── civicpath-backend (NestJS / Node Microservice API)
│
└── 4. DevOps & Developer Infrastructure
    ├── docker-dev-infra (Docker Compose & Infrastructure Templates)
    └── ai-agent-toolkit (Central Agent Skills, Rules & Workflows)
```

### 1. Seyalicraft Portal Domain

#### `seyalicraft-frontend`
- **Repository**: [`muralitharan805/seyalicraft-frontend`](https://github.com/muralitharan805/seyalicraft-frontend)
- **Visibility**: Private
- **Primary Purpose**: Main enterprise web portal for Seyalicraft organization branding, portfolio showcase, technical blogs, interactive developer tools, and client project management.
- **Tech Stack**: Angular 21 (Signals, Material 3, Tailwind/Vanilla CSS), `@angular/ssr`, TypeScript, Cloudflare Pages/Workers (`wrangler.jsonc`).
- **Core Domain Routes**:
  - `/` — **Home**: Hero banner, technical skill stack matrix, featured projects, recent blog highlights.
  - `/projects` — **Projects Showcase**: Searchable/filterable gallery of engineering projects, architecture diagrams, live demo links.
  - `/blog` — **Blog & Insights**: Technical articles, tutorials, and software architecture deep-dives.
  - `/tools` — **Developer Tools**: Interactive client-side developer utility tools and calculators.
  - `/contact` — **Contact**: Interactive contact form with Reactive Forms validation.
- **Architectural Mandates**:
  - Native `@if`, `@for`, `@switch` control flow blocks only (legacy `*ngIf` / `*ngFor` strictly forbidden).
  - DOM Guarding for SSR: Browser-only APIs (`window`, `localStorage`) MUST be guarded with `isPlatformBrowser(this.platformId)`.
  - Testing: Vitest (`pnpm test`).

---

### 2. NidhiFlow Product Suite (Personal Finance & Net Worth)

#### `nidhiflow-frontend`
- **Repository**: [`muralitharan805/nidhiflow-frontend`](https://github.com/muralitharan805/nidhiflow-frontend)
- **Visibility**: Public
- **Primary Purpose**: Interactive Web SPA for personal finance management, double-entry ledger visualization, EMI amortization scheduling, and 7-dimensional scenario forecasting.
- **Tech Stack**: Angular 21, Angular Material, Signals, Chart.js / D3, TypeScript.
- **Key Features**: Net Worth dashboard, EMI recalculation simulator, categorical budget tracking, real-time trial balance view.

#### `nidhiflow-backend`
- **Repository**: [`muralitharan805/nidhiflow-backend`](https://github.com/muralitharan805/nidhiflow-backend)
- **Visibility**: Public
- **Primary Purpose**: High-reliability NestJS backend API serving double-entry bookkeeping engine, immutable journal ledger, EMI amortization calculations, multi-year compounding inflation modeling, and pgvector AI category suggestions.
- **Tech Stack**: NestJS, TypeScript, PostgreSQL (Prisma ORM), Redis (caching & rate limiting), pgvector (vector search).

---

### 3. CivicPath Product Suite (Civic Platform)

#### `civicpath-frontend` & `civicpath-backend`
- **Primary Purpose**: Civic infrastructure tracking, 3-layer boundary GIS detection (DataMeet GeoJSON), election candidate profiling, and public issue tracking.
- **Tech Stack**: Angular Frontend SPA + NestJS / PostGIS Backend Engine.

---

### 4. DevOps & Developer Infrastructure

#### `docker-dev-infra`
- **Repository**: [`muralitharan805/docker-dev-infra`](https://github.com/muralitharan805/docker-dev-infra)
- **Visibility**: Public
- **Primary Purpose**: Centralized Docker Development Infrastructure, Docker Compose templates, PostgreSQL + pgvector containers, Redis containers, and local development proxies.

#### `ai-agent-toolkit` (Current Workspace)
- **Repository**: [`muralitharan805/ai-agent-toolkit`](https://github.com/muralitharan805/ai-agent-toolkit)
- **Visibility**: Public
- **Primary Purpose**: Reusable repository of AI agent skills, rules, workflows, and synchronization CLI utilities (`bin/sync-skills.sh`).

---

## Inter-Service Communication & API Protocols

1. **HTTP/REST Standards**:
   - Standard RESTful endpoint design (`/api/v1/auth`, `/api/v1/transactions`, `/api/v1/amortization`).
   - Standard response payload format: `{ data: T, meta?: Record<string, unknown>, message?: string }`.
2. **Correlation ID Tracing**:
   - Every request MUST pass or generate `X-Correlation-ID` header.
3. **Authentication & Authorization**:
   - JWT Access Tokens (short-lived) + Refresh Tokens (stored in HTTP-Only secure cookies).
4. **Package Management**:
   - Mandatory `pnpm` usage across all repositories (`pnpm install`, `pnpm run dev`, `pnpm build`).

---

## Developer Workflows & Agent Protocol

When working on any Seyalicraft repository:
1. Always reference the product domain context (e.g. `nidhiflow` for finance, `seyalicraft` for main portal).
2. Follow strict type safety: zero `any` types permitted.
3. Use guard clauses to keep logic flat and maintainable.
4. Ensure all public APIs include TSDoc / JSDoc comments.
