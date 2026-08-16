---
trigger: always_on
description: "Enforces strict TypeScript typing across all workspace files by prohibiting explicit or implicit use of the `any` type."
---
# No `any` Type Enforcement

## Description
This rule strictly forbids the use of TypeScript's `any` type in all production, test, and utility code to preserve type safety and catch errors at compile time.

## Constraints
- The agent MUST NOT write `any` as an explicit type annotation for variables, parameters, return types, or type assertions.
- The agent MUST use specific interfaces, generics, `unknown` with type narrowing, or utility types (`Record<string, unknown>`) instead of `any`.
- If an third-party external library lacks types, the agent MUST declare a minimal custom interface or type boundary rather than resorting to `any`.

## Examples
- **Correct implementation:**
```typescript
function parseUserData(input: unknown): UserProfile {
  if (isUserData(input)) {
    return input;
  }
  throw new Error("Invalid user payload format");
}
```

- **Incorrect implementation:**
```typescript
function parseUserData(input: any): any {
  return input;
}
```
