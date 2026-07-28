# NidhiFlow Financial Domain & Multi-Tenant Enforcement Rules

## Description
Enforces strict multi-tenant user data isolation (`user_id`), mandatory double-entry ledger balance checks ($\sum \text{Debits} == \sum \text{Credits}$), immutable ledger reversing entry protocols, zero direct deletions, and currency standardizations for NidhiFlow personal finance microservices.

## Constraints

### 1. Mandatory Multi-Tenant User Isolation
- All database entities (`accounts`, `journal_entries`, `journal_postings`, `bank_reconciliations`, `loans_emi`) MUST include `userId` / `user_id`.
- All repository/Prisma queries MUST explicitly scope by `where: { userId: currentUserId }`.
- Cross-user querying or data leaking is strictly prohibited.

### 2. Double-Entry Balancing Enforcement
- Every API endpoint or service method that handles journal entry creation (`postJournalEntry`) MUST verify that total Debits equal total Credits BEFORE persisting to database.
- If total Debits != total Credits, the backend MUST reject the payload with `400 Bad Request`.

### 3. Immutable Ledger Protocol
- Posted transactions (`isPosted = true`) MUST NOT be updated or deleted directly via SQL `UPDATE` or `DELETE`.
- Reversals MUST be executed by posting a new entry with entry number `REV-${originalNumber}` and inverted debit/credit allocations.

### 4. Monetary Representation & Precision
- Monetary amounts MUST be stored as `NUMERIC(15, 2)` or `Decimal` in Prisma to avoid floating-point rounding errors.
- Never use standard JavaScript IEEE 754 floating point numbers for financial calculations without rounding helpers.

### 5. Base Currency & FX Handling
- All financial balances MUST maintain a base currency value in `INR` (`₹`).
- Foreign currency transactions MUST store both foreign amount, foreign currency code, and converted base currency amount using exchange rate tables.
