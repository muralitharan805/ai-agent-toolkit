---
name: nidhiflow-product-context
description: Domain architecture, double-entry bookkeeping engine, net worth tracking, EMI loan amortization calculations, 7-dimensional scenario forecasting, bank auto-reconciliation, Angular 21 Signal SPA (nidhiflow-frontend), and NestJS Prisma microservice API (nidhiflow-backend) for the NidhiFlow personal finance suite under seyalicraft.com.
---

# NidhiFlow Product Suite Architecture & Domain Specification

## Overview

**NidhiFlow** (`nidhiflow.seyalicraft.com`) is Seyalicraft's flagship personal finance, net worth management, and automated accounting platform. It provides individuals with formal double-entry accounting, real-time balance sheet and profit-and-loss statements, EMI loan amortization scheduling, multi-year inflation and financial forecasting, and AI-assisted bank statement reconciliation (`pgvector`).

This skill provides AI Agents and software engineers with complete architectural context, repository structures, data schemas, domain entities, and operational constraints for both the frontend SPA and backend API.

---

## Subdomains & Repositories

- **Frontend Subdomain**: `https://nidhiflow.seyalicraft.com`
- **Backend API Subdomain**: `https://api.nidhiflow.seyalicraft.com`
- **Repositories**:
  - `nidhiflow-frontend`: Angular 21 Signal-driven Web SPA ([`muralitharan805/nidhiflow-frontend`](https://github.com/muralitharan805/nidhiflow-frontend))
  - `nidhiflow-backend`: NestJS Double-Entry & Financial API ([`muralitharan805/nidhiflow-backend`](https://github.com/muralitharan805/nidhiflow-backend))

---

## Architectural Breakdown & Core Components

```
NidhiFlow Product Suite
├── 1. nidhiflow-frontend (Angular 21 Web SPA)
│   ├── Component Hierarchy (Dashboard, Journal, Amortization, Forecast, Reconciliation)
│   ├── Signal Reactive State Management (Net Worth, Accounts Tree, Active Entries)
│   ├── Angular Material 3 & Chart.js / D3 Visualizations
│   └── Multi-Currency & Dark Mode Styling
│
└── 2. nidhiflow-backend (NestJS Microservice API)
    ├── Auth & Multi-Tenant User Guard (JWT + User-Scoped Queries)
    ├── Double-Entry Ledger Engine (Balancing Check: SUM(Debits) == SUM(Credits))
    ├── Immutable Ledger Protocol (Reversing Entries REV-JE-xxx)
    ├── Financial Statements Service (Trial Balance, Balance Sheet, P&L)
    ├── EMI Amortization & Debt Payoff Math Engine
    └── Prisma ORM + PostgreSQL + pgvector AI Search
```

---

## Core Domain Entities & Schemas

### 1. Chart of Accounts (`Account`)

Accounts form the foundational tree hierarchy of the double-entry system. Every account belongs to one of 5 fundamental types: `ASSET`, `LIABILITY`, `EQUITY`, `INCOME`, `EXPENSE`.

```typescript
export enum AccountType {
  ASSET = 'ASSET',
  LIABILITY = 'LIABILITY',
  EQUITY = 'EQUITY',
  INCOME = 'INCOME',
  EXPENSE = 'EXPENSE',
}

export interface AccountNode {
  id: string;
  userId: string;
  code: string; // e.g. "1010" for Cash, "2010" for Credit Card
  name: string;
  type: AccountType;
  parentId?: string | null;
  currencyCode: string; // Default: 'INR'
  taxSection?: string;  // e.g. '80C', '80D', '24B', 'HRA'
  isActive: boolean;
  balance?: number;
  children?: AccountNode[];
}
```

### 2. Balanced Journal Entry & Posting (`JournalEntry` / `JournalPosting`)

Journal entries record financial events. Every entry **must balance** ($\sum \text{Debits} = \sum \text{Credits}$).

```typescript
export enum PostingType {
  DEBIT = 'DEBIT',
  CREDIT = 'CREDIT',
}

export interface JournalPosting {
  id: string;
  accountId: string;
  type: PostingType;
  amount: number; // Positive number > 0
  foreignAmount?: number;
  currencyCode?: string;
}

export interface JournalEntry {
  id: string;
  userId: string;
  entryNumber: string; // Unique string e.g. JE-2026-0042
  entryDate: string;   // ISO Date
  description: string;
  referenceNo?: string;
  isRecurring: boolean;
  isPosted: boolean;
  postings: JournalPosting[];
  createdAt: Date;
}
```

---

## Key Business Logic & Financial Formulas

### 1. The Accounting Equation & Net Worth
$$\text{Assets} = \text{Liabilities} + \text{Equity}$$
$$\text{Net Worth} = \sum \text{Assets} - \sum \text{Liabilities}$$

### 2. Immutable Ledger & Reversing Entries
Posted entries MUST NOT be edited or deleted directly. To correct an entry:
1. Generate reversing entry with number `REV-${originalEntryNumber}`.
2. Flip original Debit allocations to Credit, and Credit allocations to Debit.

### 3. EMI Amortization Formula
$$M = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}$$
Where $M$ = monthly EMI, $P$ = principal loan amount, $r$ = monthly interest rate ($\text{annual rate} / 12 / 100$), $n$ = total tenure in months.

- **Double-Entry Allocation for EMI**:
  - `DEBIT`: Liability Account (Principal Portion)
  - `DEBIT`: Interest Expense Account (Interest Portion)
  - `CREDIT`: Asset Bank Account (Total EMI Amount)

---

## 7-Dimensional Forecasting Engine

1. **Debt Prepayment Accelerator**: Models early payoff and total interest saved.
2. **Emergency Survival Runway**: Calculates runway under 0% income / income shock.
3. **FIRE & Retirement Target**: Projects compounding growth toward retirement corpus.
4. **SIP Life Goal Milestone**: Tracks investment targets over multi-year horizons.
5. **Inflation Crossover Model**: $E_{t} = E_{0} \times (1 + i)^t$ to detect deficit crossover years.
6. **Asset Allocation Sandbox**: Simulates portfolio rebalancing.
7. **Receivable Default Stress Test**: Models bad debt impact.

---

## Technical Stack & Execution Commands

### `nidhiflow-frontend`
- **Framework**: Angular 21 (Signals, Standalone Components, Material 3, Tailwind CSS)
- **Dev Command**: `pnpm run dev` (Runs on `http://localhost:4200`)
- **Build Command**: `pnpm build`

### `nidhiflow-backend`
- **Framework**: NestJS (TypeScript, Prisma ORM, PostgreSQL, Redis)
- **Dev Command**: `pnpm run start:dev` (Runs on `http://localhost:3000`)
- **Database Migration**: `pnpm run prisma:migrate`
