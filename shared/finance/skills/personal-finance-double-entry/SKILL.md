---
name: personal-finance-double-entry
description: "Architectural guidelines, database schemas, double-entry bookkeeping engine protocols, EMI loan amortization calculations, 7-dimensional multi-year inflation scenario forecasting engine, interactive Chart of Accounts tree, pgvector AI category search, NestJS modules, and Angular 21 Signal-driven components for building Personal Finance & Net Worth Web SPAs."
---

# Personal Finance & Net Worth Engine (Double-Entry Bookkeeping & Advanced Forecasting)

## Goal
Guide the design and implementation of an enterprise-grade Personal Finance Web SPA. Enforces formal **Double-Entry Bookkeeping**, **The Accounting Equation**, **EMI Amortization & Debt Payoff Projections**, **7-Dimensional Financial Forecasting Engine (Inflation, FIRE Retirement, Debt-Free Prepayment, Emergency Runway, Goal Targets, Tax, & Investment Growth)**, **Interactive Chart of Accounts Tree**, and **AI Vector Search (`pgvector`)** using **Angular 21** and **NestJS**.

---

# Core Domain & Accounting Principles

### 1. The Accounting Equation & Net Worth
Every monetary transaction affects the core accounting equation:

$$\text{Assets} = \text{Liabilities} + \text{Equity}$$

$$\text{Net Worth} = \sum \text{Assets} - \sum \text{Liabilities}$$

Where:
- **Assets**: Cash, Bank Accounts, Mutual Funds, Stocks, Real Estate, Lending / Receivables.
- **Liabilities**: Credit Card Balance, Personal Loans, Home Loan/Mortgage, Vehicle EMI, Payables.
- **Equity**: Retained Earnings + Capital / Opening Balance.
- **Income**: Salary, Investment Dividends, Interest Earned, Rental Income.
- **Expenses**: Groceries, Rent, Utilities, Transport, Medical, Entertainment, Education, etc.

### 2. Double-Entry Posting Rules
Every transaction MUST contain a balanced set of postings ($\sum \text{Debits} = \sum \text{Credits}$):

| Account Type | Increase (+)| Decrease (-) | Normal Balance |
| :--- | :--- | :--- | :--- |
| **Asset** | Debit ($\text{Dr}$) | Credit ($\text{Cr}$) | Debit |
| **Expense** | Debit ($\text{Dr}$) | Credit ($\text{Cr}$) | Debit |
| **Liability** | Credit ($\text{Cr}$) | Debit ($\text{Dr}$) | Credit |
| **Equity** | Credit ($\text{Cr}$) | Debit ($\text{Dr}$) | Credit |
| **Income** | Credit ($\text{Cr}$) | Debit ($\text{Dr}$) | Credit |

### 3. EMI Amortization & Debt Payoff Formula
For loans and EMIs, monthly installment ($M$) is calculated using standard amortization math:

$$M = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}$$

---

# 7 Advanced Forecasting & Scenario Dimensions

### Dimension 1: Debt-Free Prepayment & Interest Savings Forecast
$$\text{New Principal Component } P'_k = P_k + P_{\text{extra}}$$
$$\text{Tenure Reduction } \Delta n = n_{\text{original}} - n_{\text{new}}$$
$$\text{Interest Saved } = \sum I_{\text{original}} - \sum I_{\text{new}}$$

### Dimension 2: Emergency Cash Runway & Survival Forecast (Income Shock)
$$\text{Runway (Months)} = \frac{\sum \text{Liquid Assets (Cash, Bank, FD)}}{\text{Monthly Mandated Expenses } (E_{\text{essential}} + \text{EMI})}$$

### Dimension 3: FIRE (Financial Independence Retire Early) & Retirement Corpus Forecast
$$\text{Future Annual Expense } E_{\text{retire}} = E_{\text{current}} \times (1 + i)^{y_{\text{retire}} - y_{\text{current}}}$$
$$\text{Required FIRE Corpus } C_{\text{FIRE}} = E_{\text{retire}} \times 25$$

