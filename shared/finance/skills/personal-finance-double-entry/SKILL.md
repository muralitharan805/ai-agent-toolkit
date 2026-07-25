---
name: personal-finance-double-entry
description: "Architectural guidelines, database schemas, double-entry bookkeeping engine protocols, immutable ledger constraints, reversing entries, financial statements (Trial Balance, Balance Sheet, P&L), EMI loan amortization calculations, prepayment simulators, 7-dimensional forecasting, bank statement CSV/PDF auto-reconciliation, multi-currency support, tax tagging, pgvector AI category search, NestJS modules, and Angular 21 Signal-driven components for building Personal Finance & Net Worth Web SPAs."
---

# Personal Finance & Net Worth Engine (Double-Entry Bookkeeping & Enterprise Production Capabilities)

## Goal
Guide the design and implementation of an enterprise-grade Personal Finance Web SPA (**NidhiFlow**). Enforces formal **Double-Entry Bookkeeping**, **The Accounting Equation**, **Immutable Ledger Constraints**, **Audit-Compliant Reversing Entries**, **Real-Time Financial Statements (Trial Balance, Balance Sheet, P&L)**, **EMI Amortization & Debt Payoff Projections**, **7-Dimensional Financial Forecasting Sandbox**, **Bank Statement Auto-Reconciliation**, **Multi-Currency Support**, **Tax Tagging**, **Interactive Chart of Accounts Tree**, and **AI Vector Search (`pgvector`)** using **Angular 21** and **NestJS**.

---

# Core Domain & Accounting Principles

### 1. The Accounting Equation & Net Worth
Every monetary transaction affects the core accounting equation:

$$\text{Assets} = \text{Liabilities} + \text{Equity}$$

$$\text{Net Worth} = \sum \text{Assets} - \sum \text{Liabilities}$$

### 2. Double-Entry Posting Rules
Every transaction MUST contain a balanced set of postings ($\sum \text{Debits} = \sum \text{Credits}$):

| Account Type | Increase (+) | Decrease (-) | Normal Balance |
| :--- | :--- | :--- | :--- |
| **Asset** | Debit ($\text{Dr}$) | Credit ($\text{Cr}$) | Debit |
| **Expense** | Debit ($\text{Dr}$) | Credit ($\text{Cr}$) | Debit |
| **Liability** | Credit ($\text{Cr}$) | Debit ($\text{Dr}$) | Credit |
| **Equity** | Credit ($\text{Cr}$) | Debit ($\text{Dr}$) | Credit |
| **Income** | Credit ($\text{Cr}$) | Debit ($\text{Dr}$) | Credit |

### 3. Immutable Ledger Constraint & Reversing Entry Protocol
- **No Direct Update or Delete**: Posted journal entries MUST NOT be edited or deleted directly in the database.
- **Reversing Entry Action**: Errors or cancellations MUST be performed by issuing an audit-compliant **Reversing Journal Entry**:
  - `entryNumber`: `REV-${originalEntryNumber}`
  - `description`: `[REVERSAL] ${reason} - ${originalDescription}`
  - `postings`: Flip original Debit allocations to Credit, and original Credit allocations to Debit.

### 4. EMI Amortization & Debt Payoff Formula
$$M = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}$$

- **EMI Double-Entry Posting**:
  - `DEBIT`: Liability Account (Principal Reduction Component)
  - `DEBIT`: Interest Expense Account (Interest Component)
  - `CREDIT`: Asset Bank Account (Total EMI Amount)

---

# Real-Time Financial Statements Engine

### 1. Trial Balance (இருப்புச் சோதனையறிக்கை)
- Verifies that $\sum \text{Debits} = \sum \text{Credits}$ across all accounts in the Chart of Accounts.
- Highlights any unbalancing anomalies immediately.

### 2. Balance Sheet (இருப்புநிலைத் தாள்)
- Evaluates $\text{Assets} = \text{Liabilities} + \text{Equity}$ in real time.
- Groups active ledger accounts into Assets (Cash, Bank, Investments), Liabilities (Loans, Credit Cards), and Equity (Capital, Retained Earnings).

### 3. Income Statement / Profit & Loss (வருமான அறிக்கை)
- Calculates Net Income / Loss: $\text{Net Income} = \text{Total Revenues} - \text{Total Expenses}$.

---

# 7 Advanced Forecasting & Scenario Dimensions

1. **Debt-Free Prepayment & Interest Savings Forecast**
2. **Emergency Cash Runway & Survival Forecast (Income Shock)**
3. **FIRE (Financial Independence Retire Early) & Retirement Corpus Forecast**
4. **Life Goal & Milestone Target Forecast (SIP Calculator)**
5. **Multi-Year Inflation Escalation & Deficit Crossover Forecast** ($E_{k, t} = E_{k, 0} \times (1 + i_k)^t$)
6. **Asset Allocation & Compound Investment Growth Forecast**
7. **Lending & Receivable Default Impact Forecast**

*Note: Forecasting simulations MUST execute in an isolated transient sandbox state without mutating historical ledger postings.*

---

# 5 Enterprise Production-Grade Capabilities

### 1. Bank Statement Import & Auto-Reconciliation Engine
- Accepts CSV / OFX / PDF bank statements (HDFC, ICICI, SBI, Axis, etc.).
- Matches statement lines against posted ledger transactions.
- 1-click posting of unmatched statement items directly to the double-entry ledger.

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
    entry_number VARCHAR(64) UNIQUE NOT NULL,
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
3. **Reversal Verification**: Post a reversing transaction for `JE-101`; verify `REV-JE-101` flips debits/credits and cancels out net balance.
4. **Amortization Accuracy**: Verify that adding up the principal components of an EMI schedule equals the original principal.
5. **Statement Reconciliation Test**: Upload a sample bank statement line `"HDFC BANK ATM SWIPE DMART"`; verify `pgvector` auto-suggests `EXPENSE: Groceries` with confidence score > 85%.
6. **Inflation Forecast Test**: Set salary growth to 0% and expense inflation to 8%. Verify that the simulation identifies the exact year when expenses surpass income (Deficit Crossover).
7. **Multi-Currency Test**: Post a $100 USD transaction with exchange rate 83.50; verify base posting records ₹8,350 INR.
