# Clean Code & SOLID Architecture Engineering Guide

## 1. Core Philosophy & The Junior Developer Readability Benchmark

Clean Code is not merely code that executes without runtime errors; it is code that clearly expresses its business intent to any engineer reading it for the first time. In high-velocity teams, code is read ten times more often than it is written.

### The 2-Minute Readability Benchmark
Any fresher or junior developer joining the team must be able to read any service method or controller endpoint from top to bottom and articulate its exact business responsibility within two minutes, without consulting external documentation or guessing side effects.

---

## 2. SOLID Design Principles in Modern TypeScript

| Principle | Core Invariant | Anti-Pattern | Modern Clean Architecture Solution |
| :--- | :--- | :--- | :--- |
| **S - Single Responsibility** | A class or function must have exactly one reason to change. | A single service handling database persistence, PDF rendering, and email dispatch. | Split into `UserRepository`, `PdfReportGenerator`, and `EmailNotificationService`. |
| **O - Open / Closed** | Open for extension, closed for modification. | Hardcoded switch statements matching payment gateways (`switch (gateway) { case 'STRIPE': ... }`). | Strategy pattern: Define `PaymentGatewayStrategy` interface and register providers dynamically. |
| **L - Liskov Substitution** | Subtypes must be substitutable for their base types without altering correctness. | Derived class throwing `UnsupportedOperationException` for inherited methods. | Split bloated interfaces into granular capabilities (`ReadableStream`, `WritableStream`). |
| **I - Interface Segregation** | Clients should not be forced to depend on methods they do not use. | A monolithic `IEntityService` requiring CRUD + Export + Audit methods on read-only views. | Narrow interfaces: `IEntityReader<T>`, `IEntityWriter<T>`, `IEntityAuditor<T>`. |
| **D - Dependency Inversion** | High-level modules must depend on abstractions, not concrete implementations. | Instantiating concrete `new PostgresConnection()` directly inside a domain service. | Inject interface tokens (`@Inject(USER_REPOSITORY_TOKEN)`) via dependency injection. |

---

## 3. Function Design & Complexity Constraints

### 3.1 Length Ceiling (Strictly $\le 35$ Lines)
Functions must not exceed 35 lines of executable logic. If a method requires more than 35 lines:
1. Extract private helper methods for secondary transformations.
2. Delegate external orchestrations to specialized sub-services.
3. Replace procedural step ladders with composable pipelines.

### 3.2 Positional Parameter Ceiling (Max 3 Positional Parameters)
Functions must accept at most 3 positional arguments. Any function requiring 4 or more inputs must encapsulate them in a typed Data Transfer Object (DTO) or options object:

```typescript
// ❌ FORBIDDEN: 5 positional parameters (error-prone parameter ordering)
export function calculateMortgage(
  principal: number,
  rate: number,
  tenureMonths: number,
  propertyTax: number,
  insurance: number
): MortgageBreakdown { ... }

// ✅ CORRECT: Encapsulated DTO options object
export interface MortgageCalculationOptions {
  readonly principalAmount: number;
  readonly annualInterestRate: number;
  readonly tenureInMonths: number;
  readonly annualPropertyTax: number;
  readonly monthlyHomeInsurance: number;
}

export function calculateMortgage(options: MortgageCalculationOptions): MortgageBreakdown { ... }
```

### 3.3 Guard Clauses & Early Returns (Max Nesting $\le 2$ Levels)
Never nest `if/else` blocks deeper than 2 levels. Use guard clauses (early `return` or early `throw`) to validate preconditions and flatten the execution path:

```typescript
// ❌ FORBIDDEN: Deeply nested conditional pyramid (3+ levels)
function processOrder(order: Order): void {
  if (order) {
    if (order.items.length > 0) {
      if (order.paymentStatus === 'PAID') {
        dispatchItems(order);
      } else {
        throw new Error('Unpaid');
      }
    } else {
      throw new Error('Empty items');
    }
  }
}

// ✅ CORRECT: Flattened execution flow with guard clauses
function processOrder(order: Order): void {
  if (!order) {
    throw new BadRequestException('Order payload must not be null');
  }
  if (order.items.length === 0) {
    throw new BadRequestException('Order must contain at least one line item');
  }
  if (order.paymentStatus !== PaymentStatus.PAID) {
    throw new PaymentRequiredException('Order cannot be dispatched prior to payment');
  }

  dispatchItems(order);
}
```

---

## 4. Mandatory TSDoc / JSDoc Block Comments

Every exported class, interface, method, controller endpoint, and public utility MUST include a comprehensive TSDoc comment block:

```typescript
/**
 * Generates an amortized repayment breakdown over the entire loan lifecycle.
 *
 * @param options - Encapsulated financial calculation parameters including principal, rate, and tenure
 * @returns An immutable array of monthly schedule records containing principal, interest, and residual debt
 * 
 * @throws {BadRequestException} When principal or interest rate is non-positive
 * @throws {UnprocessableEntityException} When tenure exceeds maximum regulatory limit (360 months)
 *
 * @example
 * const schedule = amortizationService.generateSchedule({
 *   principalAmount: 5000000,
 *   annualInterestRate: 7.25,
 *   tenureInMonths: 240
 * });
 */
export function generateSchedule(options: ScheduleCalculationOptions): readonly AmortizationRecord[] {
  // Implementation...
}
```

### Mandatory Tag Checklist
- **Business Summary**: 1–2 sentences explaining *why* the function exists in domain terms.
- `@param`: Descriptive explanation of every argument, including unit or currency (e.g. `₹ in base units`, `ms`).
- `@returns`: Exact structure and characteristics of the return value.
- `@throws`: All known domain exceptions that consumers must be prepared to catch.
- `@example`: Working TypeScript snippet demonstrating realistic invocation.