### Dimension 4: Life Goal & Milestone Target Forecast (SIP Calculator)
$$\text{Monthly SIP } S = \frac{G \times r}{(1 + r)^N - 1}$$

### Dimension 5: Multi-Year Inflation Escalation & Deficit Crossover Forecast
$$E_{k, t} = E_{k, 0} \times (1 + i_k)^t$$
$$I_t = I_0 \times (1 + g)^t$$
$$\text{Deficit Crossover condition: } I_t < \sum E_{k,t} + \text{EMI}_t \implies C_t < 0$$

### Dimension 6: Asset Allocation & Compound Investment Growth Forecast
$$A_t = A_0 (1 + R)^t + S \left[ \frac{(1 + R)^t - 1}{R} \right]$$

### Dimension 7: Lending & Receivable Default Impact Forecast
Simulates cashflow impact if lent money (receivables) defaults or delays payment by 6-24 months.

---

# Database Schema Specification (PostgreSQL + `pgvector`)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Chart of Accounts
CREATE TYPE account_type_enum AS ENUM ('ASSET', 'LIABILITY', 'EQUITY', 'INCOME', 'EXPENSE');

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    type account_type_enum NOT NULL,
    parent_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    description_embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Double-Entry Journal Entries & Postings
CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_date DATE NOT NULL,
    description TEXT NOT NULL,
    reference_no VARCHAR(64),
    is_posted BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TYPE posting_type_enum AS ENUM ('DEBIT', 'CREDIT');

CREATE TABLE journal_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id),
    type posting_type_enum NOT NULL,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0)
);

-- 3. Loans & EMI Tracker
CREATE TABLE loans_emi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    liability_account_id UUID NOT NULL REFERENCES accounts(id),
    expense_account_id UUID NOT NULL REFERENCES accounts(id),
    principal_amount NUMERIC(15, 2) NOT NULL,
    annual_interest_rate NUMERIC(5, 2) NOT NULL,
    tenure_months INT NOT NULL,
    start_date DATE NOT NULL,
    monthly_emi NUMERIC(15, 2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- 4. Financial Goals & Target Milestones
CREATE TABLE financial_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    target_amount NUMERIC(15, 2) NOT NULL,
    target_year INT NOT NULL,
    expected_cagr NUMERIC(5, 2) DEFAULT 12.00,
    current_allocated_savings NUMERIC(15, 2) DEFAULT 0.00
);

-- 5. Forecasting Scenarios
CREATE TABLE forecasting_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    description TEXT,
    horizon_years INT DEFAULT 5,
    income_annual_growth_rate NUMERIC(5, 2) DEFAULT 0.00,
    default_expense_inflation_rate NUMERIC(5, 2) DEFAULT 6.00,
    extra_monthly_prepayment NUMERIC(15, 2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# Angular 21 Standalone Core UI Components

### 1. Chart of Accounts Tree Component (`chart-of-accounts-tree.component.ts`)

```typescript
import { Component, input, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface AccountTreeNode {
  id: string;
  code: string;
  name: string;
  type: 'ASSET' | 'LIABILITY' | 'EQUITY' | 'INCOME' | 'EXPENSE';
  balance: number;
  children?: AccountTreeNode[];
}

@Component({
  selector: 'app-chart-of-accounts-tree',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="card p-6 bg-slate-900 text-slate-100 rounded-2xl border border-slate-800 shadow-2xl">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h2 class="text-2xl font-bold text-emerald-400">Chart of Accounts Hierarchy</h2>
          <p class="text-slate-400 text-sm">Organized under The Accounting Equation (Assets = Liabilities + Equity)</p>
        </div>
        <div class="flex gap-2">
          <span class="px-3 py-1 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full text-xs font-bold">
            Assets: ₹{{ totalAssets() | number }}
          </span>
          <span class="px-3 py-1 bg-rose-950 text-rose-400 border border-rose-800 rounded-full text-xs font-bold">
            Liabilities: ₹{{ totalLiabilities() | number }}
          </span>
        </div>
      </div>

      <div class="space-y-4">
        <ng-container *ngFor="let group of accountGroups()">
          <div class="bg-slate-950 rounded-xl p-4 border border-slate-800">
            <div class="flex justify-between items-center font-bold text-lg mb-3" [ngClass]="getGroupColor(group.type)">
              <span>{{ group.type }} ACCOUNTS</span>
              <span>Total: ₹{{ group.totalBalance | number }}</span>
            </div>

            <div class="pl-4 space-y-2 border-l-2 border-slate-800">
              <div *ngFor="let acc of group.accounts" class="flex justify-between items-center p-2 rounded-lg hover:bg-slate-800/50 transition-all text-sm font-mono">
                <div class="flex items-center gap-2">
                  <span class="text-xs text-slate-500 font-bold">[{{ acc.code }}]</span>
                  <span class="text-slate-200">{{ acc.name }}</span>
                </div>
                <span class="font-bold" [class.text-emerald-400]="group.type === 'ASSET' || group.type === 'EXPENSE'" [class.text-cyan-400]="group.type === 'INCOME'" [class.text-rose-400]="group.type === 'LIABILITY'">
                  ₹{{ acc.balance | number:'1.2-2' }}
                </span>
              </div>
            </div>
          </div>
        </ng-container>
      </div>
    </div>
  `
})
export class ChartOfAccountsTreeComponent {
  accounts = input<AccountTreeNode[]>([]);

