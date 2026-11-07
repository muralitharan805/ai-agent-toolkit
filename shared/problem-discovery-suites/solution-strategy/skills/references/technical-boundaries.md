# Technical Boundaries & Architecture Scope Reference

## Purpose
This document enforces strict scope boundaries for the **Solution Strategy** capability. It defines the exact boundary between *architectural shape definition* (which this skill governs) and *low-level implementation hallucination* (which is strictly forbidden).

---

## The Core Scope Distinction

```text
ALLOWED: ARCHITECTURAL SHAPE & OPERATIONAL PROFILE
├── Solution Class (e.g. INTEGRATION_SERVICE, CLI_UTILITY)
├── Execution Surface (e.g. Headless daemon, Browser DOM, Local CLI)
├── State Locality (e.g. In-memory, Local SQLite, Remote transactional DB)
├── Network Topography (e.g. Pull polling, Push webhooks, Direct peer sync)
└── Security & Compliance Boundaries (e.g. Air-gapped, End-to-end encrypted)

FORBIDDEN: IMPLEMENTATION HALLUCINATION & BIKESHEDDING
├── Specific UI Frameworks (e.g. Next.js vs Remix vs Angular vs Vue)
├── Specific CSS/Styling Tools (e.g. TailwindCSS, Styled Components)
├── Specific Database Vendors (e.g. PostgreSQL vs MySQL vs MongoDB)
├── Specific ORMs / State Libraries (e.g. Prisma vs Drizzle, Redux vs Zustand)
├── Speculative Commercial Pricing Tiers (e.g. "$29/mo Starter, $99/mo Pro")
└── Fictitious Marketing Copy, Brand Names, or Slogans
```

---

## Why Premature Tech Stack Lock-in Fails

1. **Premature Optimization**: Debating Postgres connection pool sizes or Kubernetes manifests for a workflow executed 3 times a day by 2 people wastes engineering attention.
2. **False Rigidity**: Committing to a full-stack web framework before user workflow habits are established locks the builder into a heavy codebase when a 50-line CLI script was all that was needed.
3. **Distraction from Discovery**: The goal of problem discovery is de-risking user adoption and business viability, not showcasing developer resume technology.

---

## Permitted Technical Characterization

When describing the architecture in `SolutionAssessment`, characterization must remain at the structural systems level:

### Compliant Examples

| Solution Class | Compliant Operational Profile | Non-Compliant Implementation Hallucination |
|---|---|---|
| `LOCAL_SCRIPT` | "Single-file script reading CSV from stdin and writing normalized JSON to stdout. Uses standard library parsers." | "Python 3.12 script using Pandas, Click, Pydantic, and SQLite with SQLAlchemy." |
| `BROWSER_EXTENSION` | "Manifest V3 extension using content script DOM injection and chrome.storage.local for operator preferences." | "React 19 extension styled with Tailwind CSS, built with Vite and Zustand store." |
| `INTEGRATION_SERVICE` | "Stateless scheduled worker polling source REST API every 15 minutes, deduplicating via transactional key, and pushing batch updates to webhook." | "Node.js Express microservice on AWS ECS Fargate with BullMQ, Redis, PostgreSQL, and Prisma ORM." |
| `MULTI_TENANT_SAAS` | "Multi-tenant cloud service with tenant-isolated schema, authenticated API gateway, asynchronous queue for long-running reports, and Stripe billing integration." | "Next.js App Router on Vercel with Supabase Auth, Prisma ORM, Neon Postgres, Resend, and Shadcn UI." |

---

## Guidelines for Downstream Hand-off

Once the `SolutionAssessment` is finalized and marked `READY_TO_BUILD` in the SQLite `candidates` table:
1. The builder selects the implementation technology that best matches their team's existing core competencies and operational stack.
2. For portfolio and utility projects, refer to the developer profile:
   - Primary: Angular, Next.js, Node.js, NestJS, Spring Boot, Laravel, PHP, Docker, AWS.
3. The solution strategy provides the **requirements and boundaries**, leaving implementation details to the engineering phase.
