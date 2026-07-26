---
description: "Strict accounting, ledger, and forecasting simulation constraints for personal finance apps."
trigger: always_on
---

# Double-Entry Accounting & Forecasting Rules

## Description
Enforces mandatory constraints for financial transaction recording, account classification, EMI amortization schedule calculations, multi-year inflation scenario modeling, and Net Worth generation in personal finance applications.

## Constraints

### 1. Mandatory Double-Entry Balance Constraint
- Every transaction MUST have at least two posting lines (one Debit and one Credit).
- Total sum of Debits MUST strictly equal total sum of Credits:
  $$\sum \text{Debits} - \sum \text{Credits} = 0$$
- An unbalanced entry MUST NEVER be persisted to the database.

### 2. The Accounting Equation & Net Worth Constraint
- Every account head MUST be classified under one of the 5 canonical types: `ASSET`, `LIABILITY`, `EQUITY`, `INCOME`, or `EXPENSE`.
- Net Worth MUST strictly be computed as:
  $$\text{Net Worth} = \sum \text{Assets} - \sum \text{Liabilities}$$
- Single-entry plus/minus modifications without specifying an offsetting account head are STRICTLY FORBIDDEN.

### 3. Immutable Journal Ledger Constraint
- Once a journal entry is posted, it MUST NOT be edited or deleted directly in the database.
- Any correction or refund MUST be performed by issuing a reversing journal entry (opposite Debit/Credit allocations) with proper audit logs.

### 4. EMI & Loan Amortization Constraint
- EMI principal payments MUST debit the corresponding Liability account (reducing debt).
- EMI interest payments MUST debit the Interest Expense account.
- Any early principal prepayment MUST trigger an immediate recalculation of the remaining amortization schedule and update the projected payoff completion date.

### 5. Multi-Year Forecasting & Inflation Modeling Constraint
- Forecasting simulations MUST NOT mutate active ledger postings or real historical account balances; simulations MUST execute in isolated transient or scenario sandbox states.
- Category inflation rates ($i_k$) MUST compounding annually:
  $$E_{k, t} = E_{k, 0} \times (1 + i_k)^t$$
- The system MUST explicitly highlight the **Deficit Crossover Year** ($t$) whenever projected annual expenses + loan obligations exceed projected income ($I_t < E_t + \text{EMI}_t$).
