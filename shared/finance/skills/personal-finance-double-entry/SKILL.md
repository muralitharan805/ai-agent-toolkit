---
name: personal-finance-double-entry
description: "Architectural guidelines, database schemas, double-entry bookkeeping engine protocols, EMI loan amortization calculations, 7-dimensional multi-year inflation scenario forecasting engine, bank statement CSV/PDF auto-reconciliation, multi-currency support, tax tagging, pgvector AI category search, NestJS modules, and Angular 21 Signal-driven components for building Personal Finance & Net Worth Web SPAs."
---

# Personal Finance & Net Worth Engine (Double-Entry Bookkeeping & Enterprise Production Capabilities)

## Goal
Guide the design and implementation of an enterprise-grade Personal Finance Web SPA (**NidhiFlow**). Enforces formal **Double-Entry Bookkeeping**, **The Accounting Equation**, **EMI Amortization & Debt Payoff Projections**, **7-Dimensional Financial Forecasting Engine**, **Bank Statement Auto-Reconciliation**, **Multi-Currency Support**, **Tax Tagging**, **Interactive Chart of Accounts Tree**, and **AI Vector Search (`pgvector`)** using **Angular 21** and **NestJS**.

---

# Core Domain & Accounting Principles

### 1. The Accounting Equation & Net Worth
Every monetary transaction affects the core accounting equation:

$$\text{Assets} = \text{Liabilities} + \text{Equity}$$

$$\text{Net Worth} = \sum \text{Assets} - \sum \text{Liabilities}$$

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
$$M = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}$$

---

# 7 Advanced Forecasting & Scenario Dimensions

1. **Debt-Free Prepayment & Interest Savings Forecast**
2. **Emergency Cash Runway & Survival Forecast (Income Shock)**
3. **FIRE (Financial Independence Retire Early) & Retirement Corpus Forecast**
4. **Life Goal & Milestone Target Forecast (SIP Calculator)**
5. **Multi-Year Inflation Escalation & Deficit Crossover Forecast**
6. **Asset Allocation & Compound Investment Growth Forecast**
7. **Lending & Receivable Default Impact Forecast**

---

# 5 Enterprise Production-Grade Capabilities

### 1. Bank Statement Import & Auto-Reconciliation Engine
- Accepts CSV / OFX / PDF bank statements (HDFC, ICICI, SBI, Axis, etc.).
- Parses raw statement lines and uses `pgvector` similarity search (`<=>`) to match description text to appropriate Chart of Accounts heads.
- Automatically generates balanced Debit/Credit journal entries with single-click user approval.

### 2. Multi-Currency & FX Rate Conversion Engine
- Supports transactions in foreign currencies (USD $, EUR €, SGD $, AED).
- Converts foreign amounts into base currency (INR ₹) using daily FX rate tables ($A_{\text{base}} = A_{\text{foreign}} \times \text{ExchangeRate}$).
- Tracks unrealized FX gain/loss on foreign assets/investments.

### 3. Recurring & Scheduled Transaction Automation
- Schedules recurring monthly transactions (Salary credit on 1st, Rent debit on 5th, SIP investment on 15th, EMI debit on 20th).
- Automatically posts entries or sends reminder notifications when due.

### 4. Tax Category Tagging & Deduction Computation
- Tags expense and asset postings with tax deduction flags (e.g. Section 80C for ELSS/PPF, Section 80D for Health Insurance, Section 24b for Home Loan Interest, HRA for Rent).
- Computes estimated tax savings and generates tax report during filing season.

### 5. Encrypted Data Privacy & Automated Backup Export
- AES-256 encryption for sensitive account numbers and transaction memos.
- One-click encrypted JSON / CSV backup export and restore utility.

---

# Database Schema Specification (PostgreSQL + `pgvector`)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Currencies & Exchange Rates
CREATE TABLE currencies (
    code VARCHAR(3) PRIMARY KEY, -- e.g. 'INR', 'USD', 'EUR'
    symbol VARCHAR(8) NOT NULL,
    exchange_rate_to_base NUMERIC(12, 6) DEFAULT 1.000000 -- Base currency rate = 1.0
);

-- 2. Chart of Accounts
CREATE TYPE account_type_enum AS ENUM ('ASSET', 'LIABILITY', 'EQUITY', 'INCOME', 'EXPENSE');

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    type account_type_enum NOT NULL,
    parent_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    currency_code VARCHAR(3) DEFAULT 'INR' REFERENCES currencies(code),
    tax_section VARCHAR(32), -- e.g. '80C', '80D', '24B', 'HRA'
    is_active BOOLEAN DEFAULT TRUE,
    description_embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Double-Entry Journal Entries & Postings
CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_date DATE NOT NULL,
    description TEXT NOT NULL,
    reference_no VARCHAR(64),
    is_recurring BOOLEAN DEFAULT FALSE,
    is_posted BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TYPE posting_type_enum AS ENUM ('DEBIT', 'CREDIT');

CREATE TABLE journal_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id),
    type posting_type_enum NOT NULL,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    foreign_amount NUMERIC(15, 2),
    currency_code VARCHAR(3) DEFAULT 'INR' REFERENCES currencies(code)
);

-- 4. Bank Statement Reconciliation Staging
CREATE TABLE bank_reconciliations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_statement_line TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    suggested_account_id UUID REFERENCES accounts(id),
    confidence_score NUMERIC(5, 2),
    is_approved BOOLEAN DEFAULT FALSE
);

-- 5. Loans & EMI Tracker
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
```

---

# Verification Protocols

1. **Accounting Verification**: Test that Net Worth dynamically equals total Asset balances minus total Liability balances.
2. **Double-Entry Balance Test**: Attempt to post an entry with total Debits != total Credits; verify NestJS throws `400 Bad Request`.
3. **Amortization Accuracy**: Verify that adding up the principal components of an EMI schedule equals the original principal.
4. **Statement Reconciliation Test**: Upload a sample bank statement line `"HDFC BANK ATM SWIPE DMART"`; verify `pgvector` auto-suggests `EXPENSE: Groceries` with confidence score > 85%.
5. **Inflation Forecast Test**: Set salary growth to 0% and expense inflation to 8%. Verify that the simulation identifies the exact year when expenses surpass income (Deficit Crossover).
6. **Multi-Currency Test**: Post a $100 USD transaction with exchange rate 83.50; verify base posting records ₹8,350 INR.
