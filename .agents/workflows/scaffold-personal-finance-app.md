---
description: "Workflow to scaffold enterprise full-stack Personal Finance Web SPAs with double-entry accounting engine, EMI amortization scheduler, multi-year inflation scenario forecaster, and pgvector category suggestions. Triggered by 'scaffold-finance:', 'finance:', or '/scaffold-personal-finance-app'."
trigger: manual
---

# Scaffold Personal Finance & Net Worth Web Application (SPA)

Follow this step-by-step workflow to scaffold a full-stack personal finance application using Angular 21, NestJS, and PostgreSQL with `pgvector`. Compatible both for fresh initializations and pre-scaffolded Angular / NestJS enterprise projects.

## Steps

### Step 1: Database Setup & pgvector Schema
1. Ensure PostgreSQL is installed with the `vector` extension enabled (`CREATE EXTENSION IF NOT EXISTS vector;`).
2. Create the double-entry accounting tables:
   - `accounts` (Chart of Accounts with `account_type_enum` and `description_embedding vector(1536)`).
   - `journal_entries` and `journal_postings` ($\sum \text{Debits} = \sum \text{Credits}$).
   - `loans_emi` and `amortization_schedules`.
   - `forecasting_scenarios` and `scenario_category_inflations` (for what-if multi-year inflation modeling).

### Step 2: NestJS Backend Domain Integration
1. Initialize NestJS app *(Skip if already scaffolded via CLI / Layer 2 Framework Scaffold)*:
   ```bash
   npx -y @nestjs/cli new backend --strict --package-manager npm
   ```
2. Install TypeORM / Prisma and PostgreSQL dependencies:
   ```bash
   npm install @nestjs/typeorm typeorm pg @nestjs/config class-validator class-transformer
   ```
3. Implement `LedgerModule`:
   - Create transaction posting service with strict balance verification guard (`Math.abs(totalDebit - totalCredit) === 0`).
   - Create Account Head management endpoints (Asset, Liability, Equity, Income, Expense).
4. Implement `AmortizationModule`:
   - Calculate monthly EMI: $M = P \frac{r(1+r)^n}{(1+r)^n - 1}$.
   - Generate full repayment schedule broken down by interest component and principal component.
   - Calculate exact debt-free / payoff completion date.
5. Implement `VectorCategorizationModule`:
   - Embed transaction description strings into vector representations.
   - Perform cosine distance similarity search (`<=>`) against existing account head embeddings to auto-suggest categories for daily spending entries.
6. Implement `ForecastingModule` & `SimulationService`:
   - Apply compound inflation escalation math: $E_{k, t} = E_{k, 0} \times (1 + i_k)^t$.
   - Calculate annual income growth or stagnation: $I_t = I_0 \times (1 + g)^t$.
   - Detect Deficit Crossover Point ($I_t < E_t + \text{EMI}_t$) and project cumulative Net Worth ($NW_t$).

### Step 3: Angular 21 SPA Frontend Domain Integration
1. Initialize Angular 21 project *(Skip if already scaffolded via CLI / Layer 2 Framework Scaffold)*:
   ```bash
   npx -y @angular/cli new frontend --standalone --style=css --routing=true
   ```
2. Install Angular Material / Charting libraries:
   ```bash
   npm install @angular/cdk chart.js ng2-charts
   ```
3. Build Core Components:
   - `AccountHeadManagerComponent` & `ChartOfAccountsTreeComponent`: Tree view of Chart of Accounts classified under The Accounting Equation with automatic balance rollups.
   - `DailySpendingEntryComponent`: Dynamic Debit/Credit line item table with instant live visual balance indicator.
   - `EmiPayoffCountdownComponent`: Loan amortization countdown bar showing remaining installments, interest saved, and payoff date.
   - `NetWorthDashboardComponent`: Dynamic card metrics showing total Assets, total Liabilities, and calculated Net Worth.
   - `FinancialForecastingComponent` & `ScenarioSimulatorWorkspaceComponent`: Interactive "What-If" multi-year scenario simulation workspace with custom inflation rates per category, salary growth sliders, and Deficit warning banner.

### Step 4: Automated Project Documentation (README.md)
Generate a comprehensive, professional `README.md` file in the root of the scaffolded application containing:
- **Project Name**: `NidhiFlow` (Personal Finance & Net Worth Intelligence Engine).
- **Core Architecture Summary**: Formal Double-Entry Bookkeeping ($\sum \text{Debits} = \sum \text{Credits}$), The Accounting Equation, EMI Amortization, 7-Dimensional Forecasting Simulator, and PostgreSQL `pgvector` AI Category Search.
- **Tech Stack Specification**: Angular 21 (Signals) + NestJS TypeScript + PostgreSQL `pgvector`.
- **Local Setup & Development Commands**: Database migration commands, `npm run start:dev` for backend, and `npm run start` for frontend.

### Step 5: Verification & Integration Testing
1. Run backend tests to verify unbalanced transactions are rejected with `400 Bad Request`.
2. Post a sample daily expense entry (e.g. Debit: `EXPENSE: Groceries` ₹1500, Credit: `ASSET: Bank Account` ₹1500). Verify Assets decrease, Expenses increase, and Net Worth updates accurately.
3. Add a sample loan (e.g. Home Loan ₹2,500,000 at 8.5% for 240 months). Verify EMI payoff date is correctly projected.
4. Run a 5-year simulation scenario with 0% salary growth and 8% grocery/rent inflation; verify Angular component highlights the exact crossover year when net cashflow turns negative.
