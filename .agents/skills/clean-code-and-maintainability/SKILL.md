---
name: clean-code-and-maintainability
description: "Guidelines for writing clean, self-documenting, maintainable, and scalable software adhering to Robert C. Martin's Clean Code principles, mandatory TSDoc/JSDoc comments, SOLID design, and junior-developer-friendly readability."
---

# Clean Code & Long-Term Maintainability Guidelines

## Goal
Guide AI coding agents and developers in writing enterprise-grade, clean, self-documenting code that adheres to Robert C. Martin's **Clean Code** principles, mandatory **TSDoc/JSDoc block comments**, **SOLID design patterns**, and junior-developer-friendly readability.

---

# Core Clean Code & Readability Principles

### 1. Meaningful & Intention-Revealing Names
- Names MUST reveal intent without needing explanatory inline comments.
- **Bad**: `const d = 86400;`, `function proc(x: any)`
- **Good**: `const ONE_DAY_IN_SECONDS = 86400;`, `function calculateMonthlyEmi(principal: number, interestRate: number)`

### 2. Single Responsibility Principle (SRP)
- Functions should do ONE thing, do it well, and do it only.
- Function length SHOULD NOT exceed 30 lines. If a method performs multiple steps, extract helper functions.

### 3. Mandatory TSDoc / JSDoc Block Comments
Every exported class, interface, service method, controller endpoint, and utility algorithm MUST include TSDoc comments so fresher/junior developers can instantly understand the business purpose:

```typescript
/**
 * Calculates the monthly EMI installment and full amortization schedule for a loan.
 *
 * @param principal - Total principal loan amount in base currency (e.g. ₹25,00,000)
 * @param annualInterestRate - Annual interest rate percentage (e.g. 8.5 for 8.5%)
 * @param tenureMonths - Loan duration in months (e.g. 240 for 20 years)
 * @param startDate - Date when loan repayment begins
 * 
 * @returns Array of amortization schedule rows containing principal/interest split & remaining balance
 * 
 * @throws {BadRequestException} If principal, rate, or tenure are non-positive values
 * 
 * @example
 * const schedule = amortizationService.calculateSchedule(2500000, 8.5, 240, new Date());
 */
export function calculateAmortizationSchedule(
  principal: number,
  annualInterestRate: number,
  tenureMonths: number,
  startDate: Date
): AmortizationScheduleRow[] {
  // Implementation...
}
```

### 4. Parameter Count Control (Max 3 Parameters)
- Functions SHOULD accept at most 3 positional parameters.
- If a function requires 4 or more parameters, wrap them in a typed DTO class or Options object:

```typescript
// Bad
function createLoan(account: string, rate: number, tenure: number, date: Date, extra: number, user: string)

// Good: Uses typed DTO
function createLoan(dto: CreateLoanDto)
```

### 5. No Magic Numbers or Hardcoded Strings
- Replace magic numbers and inline string literals with explicit Enums or `readonly` Constants:

```typescript
// Bad
if (user.role === 2) { ... }

// Good
export enum UserRole {
  ADMIN = 'ADMIN',
  MEMBER = 'MEMBER',
}
if (user.role === UserRole.ADMIN) { ... }
```

### 6. SOLID Architecture Principles

| Principle | Description | Implementation |
| :--- | :--- | :--- |
| **S** - Single Responsibility | A class should have only one reason to change. | Separate `LedgerService` from `PdfExportService`. |
| **O** - Open / Closed | Open for extension, closed for modification. | Use strategy pattern for different report exporters. |
| **L** - Liskov Substitution | Derived classes must be substitutable for base types. | Custom exception classes extending `HttpException`. |
| **I** - Interface Segregation | Don't force implementation of unused interfaces. | Small, focused interfaces (`IUserRepository`, `IEmiCalculator`). |
| **D** - Dependency Inversion | Depend on abstractions, not concrete implementations. | Inject abstract provider tokens via NestJS DI. |

---

# Refactoring Checklist for AI Agents & Developers

1. **Readability Check**: Can a fresher developer read this file top-to-bottom and understand what it does within 2 minutes?
2. **Comment Check**: Are all public service methods documented with TSDoc `@param` and `@returns` tags?
3. **Complexity Check**: Are there deeply nested `if/else` conditionals (> 3 levels)? Use early returns / guard clauses instead:

```typescript
// Bad (Deep nesting)
function processPayment(user: User, amount: number) {
  if (user) {
    if (user.isActive) {
      if (amount > 0) {
        // Do payment
      }
    }
  }
}

// Good (Guard clauses / Early return)
function processPayment(user: User, amount: number): void {
  if (!user || !user.isActive) {
    throw new UnauthorizedException('User account is inactive.');
  }
  if (amount <= 0) {
    throw new BadRequestException('Payment amount must be positive.');
  }

  // Do payment
}
```

---

# Verification Protocols

1. **JSDoc Validation**: Ensure all exported methods contain complete JSDoc annotations.
2. **Linting Check**: Run `pnpm run lint` to enforce clean code syntax and zero `any` types.