  accountGroups = computed(() => {
    const list = this.accounts();
    const types = ['ASSET', 'LIABILITY', 'EQUITY', 'INCOME', 'EXPENSE'] as const;

    return types.map(t => {
      const filtered = list.filter(a => a.type === t);
      const totalBalance = filtered.reduce((sum, a) => sum + a.balance, 0);
      return { type: t, accounts: filtered, totalBalance };
    });
  });

  totalAssets = computed(() => {
    return this.accounts().filter(a => a.type === 'ASSET').reduce((sum, a) => sum + a.balance, 0);
  });

  totalLiabilities = computed(() => {
    return this.accounts().filter(a => a.type === 'LIABILITY').reduce((sum, a) => sum + a.balance, 0);
  });

  getGroupColor(type: string): string {
    switch (type) {
      case 'ASSET': return 'text-emerald-400';
      case 'LIABILITY': return 'text-rose-400';
      case 'EQUITY': return 'text-purple-400';
      case 'INCOME': return 'text-cyan-400';
      case 'EXPENSE': return 'text-amber-400';
      default: return 'text-slate-300';
    }
  }
}
```

### 2. Interactive Scenario Simulator Workspace (`scenario-simulator-workspace.component.ts`)

```typescript
import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-scenario-simulator-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="card p-6 bg-slate-900 text-slate-100 rounded-2xl border border-slate-800 shadow-2xl space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-bold text-amber-400">Interactive 5-Year What-If Simulator</h2>
          <p class="text-slate-400 text-sm">Adjust real-time inflation sliders to simulate future net worth & deficit crossover points.</p>
        </div>
        <span class="px-3 py-1 bg-amber-950 text-amber-400 border border-amber-800 rounded-full text-xs font-bold">
          WOW SIMULATOR ENGINE
        </span>
      </div>

      <!-- Realtime Sliders -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 bg-slate-950 p-6 rounded-xl border border-slate-800">
        <div>
          <div class="flex justify-between text-sm font-semibold mb-2">
            <span class="text-slate-400">Salary Growth Rate</span>
            <span class="text-emerald-400 font-mono">{{ salaryGrowth() }}% / yr</span>
          </div>
          <input type="range" min="0" max="20" [(ngModel)]="salaryGrowth" class="w-full accent-emerald-500" />
        </div>

        <div>
          <div class="flex justify-between text-sm font-semibold mb-2">
            <span class="text-slate-400">Grocery Inflation</span>
            <span class="text-rose-400 font-mono">{{ groceryInflation() }}% / yr</span>
          </div>
          <input type="range" min="0" max="25" [(ngModel)]="groceryInflation" class="w-full accent-rose-500" />
        </div>

        <div>
          <div class="flex justify-between text-sm font-semibold mb-2">
            <span class="text-slate-400">Rent Escalation</span>
            <span class="text-amber-400 font-mono">{{ rentInflation() }}% / yr</span>
          </div>
          <input type="range" min="0" max="25" [(ngModel)]="rentInflation" class="w-full accent-amber-500" />
        </div>
      </div>

      <!-- Deficit Crossover Warning Banner -->
      <div *ngIf="crossoverYear()" class="p-4 bg-rose-950/70 border border-rose-500 text-rose-200 rounded-xl flex justify-between items-center animate-pulse">
        <div>
          <h4 class="font-bold text-lg">⚠️ DEFICIT WARNING DETECTED!</h4>
          <p class="text-sm">In <strong>Year {{ crossoverYear() }}</strong>, projected expenses & loan EMIs will surpass total income!</p>
        </div>
        <span class="text-3xl">📊</span>
      </div>

      <!-- Trajectory Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
          <span class="text-xs text-slate-400 font-semibold block">YEAR 1 NET WORTH</span>
          <span class="text-2xl font-bold font-mono text-cyan-400">₹{{ yearlyResults()[0].netWorth | number }}</span>
        </div>
        <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
          <span class="text-xs text-slate-400 font-semibold block">YEAR 3 NET WORTH</span>
          <span class="text-2xl font-bold font-mono text-cyan-400">₹{{ yearlyResults()[2].netWorth | number }}</span>
        </div>
        <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
          <span class="text-xs text-slate-400 font-semibold block">YEAR 5 NET WORTH</span>
          <span class="text-2xl font-bold font-mono" [class.text-emerald-400]="yearlyResults()[4].netWorth >= 0" [class.text-rose-400]="yearlyResults()[4].netWorth < 0">
            ₹{{ yearlyResults()[4].netWorth | number }}
          </span>
        </div>
      </div>
    </div>
  `
})
export class ScenarioSimulatorWorkspaceComponent {
  salaryGrowth = signal<number>(0);
  groceryInflation = signal<number>(8);
  rentInflation = signal<number>(10);

  baseIncome = 1200000;
  baseGrocery = 240000;
  baseRent = 360000;
  baseOther = 200000;
  annualEmi = 300000;
  initialNetWorth = 1000000;

  yearlyResults = computed(() => {
    const list = [];
    let nw = this.initialNetWorth;

    for (let y = 1; y <= 5; y++) {
      const inc = this.baseIncome * Math.pow(1 + this.salaryGrowth() / 100, y - 1);
      const groc = this.baseGrocery * Math.pow(1 + this.groceryInflation() / 100, y - 1);
      const rent = this.baseRent * Math.pow(1 + this.rentInflation() / 100, y - 1);
      const totalExp = groc + rent + this.baseOther;
      const netCash = inc - totalExp - this.annualEmi;
      nw += netCash;

      list.push({ year: y, inc, exp: totalExp, netCash, netWorth: Math.round(nw), isDeficit: netCash < 0 });
    }
    return list;
  });

  crossoverYear = computed(() => {
    const found = this.yearlyResults().find(r => r.isDeficit);
    return found ? found.year : null;
  });
}
```

---

# Verification Protocols

1. **Accounting Verification**: Test that Net Worth dynamically equals total Asset balances minus total Liability balances.
2. **Double-Entry Balance Test**: Attempt to post an entry with total Debits != total Credits; verify NestJS throws `400 Bad Request`.
3. **Amortization Accuracy**: Verify that adding up the principal components of an EMI schedule equals the original principal.
4. **Inflation Forecast Test**: Set salary growth to 0% and expense inflation to 8%. Verify that the simulation identifies the exact year when expenses surpass income (Deficit Crossover).
5. **Emergency Runway Test**: Set liquid assets to ₹6,00,000 and monthly total expenses to ₹50,000; verify runway computes to exactly 12.0 months.
6. **Vector Suggestion Test**: Query `pgvector` with `"bought milk and bread"` and verify similarity matching returns the `EXPENSE: Groceries` head.
