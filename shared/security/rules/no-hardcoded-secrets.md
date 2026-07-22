---
trigger: always_on
description: "Prevents hardcoding passwords, API tokens, private keys, database credentials, or secret strings in source code or configuration files."
---
# No Hardcoded Secrets Rule

## Description
This rule mandates that all sensitive credentials, secret tokens, private keys, and database passwords MUST be loaded exclusively through environment variables or secret management services. Hardcoding secrets in any code file is strictly prohibited.

## Constraints
- The agent MUST NOT write hardcoded secret strings (API keys, JWT secrets, passwords, SSH keys) in source files, tests, or config files.
- The agent MUST reference environment variables (`process.env.API_KEY`, `process.env.DATABASE_URL`) or use `.env.example` templates for configuration.
- The agent MUST ensure `.env` files are included in `.gitignore`.

## Examples
- **Correct implementation:**
```typescript
const dbUri = process.env.DATABASE_URL;
if (!dbUri) {
  throw new Error("DATABASE_URL environment variable is required");
}
```

- **Incorrect implementation:**
```typescript
const dbUri = "postgres://admin:secretpassword123@localhost:5432/mydb"; // Security Risk!
```
